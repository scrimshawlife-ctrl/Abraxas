"""
Tests for sandbox portfolio thresholds.
"""

from datetime import datetime, timezone
from pathlib import Path
import json

import yaml

from abraxas.backtest.schema import (
    BacktestCase,
    BacktestResult,
    BacktestStatus,
    Confidence,
    ForecastRef,
    EvaluationWindow,
    Triggers,
    TriggerSpec,
    TriggerKind,
    Scoring,
    ForecastBranchRef,
)
from abraxas.evolution.schema import MetricCandidate, CandidateKind, SourceDomain, CandidateTarget
from abraxas.evolution.sandbox import run_sandbox_portfolios


def _write_case(case: BacktestCase, path: Path) -> None:
    path.write_text(yaml.safe_dump(case.dict(), sort_keys=False))


def _make_case(case_id: str) -> BacktestCase:
    return BacktestCase(
        case_id=case_id,
        created_at=datetime.now(timezone.utc),
        description="test",
        forecast_ref=ForecastRef(
            run_id="run",
            artifact_path="out/runs/run/reports/enterprise.json",
            tier="enterprise",
        ),
        evaluation_window=EvaluationWindow(
            start_ts=datetime(2025, 12, 20, 12, 0, 0, tzinfo=timezone.utc),
            end_ts=datetime(2025, 12, 23, 12, 0, 0, tzinfo=timezone.utc),
        ),
        triggers=Triggers(
            any_of=[TriggerSpec(kind=TriggerKind.TERM_SEEN, params={"term": "test"})]
        ),
        scoring=Scoring(type="binary", weights={"trigger": 1.0}),
        forecast_branch_ref=ForecastBranchRef(
            ensemble_id="ens",
            branch_id="branch",
            predicted_p_at_ts="auto",
        ),
        horizon="H72H",
        segment="core",
        narrative="N1_primary",
        topic_keys=["propaganda_pressure"],
    )


def _make_result(case_id: str, brier: float) -> BacktestResult:
    return BacktestResult(
        case_id=case_id,
        status=BacktestStatus.HIT,
        score=1.0,
        confidence=Confidence.HIGH,
        forecast_scoring={"brier": brier},
    )


def test_sandbox_portfolio_thresholds(tmp_path):
    cases_dir = tmp_path / "cases"
    cases_dir.mkdir()

    case_ids = [f"case_{idx}" for idx in range(5)]
    for case_id in case_ids:
        _write_case(_make_case(case_id), cases_dir / f"{case_id}.yaml")

    portfolios_path = tmp_path / "portfolios.yaml"
    portfolios_path.write_text(
        yaml.safe_dump(
            {
                "portfolios": [
                    {
                        "portfolio_id": "short_term_core",
                        "horizons": ["H72H", "H30D"],
                        "segments": ["core"],
                        "narratives": ["N1_primary", "N2_counter"],
                        "case_selectors": [
                            {"kind": "has_forecast_branch_ref"},
                            {"kind": "topic_key_in", "params": {"topic_keys": ["propaganda_pressure"]}},
                        ],
                        "protected": True,
                    }
                ]
            },
            sort_keys=False,
        )
    )

    candidate = MetricCandidate(
        candidate_id="cand_test_portfolio_001",
        kind=CandidateKind.PARAM_TWEAK,
        source_domain=SourceDomain.AALMANAC,
        proposed_at="2025-12-26T00:00:00Z",
        proposed_by="test",
        name="test_param",
        description="test",
        rationale="test",
        param_path="forecast.test",
        current_value=0.1,
        proposed_value=0.2,
        target=CandidateTarget(
            portfolios=["short_term_core"],
            horizons=["H72H"],
            score_metrics=["brier"],
            improvement_thresholds={"brier": -0.003},
            no_regress_portfolios=[],
            mechanism="test",
        ),
    )

    baseline_results = {case_id: _make_result(case_id, 0.3) for case_id in case_ids}
    after_results = {case_id: _make_result(case_id, 0.295) for case_id in case_ids}

    ctx = {
        "run_id": "test_run",
        "run_at": "2025-12-26T00:00:00+00:00",
        "output_dir": tmp_path,
    }

    result = run_sandbox_portfolios(
        candidate=candidate,
        cases_dir=cases_dir,
        portfolios_path=portfolios_path,
        ctx=ctx,
        overrides={
            "baseline_results": baseline_results,
            "after_results": after_results,
        },
    )

    assert result.pass_gate is True
    assert result.portfolio_results["short_term_core"]["status"] == "PASS"

    report_path = tmp_path / "reports" / f"portfolio_sandbox_{result.sandbox_id}.json"
    assert report_path.exists()

    golden_path = Path(__file__).parent / "golden" / "portfolios" / "portfolio_sandbox_report.json"
    report_data = json.loads(report_path.read_text())
    golden_data = json.loads(golden_path.read_text())
    assert report_data == golden_data
