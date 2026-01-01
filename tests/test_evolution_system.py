"""
Tests for Metric Evolution Track v0.1

Tests cover:
- Source vector map registry
- Candidate generation
- Sandbox execution
- Promotion gate with stabilization
- Ledger integrity
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path

from abraxas.evolution.schema import (
    MetricCandidate,
    SandboxResult,
    PromotionEntry,
    CandidateKind,
    SourceDomain,
    CandidateFilter,
    SandboxConfig,
    PromotionCriteria,
    StabilizationWindow
)
from abraxas.online.vector_map_loader import (
    load_vector_map,
    validate_vector_map,
    get_sources_for_domain,
    VectorMapValidationError
)
from abraxas.evolution.candidate_generator import (
    CandidateGenerator,
    generate_candidates_from_deltas
)
from abraxas.evolution.store import EvolutionStore
from abraxas.evolution.sandbox import SandboxExecutor, run_candidate_sandbox
from abraxas.evolution.promotion_gate import PromotionGate, validate_promotion


# Vector Map Tests

def test_vector_map_loads():
    """Test that vector map loads successfully."""
    vm_path = Path(__file__).parent.parent / "data" / "vector_maps" / "source_vector_map_v0_1.yaml"
    vm = load_vector_map(vm_path)

    assert vm.version == "0.1.0"
    assert len(vm.nodes) > 0
    assert len(vm.get_enabled_nodes()) > 0


def test_vector_map_validation():
    """Test vector map validation."""
    vm_path = Path(__file__).parent.parent / "data" / "vector_maps" / "source_vector_map_v0_1.yaml"
    vm = load_vector_map(vm_path)

    is_valid, errors = validate_vector_map(vm)
    assert is_valid, f"Validation failed: {errors}"
    assert len(errors) == 0


def test_vector_map_domain_filtering():
    """Test getting nodes by domain."""
    vm_path = Path(__file__).parent.parent / "data" / "vector_maps" / "source_vector_map_v0_1.yaml"
    vm = load_vector_map(vm_path)

    integrity_nodes = vm.get_nodes_by_domain("INTEGRITY")
    assert len(integrity_nodes) > 0
    assert all(n.domain == "INTEGRITY" for n in integrity_nodes)


# Candidate Generation Tests

def test_candidate_generator_aalmanac():
    """Test candidate generation from AALMANAC deltas."""
    aalmanac_deltas = {
        "term_velocities": {
            "deepfake": {"velocity": 0.85, "frequency": 120}
        },
        "frequency_spikes": [
            {"term": "misinformation", "spike_ratio": 4.5}
        ]
    }

    candidates = generate_candidates_from_deltas(
        aalmanac_deltas=aalmanac_deltas,
        run_id="test_run_aalmanac"
    )

    assert len(candidates) > 0
    assert any(c.source_domain == SourceDomain.AALMANAC for c in candidates)
    assert any(c.kind == CandidateKind.METRIC for c in candidates)
    assert any(c.kind == CandidateKind.PARAM_TWEAK for c in candidates)


def test_candidate_generator_mw():
    """Test candidate generation from MW deltas."""
    mw_deltas = {
        "synthetic_saturation": {"delta": 0.18, "current": 0.62},
        "cluster_splits": [
            {"cluster_id": "cluster_001", "confidence": 0.75}
        ]
    }

    candidates = generate_candidates_from_deltas(
        mw_deltas=mw_deltas,
        run_id="test_run_mw"
    )

    assert len(candidates) > 0
    assert any(c.source_domain == SourceDomain.MW for c in candidates)


def test_candidate_generator_integrity():
    """Test candidate generation from Integrity deltas."""
    integrity_deltas = {
        "ssi_trend": {"velocity": 0.12, "current": 0.58},
        "trust_surface": {"delta": -0.25, "current": 0.72}
    }

    candidates = generate_candidates_from_deltas(
        integrity_deltas=integrity_deltas,
        run_id="test_run_integrity"
    )

    assert len(candidates) > 0
    assert any(c.source_domain == SourceDomain.INTEGRITY for c in candidates)


def test_candidate_max_limits():
    """Test that candidate generation respects max limits."""
    # Create large deltas to trigger many candidates
    aalmanac_deltas = {
        "term_velocities": {
            f"term_{i}": {"velocity": 0.85, "frequency": 120}
            for i in range(20)
        }
    }

    generator = CandidateGenerator(max_candidates_per_run=10, max_per_source=4)
    candidates = generator.generate_candidates(
        aalmanac_deltas=aalmanac_deltas,
        run_id="test_max_limits"
    )

    # Should be limited to max_candidates_per_run
    assert len(candidates) <= 10


# Store and Ledger Tests

def test_candidate_store_save_load(tmp_path):
    """Test saving and loading candidates."""
    store = EvolutionStore(base_path=tmp_path)

    candidate = MetricCandidate(
        candidate_id="cand_test_001",
        kind=CandidateKind.PARAM_TWEAK,
        source_domain=SourceDomain.AALMANAC,
        proposed_at=datetime.now(timezone.utc).isoformat(),
        proposed_by="test",
        name="test_param",
        description="Test parameter",
        rationale="Testing store",
        param_path="test.param",
        current_value=1.0,
        proposed_value=1.5,
        priority=5
    )

    # Save
    store.save_candidate(candidate)

    # Load
    loaded = store.load_candidate("cand_test_001")
    assert loaded is not None
    assert loaded.candidate_id == candidate.candidate_id
    assert loaded.name == candidate.name


def test_candidate_ledger_chain_integrity(tmp_path):
    """Test ledger hash chain integrity."""
    store = EvolutionStore(base_path=tmp_path)

    # Append multiple candidates
    for i in range(5):
        candidate = MetricCandidate(
            candidate_id=f"cand_test_{i:03d}",
            kind=CandidateKind.PARAM_TWEAK,
            source_domain=SourceDomain.AALMANAC,
            proposed_at=datetime.now(timezone.utc).isoformat(),
            proposed_by="test",
            name=f"test_param_{i}",
            description=f"Test parameter {i}",
            rationale="Testing ledger",
            param_path=f"test.param.{i}",
            current_value=float(i),
            proposed_value=float(i + 1),
            priority=5
        )
        store.append_candidate_ledger(candidate)

    # Verify chain
    is_valid, errors = store.verify_ledger_chain("candidates")
    assert is_valid, f"Ledger chain invalid: {errors}"


def test_candidate_filtering(tmp_path):
    """Test filtering candidates."""
    store = EvolutionStore(base_path=tmp_path)

    # Create candidates of different kinds
    for kind in [CandidateKind.METRIC, CandidateKind.PARAM_TWEAK]:
        candidate = MetricCandidate(
            candidate_id=f"cand_{kind.value}_001",
            kind=kind,
            source_domain=SourceDomain.AALMANAC,
            proposed_at=datetime.now(timezone.utc).isoformat(),
            proposed_by="test",
            name=f"test_{kind.value}",
            description="Test",
            rationale="Testing filter",
            priority=5
        )
        store.save_candidate(candidate)

    # Filter for metrics only
    filter_criteria = CandidateFilter(kind=CandidateKind.METRIC)
    metrics = store.list_candidates(filter_criteria)

    assert len(metrics) > 0
    assert all(c.kind == CandidateKind.METRIC for c in metrics)


# Sandbox Tests

def test_sandbox_param_tweak():
    """Test sandbox execution for param tweak."""
    candidate = MetricCandidate(
        candidate_id="cand_sandbox_test_001",
        kind=CandidateKind.PARAM_TWEAK,
        source_domain=SourceDomain.INTEGRITY,
        proposed_at=datetime.now(timezone.utc).isoformat(),
        proposed_by="test",
        name="test_threshold",
        description="Test threshold tweak",
        rationale="Testing sandbox",
        param_path="test.threshold",
        current_value=0.5,
        proposed_value=0.7,
        expected_improvement={"brier_delta": -0.08},
        target_horizons=["H72H"],
        protected_horizons=["H30D"],
        priority=5
    )

    result = run_candidate_sandbox(candidate, run_id="test_sandbox")

    assert result.sandbox_id is not None
    assert result.candidate_id == candidate.candidate_id
    assert "brier_delta" in result.score_delta
    assert "passed" in result.model_dump()


def test_sandbox_metric_validation():
    """Test sandbox validation for new metric."""
    candidate = MetricCandidate(
        candidate_id="cand_metric_test_001",
        kind=CandidateKind.METRIC,
        source_domain=SourceDomain.MW,
        proposed_at=datetime.now(timezone.utc).isoformat(),
        proposed_by="test",
        name="test_metric",
        description="Test metric",
        rationale="Testing metric validation",
        implementation_spec={
            "formula": "test_formula",
            "inputs": ["a", "b"],
            "output_range": [0.0, 1.0],
            "computation": "local"
        },
        priority=5
    )

    result = run_candidate_sandbox(candidate, run_id="test_metric_sandbox")

    assert result.passed is True  # Spec is valid
    assert result.pass_criteria.get("spec_valid") is True
    assert result.pass_criteria.get("requires_implementation") is True


def test_sandbox_pass_criteria():
    """Test sandbox pass criteria checking."""
    config = SandboxConfig(
        improvement_threshold=10.0,  # Require 10% improvement
        regression_tolerance=0.02
    )

    candidate = MetricCandidate(
        candidate_id="cand_criteria_test_001",
        kind=CandidateKind.PARAM_TWEAK,
        source_domain=SourceDomain.INTEGRITY,
        proposed_at=datetime.now(timezone.utc).isoformat(),
        proposed_by="test",
        name="test_param",
        description="Test",
        rationale="Testing criteria",
        param_path="test.param",
        current_value=0.5,
        proposed_value=0.7,
        expected_improvement={"brier_delta": -0.08},
        target_horizons=["H72H"],
        priority=5
    )

    result = run_candidate_sandbox(candidate, config=config, run_id="test_criteria")

    # Check criteria keys exist
    assert "improvement_threshold" in result.pass_criteria
    assert "no_regressions" in result.pass_criteria
    assert "cost_bounds" in result.pass_criteria


# Stabilization Window Tests

def test_stabilization_window_tracking():
    """Test stabilization window tracking."""
    window = StabilizationWindow(candidate_id="cand_stab_001", window_size=3)

    assert window.consecutive_passes == 0
    assert not window.is_stable()

    # Record 3 passing runs
    for i in range(3):
        result = SandboxResult(
            sandbox_id=f"sbx_{i}",
            candidate_id="cand_stab_001",
            run_at=datetime.now(timezone.utc).isoformat(),
            run_id=f"run_{i}",
            hindcast_window_days=90,
            cases_tested=10,
            score_before={},
            score_after={},
            score_delta={},
            passed=True
        )
        window.record_run(result)

    assert window.consecutive_passes == 3
    assert window.is_stable()


def test_stabilization_window_reset_on_failure():
    """Test that stabilization window resets on failure."""
    window = StabilizationWindow(candidate_id="cand_stab_002", window_size=3)

    # 2 passes
    for i in range(2):
        result = SandboxResult(
            sandbox_id=f"sbx_pass_{i}",
            candidate_id="cand_stab_002",
            run_at=datetime.now(timezone.utc).isoformat(),
            run_id=f"run_pass_{i}",
            hindcast_window_days=90,
            cases_tested=10,
            score_before={},
            score_after={},
            score_delta={},
            passed=True
        )
        window.record_run(result)

    assert window.consecutive_passes == 2

    # 1 failure
    fail_result = SandboxResult(
        sandbox_id="sbx_fail",
        candidate_id="cand_stab_002",
        run_at=datetime.now(timezone.utc).isoformat(),
        run_id="run_fail",
        hindcast_window_days=90,
        cases_tested=10,
        score_before={},
        score_after={},
        score_delta={},
        passed=False,
        failure_reasons=["test failure"]
    )
    window.record_run(fail_result)

    # Should reset
    assert window.consecutive_passes == 0
    assert window.consecutive_failures == 1
    assert not window.is_stable()


# Promotion Gate Tests

def test_promotion_gate_stabilization(tmp_path):
    """Test promotion gate requires stabilization."""
    store = EvolutionStore(base_path=tmp_path)
    gate = PromotionGate(store=store)

    candidate = MetricCandidate(
        candidate_id="cand_promo_001",
        kind=CandidateKind.PARAM_TWEAK,
        source_domain=SourceDomain.INTEGRITY,
        proposed_at=datetime.now(timezone.utc).isoformat(),
        proposed_by="test",
        name="test_promo",
        description="Test promotion",
        rationale="Testing promotion",
        param_path="test.param",
        current_value=0.5,
        proposed_value=0.7,
        priority=5
    )

    # Only 2 passing results (need 3)
    sandbox_results = []
    for i in range(2):
        result = SandboxResult(
            sandbox_id=f"sbx_{i}",
            candidate_id=candidate.candidate_id,
            run_at=datetime.now(timezone.utc).isoformat(),
            run_id=f"run_{i}",
            hindcast_window_days=90,
            cases_tested=10,
            score_before={},
            score_after={},
            score_delta={"brier_delta": -0.08},
            passed=True
        )
        sandbox_results.append(result)

    can_promote, reasons = gate.can_promote(candidate, sandbox_results)
    assert not can_promote
    assert any("Not stabilized" in r for r in reasons)


def test_promotion_param_override(tmp_path):
    """Test promotion creates param override."""
    store = EvolutionStore(base_path=tmp_path)
    gate = PromotionGate(store=store)

    candidate = MetricCandidate(
        candidate_id="cand_param_override_001",
        kind=CandidateKind.PARAM_TWEAK,
        source_domain=SourceDomain.INTEGRITY,
        proposed_at=datetime.now(timezone.utc).isoformat(),
        proposed_by="test",
        name="test_param_override",
        description="Test param override",
        rationale="Testing override",
        param_path="test.override.param",
        current_value=0.5,
        proposed_value=0.8,
        priority=5
    )

    # 3 passing results
    sandbox_results = []
    for i in range(3):
        result = SandboxResult(
            sandbox_id=f"sbx_{i}",
            candidate_id=candidate.candidate_id,
            run_at=datetime.now(timezone.utc).isoformat(),
            run_id=f"run_{i}",
            hindcast_window_days=90,
            cases_tested=10,
            score_before={},
            score_after={},
            score_delta={"brier_delta": -0.08},
            passed=True
        )
        sandbox_results.append(result)

    promotion = gate.promote(candidate, sandbox_results)

    assert promotion.action_type == "param_override"
    assert "override_file" in promotion.action_details
    assert promotion.action_details["param_path"] == "test.override.param"
    assert promotion.action_details["value"] == 0.8


def test_promotion_creates_ticket(tmp_path):
    """Test promotion creates implementation ticket for metrics."""
    store = EvolutionStore(base_path=tmp_path)
    gate = PromotionGate(store=store)

    candidate = MetricCandidate(
        candidate_id="cand_ticket_001",
        kind=CandidateKind.METRIC,
        source_domain=SourceDomain.MW,
        proposed_at=datetime.now(timezone.utc).isoformat(),
        proposed_by="test",
        name="test_metric_ticket",
        description="Test metric",
        rationale="Testing ticket creation",
        implementation_spec={
            "formula": "test",
            "inputs": [],
            "output_range": [0, 1],
            "computation": "local"
        },
        priority=5
    )

    # 3 passing results (spec validation)
    sandbox_results = []
    for i in range(3):
        result = SandboxResult(
            sandbox_id=f"sbx_{i}",
            candidate_id=candidate.candidate_id,
            run_at=datetime.now(timezone.utc).isoformat(),
            run_id=f"run_{i}",
            hindcast_window_days=0,
            cases_tested=0,
            score_before={},
            score_after={},
            score_delta={},
            passed=True,
            pass_criteria={"spec_valid": True, "requires_implementation": True}
        )
        sandbox_results.append(result)

    promotion = gate.promote(candidate, sandbox_results)

    assert promotion.action_type == "implementation_ticket"
    assert "ticket_file" in promotion.action_details
    assert "ticket_id" in promotion.action_details


def test_promotion_rejects_unstable(tmp_path):
    """Test promotion rejects unstable candidates."""
    store = EvolutionStore(base_path=tmp_path)
    gate = PromotionGate(store=store)

    candidate = MetricCandidate(
        candidate_id="cand_unstable_001",
        kind=CandidateKind.PARAM_TWEAK,
        source_domain=SourceDomain.INTEGRITY,
        proposed_at=datetime.now(timezone.utc).isoformat(),
        proposed_by="test",
        name="test_unstable",
        description="Test",
        rationale="Testing rejection",
        param_path="test.param",
        current_value=0.5,
        proposed_value=0.7,
        priority=5
    )

    # Alternating pass/fail (unstable)
    sandbox_results = []
    for i in range(5):
        result = SandboxResult(
            sandbox_id=f"sbx_{i}",
            candidate_id=candidate.candidate_id,
            run_at=datetime.now(timezone.utc).isoformat(),
            run_id=f"run_{i}",
            hindcast_window_days=90,
            cases_tested=10,
            score_before={},
            score_after={},
            score_delta={},
            passed=(i % 2 == 0)  # Alternate pass/fail
        )
        sandbox_results.append(result)

    can_promote, reasons = gate.can_promote(candidate, sandbox_results)
    assert not can_promote


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
