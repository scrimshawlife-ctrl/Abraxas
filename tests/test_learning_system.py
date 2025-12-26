"""
Tests for Active Learning Loops

Validates failure analysis, proposal generation, sandbox execution, and promotion.
"""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path

from abraxas.backtest.schema import (
    BacktestCase,
    BacktestResult,
    BacktestStatus,
    Confidence,
    EvaluationWindow,
    ForecastRef,
    Guardrails,
    Scoring,
    Triggers,
    TriggerSpec,
    TriggerKind,
)
from abraxas.backtest.event_query import SignalEvent
from abraxas.learning.failure_analyzer import FailureAnalyzer
from abraxas.learning.proposal_generator import ProposalGenerator
from abraxas.learning.sandbox_runner import SandboxRunner
from abraxas.learning.promotion_gate import PromotionGate
from abraxas.learning.schema import (
    ProposalType,
    SandboxReport,
    BaselineMetrics,
    ProposalMetrics,
    DeltaMetrics,
    CostDelta,
)


def test_failure_analyzer_creation(tmp_path):
    """Test creating failure analyzer."""
    analyzer = FailureAnalyzer(
        output_dir=tmp_path / "reports",
        ledger_path=tmp_path / "learning_ledgers/failure_analyses.jsonl",
    )

    assert analyzer.output_dir == tmp_path / "reports"
    assert analyzer.output_dir.exists()


def test_failure_analysis_unmet_trigger(tmp_path):
    """Test failure analysis identifies unmet triggers."""
    analyzer = FailureAnalyzer(output_dir=tmp_path / "reports")

    # Create a case with term_seen trigger
    case = BacktestCase(
        case_id="test_case_001",
        created_at=datetime.now(timezone.utc),
        description="Test case for term emergence",
        forecast_ref=ForecastRef(
            run_id="run_001", artifact_path="out/runs/run_001/report.json", tier="enterprise"
        ),
        evaluation_window=EvaluationWindow(
            start_ts=datetime(2025, 12, 20, 12, 0, 0, tzinfo=timezone.utc),
            end_ts=datetime(2025, 12, 23, 12, 0, 0, tzinfo=timezone.utc),
        ),
        triggers=Triggers(
            any_of=[
                TriggerSpec(
                    kind=TriggerKind.TERM_SEEN,
                    params={"term": "quantum computing", "min_count": 2},
                )
            ]
        ),
        guardrails=Guardrails(min_signal_count=5),
        scoring=Scoring(type="binary", weights={"trigger": 1.0}),
    )

    # MISS result (trigger not satisfied)
    result = BacktestResult(
        case_id="test_case_001",
        run_id="run_001",
        status=BacktestStatus.MISS,
        score=0.0,
        confidence=Confidence.HIGH,
    )

    # Events that don't contain the term
    events = [
        SignalEvent(
            event_id=f"e{i}",
            timestamp=datetime.now(timezone.utc),
            text=f"This is event {i} about AI",
            source="OSH",
        )
        for i in range(10)
    ]

    ledgers = {}

    # Analyze failure
    analysis = analyzer.analyze(case, result, events, ledgers)

    assert analysis.failure_id.startswith("failure_test_case_001")
    assert analysis.backtest_result["status"] == "MISS"
    assert len(analysis.unmet_triggers) == 1
    assert analysis.unmet_triggers[0].kind == "term_seen"
    assert analysis.unmet_triggers[0].expected["term"] == "quantum computing"
    assert analysis.unmet_triggers[0].actual["count"] == 0


def test_failure_analysis_signal_gaps(tmp_path):
    """Test failure analysis identifies signal gaps."""
    analyzer = FailureAnalyzer(output_dir=tmp_path / "reports")

    case = BacktestCase(
        case_id="test_case_002",
        created_at=datetime.now(timezone.utc),
        description="Test case with insufficient signals",
        forecast_ref=ForecastRef(
            run_id="run_002", artifact_path="out/runs/run_002/report.json", tier="enterprise"
        ),
        evaluation_window=EvaluationWindow(
            start_ts=datetime(2025, 12, 20, 12, 0, 0, tzinfo=timezone.utc),
            end_ts=datetime(2025, 12, 23, 12, 0, 0, tzinfo=timezone.utc),
        ),
        triggers=Triggers(any_of=[]),
        guardrails=Guardrails(min_signal_count=20),  # Require 20 signals
        scoring=Scoring(type="binary", weights={"trigger": 1.0}),
    )

    # ABSTAIN result (insufficient signals)
    result = BacktestResult(
        case_id="test_case_002",
        run_id="run_002",
        status=BacktestStatus.ABSTAIN,
        score=0.2,
        confidence=Confidence.HIGH,
    )

    # Only 5 events (below min_signal_count of 20)
    events = [
        SignalEvent(
            event_id=f"e{i}",
            timestamp=datetime.now(timezone.utc),
            text=f"Event {i}",
            source="OSH",
        )
        for i in range(5)
    ]

    ledgers = {}

    analysis = analyzer.analyze(case, result, events, ledgers)

    assert analysis.signal_gaps.missing_events == 15  # 20 - 5
    assert analysis.hypothesis == "insufficient_signal_count"


def test_proposal_generator_creates_threshold_adjustment(tmp_path):
    """Test proposal generator creates threshold adjustment."""
    from abraxas.learning.schema import FailureAnalysis, UnmetTrigger, SignalGaps, IntegrityConditions, TemporalGaps

    generator = ProposalGenerator(proposals_dir=tmp_path / "proposals")

    # Create failure analysis with unmet trigger
    failure = FailureAnalysis(
        failure_id="failure_test_case_001_run_001",
        case_id="test_case_001",
        run_id="run_001",
        backtest_result={"status": "MISS", "score": 0.0, "confidence": "HIGH"},
        unmet_triggers=[
            UnmetTrigger(
                kind="term_seen",
                expected={"term": "quantum computing", "min_count": 2},
                actual={"count": 1},
            )
        ],
        hit_falsifiers=[],
        signal_gaps=SignalGaps(missing_events=0, denied_signals=0),
        integrity_conditions=IntegrityConditions(max_ssi=0.3, synthetic_saturation=0.1),
        temporal_gaps=TemporalGaps(),
        hypothesis="term_prediction_too_aggressive",
        suggested_adjustments=["relax_min_count_threshold"],
    )

    # Generate proposal
    proposal = generator.generate(failure)

    assert proposal.proposal_type == ProposalType.THRESHOLD_ADJUSTMENT
    assert "quantum computing" in proposal.change_description.lower()
    assert proposal.source_failure_id == failure.failure_id
    assert len(proposal.expected_delta.improved_cases) > 0


def test_sandbox_runner_loads_proposal(tmp_path):
    """Test sandbox runner loads proposals."""
    from abraxas.learning.schema import Proposal, ExpectedDelta, ValidationPlan

    # Create a proposal
    proposal = Proposal(
        proposal_id="test_proposal_001",
        source_failure_id="failure_test_001",
        proposal_type=ProposalType.THRESHOLD_ADJUSTMENT,
        change_description="Test proposal",
        affected_components=["test_case"],
        expected_delta=ExpectedDelta(
            improved_cases=["test_case_001"],
            regression_risk=[],
            backtest_pass_rate_delta=0.15,
        ),
        validation_plan=ValidationPlan(
            sandbox_cases=["test_case_001"], protected_cases=[], stabilization_runs=3
        ),
    )

    # Write proposal to disk with proper serialization
    proposals_dir = tmp_path / "proposals"
    proposal_dir = proposals_dir / proposal.proposal_id
    proposal_dir.mkdir(parents=True)

    import yaml

    # Convert enums to strings for YAML
    proposal_dict = proposal.model_dump()
    proposal_dict["proposal_type"] = proposal.proposal_type.value

    with open(proposal_dir / "proposal.yaml", "w") as f:
        yaml.dump(proposal_dict, f, sort_keys=False)

    # Load it back
    runner = SandboxRunner(proposals_dir=proposals_dir, cases_dir=tmp_path / "cases")
    loaded_proposal = runner.load_proposal("test_proposal_001")

    assert loaded_proposal.proposal_id == "test_proposal_001"
    assert loaded_proposal.proposal_type == ProposalType.THRESHOLD_ADJUSTMENT


def test_promotion_gate_validates_criteria():
    """Test promotion gate validation logic."""
    gate = PromotionGate(improvement_threshold=0.10)

    from abraxas.learning.schema import Proposal, ExpectedDelta, ValidationPlan

    proposal = Proposal(
        proposal_id="test_proposal_001",
        source_failure_id="failure_001",
        proposal_type=ProposalType.THRESHOLD_ADJUSTMENT,
        change_description="Test",
        affected_components=["test"],
        expected_delta=ExpectedDelta(
            improved_cases=["test_case"], regression_risk=[], backtest_pass_rate_delta=0.15
        ),
        validation_plan=ValidationPlan(
            sandbox_cases=["test_case"], protected_cases=[], stabilization_runs=3
        ),
    )

    # Create passing sandbox reports
    sandbox_reports = []
    for i in range(3):
        report = SandboxReport(
            sandbox_run_id=f"sandbox_run_{i}",
            proposal_id="test_proposal_001",
            baseline=BaselineMetrics(
                backtest_pass_rate=0.67, hit_count=2, miss_count=1, abstain_count=0, avg_score=0.67
            ),
            proposal=ProposalMetrics(
                backtest_pass_rate=0.85, hit_count=3, miss_count=0, abstain_count=0, avg_score=0.85
            ),
            delta=DeltaMetrics(
                pass_rate_delta=0.18, hit_count_delta=1, regression_count=0
            ),
            cost_delta=CostDelta(time_ms_delta=5.0, memory_kb_delta=100),
            case_details=[],
            promotion_eligible=True,
        )
        sandbox_reports.append(report)

    # Validate
    eligible, reasons = gate.validate_promotion(proposal, sandbox_reports)

    assert eligible is True
    assert any("satisfied" in r.lower() for r in reasons)


def test_promotion_gate_rejects_regressions():
    """Test promotion gate rejects proposals with regressions."""
    gate = PromotionGate(improvement_threshold=0.10, required_stabilization_runs=1)

    from abraxas.learning.schema import Proposal, ExpectedDelta, ValidationPlan

    proposal = Proposal(
        proposal_id="test_proposal_002",
        source_failure_id="failure_002",
        proposal_type=ProposalType.THRESHOLD_ADJUSTMENT,
        change_description="Test",
        affected_components=["test"],
        expected_delta=ExpectedDelta(
            improved_cases=["test_case"], regression_risk=[], backtest_pass_rate_delta=0.15
        ),
        validation_plan=ValidationPlan(
            sandbox_cases=["test_case"], protected_cases=[], stabilization_runs=1
        ),
    )

    # Create report with good improvement BUT regression
    # (one case improved, one case regressed)
    report = SandboxReport(
        sandbox_run_id="sandbox_run_1",
        proposal_id="test_proposal_002",
        baseline=BaselineMetrics(
            backtest_pass_rate=0.50, hit_count=1, miss_count=1, abstain_count=0, avg_score=0.50
        ),
        proposal=ProposalMetrics(
            backtest_pass_rate=0.75, hit_count=2, miss_count=1, abstain_count=0, avg_score=0.75
        ),
        delta=DeltaMetrics(
            pass_rate_delta=0.25,  # Good improvement: +25%
            hit_count_delta=1,
            regression_count=1,  # BUT: 1 case regressed!
        ),
        cost_delta=CostDelta(time_ms_delta=5.0, memory_kb_delta=100),
        case_details=[],
        promotion_eligible=False,
    )

    # Validate
    eligible, reasons = gate.validate_promotion(proposal, [report])

    assert eligible is False
    # Print reasons for debugging if test fails
    if not any("regression" in r.lower() for r in reasons):
        print(f"Reasons: {reasons}")
    assert any("regression" in r.lower() for r in reasons)


def test_ledger_chain_integrity(tmp_path):
    """Test that learning ledgers maintain hash chain integrity."""
    analyzer = FailureAnalyzer(
        output_dir=tmp_path / "reports",
        ledger_path=tmp_path / "learning_ledgers/failure_analyses.jsonl",
    )

    from abraxas.learning.schema import FailureAnalysis, SignalGaps, IntegrityConditions, TemporalGaps

    # Create multiple failure analyses
    for i in range(3):
        failure = FailureAnalysis(
            failure_id=f"failure_test_{i}",
            case_id=f"test_case_{i}",
            run_id=f"run_{i}",
            backtest_result={"status": "MISS", "score": 0.0, "confidence": "HIGH"},
            unmet_triggers=[],
            hit_falsifiers=[],
            signal_gaps=SignalGaps(missing_events=0, denied_signals=0),
            integrity_conditions=IntegrityConditions(max_ssi=0.3, synthetic_saturation=0.1),
            temporal_gaps=TemporalGaps(),
            hypothesis="test_hypothesis",
            suggested_adjustments=[],
        )
        analyzer.append_to_ledger(failure)

    # Verify ledger exists and has entries
    assert analyzer.ledger_path.exists()

    with open(analyzer.ledger_path, "r") as f:
        lines = f.readlines()
        assert len(lines) == 3

        # Verify hash chain
        prev_hash = "genesis"
        for line in lines:
            entry = json.loads(line)
            assert entry["prev_hash"] == prev_hash
            assert "step_hash" in entry
            prev_hash = entry["step_hash"]
