"""Tests for Metric Governance: Gate Enforcement

Ensures all promotion gates enforce correctly:
- Provenance Gate
- Falsifiability Gate
- Non-Redundancy Gate
- Rent-Payment Gate
- Ablation Gate
- Stabilization Gate
"""

import numpy as np
import pytest

from abraxas.metrics.evaluate import MetricEvaluator
from abraxas.metrics.governance import (
    CandidateMetric,
    CandidateStatus,
    FalsifiabilityCriteria,
    ProvenanceMeta,
)


@pytest.fixture
def valid_candidate():
    """Create a valid candidate metric for testing."""
    provenance = ProvenanceMeta(
        metric_id="TEST_METRIC",
        description="Test metric for governance validation",
        units="dimensionless",
        valid_range={"min": 0.0, "max": 1.0},
        dependencies=[],
        compute_fn="test.compute_metric",
        input_sources=[
            {"source": "test_data", "hash": "a" * 64}
        ],
    )

    falsifiability = FalsifiabilityCriteria(
        predictions_influenced=["test_var_1", "test_var_2"],
        disconfirmation_criteria={"threshold": "error > 0.1"},
        evaluation_window=5,
    )

    return CandidateMetric(
        provenance=provenance,
        falsifiability=falsifiability,
        status=CandidateStatus.PROPOSED,
        required_rune_bindings=["RUNE_TEST"],
        target_sim_variables=["test_var_1", "test_var_2"],
    )


def test_provenance_gate_pass(valid_candidate):
    """Test provenance gate with valid candidate."""
    evaluator = MetricEvaluator()
    result = evaluator.evaluate_provenance_gate(valid_candidate)
    assert result is True


def test_provenance_gate_fail_no_metric_id():
    """Test provenance gate fails with missing metric_id."""
    provenance = ProvenanceMeta(
        metric_id="",  # Empty metric_id
        description="Test",
        units="test",
        valid_range={"min": 0.0, "max": 1.0},
        dependencies=[],
        compute_fn="test.fn",
        input_sources=[{"source": "test", "hash": "a" * 64}],
    )

    falsifiability = FalsifiabilityCriteria(
        predictions_influenced=["var1"],
        disconfirmation_criteria={"test": "criteria"},
        evaluation_window=5,
    )

    candidate = CandidateMetric(
        provenance=provenance,
        falsifiability=falsifiability,
        status=CandidateStatus.PROPOSED,
        required_rune_bindings=["RUNE_TEST"],
        target_sim_variables=["var1"],
    )

    evaluator = MetricEvaluator()
    result = evaluator.evaluate_provenance_gate(candidate)
    assert result is False


def test_provenance_gate_fail_no_input_sources():
    """Test provenance gate fails with no input sources."""
    provenance = ProvenanceMeta(
        metric_id="TEST_METRIC",
        description="Test",
        units="test",
        valid_range={"min": 0.0, "max": 1.0},
        dependencies=[],
        compute_fn="test.fn",
        input_sources=[],  # Empty input sources
    )

    falsifiability = FalsifiabilityCriteria(
        predictions_influenced=["var1"],
        disconfirmation_criteria={"test": "criteria"},
        evaluation_window=5,
    )

    candidate = CandidateMetric(
        provenance=provenance,
        falsifiability=falsifiability,
        status=CandidateStatus.PROPOSED,
        required_rune_bindings=["RUNE_TEST"],
        target_sim_variables=["var1"],
    )

    evaluator = MetricEvaluator()
    result = evaluator.evaluate_provenance_gate(candidate)
    assert result is False


def test_falsifiability_gate_pass(valid_candidate):
    """Test falsifiability gate with valid candidate."""
    evaluator = MetricEvaluator()
    result = evaluator.evaluate_falsifiability_gate(valid_candidate)
    assert result is True


def test_falsifiability_gate_fail_no_predictions():
    """Test falsifiability gate fails with no predictions_influenced."""
    provenance = ProvenanceMeta(
        metric_id="TEST_METRIC",
        description="Test",
        units="test",
        valid_range={"min": 0.0, "max": 1.0},
        dependencies=[],
        compute_fn="test.fn",
        input_sources=[{"source": "test", "hash": "a" * 64}],
    )

    falsifiability = FalsifiabilityCriteria(
        predictions_influenced=[],  # Empty predictions
        disconfirmation_criteria={"test": "criteria"},
        evaluation_window=5,
    )

    candidate = CandidateMetric(
        provenance=provenance,
        falsifiability=falsifiability,
        status=CandidateStatus.PROPOSED,
        required_rune_bindings=["RUNE_TEST"],
        target_sim_variables=["var1"],
    )

    evaluator = MetricEvaluator()
    result = evaluator.evaluate_falsifiability_gate(candidate)
    assert result is False


def test_redundancy_gate_pass_low_correlation(valid_candidate):
    """Test redundancy gate passes with low correlation."""
    evaluator = MetricEvaluator()

    np.random.seed(42)
    candidate_values = np.random.randn(100)
    canonical_metrics = {
        "METRIC_A": np.random.randn(100),  # Uncorrelated
        "METRIC_B": np.random.randn(100),  # Uncorrelated
    }

    passed, scores = evaluator.evaluate_redundancy_gate(
        valid_candidate, candidate_values, canonical_metrics
    )

    assert passed is True
    assert scores.max_corr < 0.85


def test_redundancy_gate_fail_high_correlation(valid_candidate):
    """Test redundancy gate fails with high correlation."""
    evaluator = MetricEvaluator()

    np.random.seed(42)
    candidate_values = np.random.randn(100)
    # Create highly correlated canonical metric
    canonical_metrics = {
        "METRIC_A": candidate_values + np.random.randn(100) * 0.01,  # Nearly identical
    }

    passed, scores = evaluator.evaluate_redundancy_gate(
        valid_candidate, candidate_values, canonical_metrics
    )

    assert passed is False
    assert scores.max_corr >= 0.85


def test_rent_payment_gate_pass():
    """Test rent payment gate with measurable lift."""
    evaluator = MetricEvaluator()

    baseline = {
        "forecast_error": 0.25,
        "brier_score": 0.20,
        "calibration": 0.70,
        "misinfo_auc": 0.75,
        "divergence_explained": 0.30,
    }

    with_candidate = {
        "forecast_error": 0.22,  # 3% improvement
        "brier_score": 0.19,  # 1% improvement
        "calibration": 0.76,  # 6% improvement
        "misinfo_auc": 0.79,  # 4% improvement
        "divergence_explained": 0.37,  # 7% improvement
    }

    passed, lift = evaluator.evaluate_rent_payment_gate(baseline, with_candidate)

    assert passed is True
    assert lift.forecast_error_delta < 0  # Improvement (negative)
    assert lift.calibration_delta > 0  # Improvement (positive)


def test_rent_payment_gate_fail_no_lift():
    """Test rent payment gate fails with no measurable lift."""
    evaluator = MetricEvaluator()

    baseline = {
        "forecast_error": 0.25,
        "brier_score": 0.20,
        "calibration": 0.70,
        "misinfo_auc": 0.75,
        "divergence_explained": 0.30,
    }

    # Identical performance (no lift)
    with_candidate = baseline.copy()

    passed, lift = evaluator.evaluate_rent_payment_gate(baseline, with_candidate)

    assert passed is False


def test_ablation_gate_pass():
    """Test ablation gate with performance degradation."""
    evaluator = MetricEvaluator()

    full = {
        "forecast_error": 0.20,
        "brier_score": 0.18,
        "calibration": 0.80,
        "misinfo_auc": 0.85,
    }

    # Ablated (worse performance)
    ablated = {
        "forecast_error": 0.23,  # Worse
        "brier_score": 0.20,  # Worse
        "calibration": 0.76,  # Worse
        "misinfo_auc": 0.82,  # Worse
    }

    passed, results = evaluator.evaluate_ablation_gate(full, ablated)

    assert passed is True
    assert results["forecast_error_degradation"] > 0


def test_ablation_gate_fail_no_degradation():
    """Test ablation gate fails if removal doesn't degrade performance."""
    evaluator = MetricEvaluator()

    full = {
        "forecast_error": 0.20,
        "brier_score": 0.18,
        "calibration": 0.80,
        "misinfo_auc": 0.85,
    }

    # Ablated (same or better - metric is useless)
    ablated = full.copy()

    passed, results = evaluator.evaluate_ablation_gate(full, ablated)

    assert passed is False


def test_stabilization_gate_pass():
    """Test stabilization gate with stable performance."""
    evaluator = MetricEvaluator()

    # 6 cycles of stable performance
    performance_history = [
        {"forecast_error": 0.20 + i * 0.001, "brier_score": 0.18}
        for i in range(6)
    ]

    passed, scores = evaluator.evaluate_stabilization_gate(
        performance_history, cycles_required=5
    )

    assert passed is True
    assert scores.cycles_passed >= 5
    assert scores.performance_variance < 0.05


def test_stabilization_gate_fail_insufficient_cycles():
    """Test stabilization gate fails with insufficient cycles."""
    evaluator = MetricEvaluator()

    # Only 3 cycles (need 5)
    performance_history = [
        {"forecast_error": 0.20, "brier_score": 0.18}
        for _ in range(3)
    ]

    passed, scores = evaluator.evaluate_stabilization_gate(
        performance_history, cycles_required=5
    )

    assert passed is False
    assert scores.cycles_passed < 5


def test_stabilization_gate_fail_high_variance():
    """Test stabilization gate fails with high performance variance."""
    evaluator = MetricEvaluator()

    # 6 cycles but very unstable
    performance_history = [
        {"forecast_error": 0.20 + i * 0.1, "brier_score": 0.18}
        for i in range(6)
    ]

    passed, scores = evaluator.evaluate_stabilization_gate(
        performance_history, cycles_required=5
    )

    assert passed is False
    assert scores.performance_variance >= 0.05
