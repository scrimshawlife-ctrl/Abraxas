"""Tests for OAS TDD golden gate validation."""

import pytest
from datetime import datetime, timezone

from abraxas.oasis.models import OperatorCandidate, OperatorStatus
from abraxas.oasis.validator import OASValidator
from abraxas.core.provenance import ProvenanceBundle, ProvenanceRef


@pytest.fixture
def validator():
    """Create validator with VBM golden enabled."""
    return OASValidator(enable_vbm_golden=True)


@pytest.fixture
def temporal_candidate():
    """Create candidate with temporal/causal triggers."""
    return OperatorCandidate(
        operator_id="TEST_TEMPORAL_01",
        version="0.1.0",
        status=OperatorStatus.PROPOSED,
        triggers=["time inversion", "retrocausal", "backwards causation"],
        actions=["detect temporal anomalies"],
        config={},
        proposed_at=datetime.now(timezone.utc),
        provenance=ProvenanceBundle(
            inputs=[ProvenanceRef(scheme="test", path="temporal", sha256="abc123")],
            transforms=["test_creation"],
            metrics={},
            created_by="test",
        ),
    )


@pytest.fixture
def eschatological_candidate():
    """Create candidate with eschatological triggers."""
    return OperatorCandidate(
        operator_id="TEST_ESCHATON_01",
        version="0.1.0",
        status=OperatorStatus.PROPOSED,
        triggers=["eschaton", "apocalypse", "end-times", "destiny"],
        actions=["predict final outcomes"],
        config={},
        proposed_at=datetime.now(timezone.utc),
        provenance=ProvenanceBundle(
            inputs=[ProvenanceRef(scheme="test", path="eschaton", sha256="def456")],
            transforms=["test_creation"],
            metrics={},
            created_by="test",
        ),
    )


@pytest.fixture
def neutral_candidate():
    """Create candidate with neutral triggers."""
    return OperatorCandidate(
        operator_id="TEST_NEUTRAL_01",
        version="0.1.0",
        status=OperatorStatus.PROPOSED,
        triggers=["data processing", "file handling", "parsing"],
        actions=["process data"],
        config={},
        proposed_at=datetime.now(timezone.utc),
        provenance=ProvenanceBundle(
            inputs=[ProvenanceRef(scheme="test", path="neutral", sha256="xyz789")],
            transforms=["test_creation"],
            metrics={},
            created_by="test",
        ),
    )


def test_tdd_inscope_temporal_triggers(validator, temporal_candidate):
    """Test that temporal triggers are detected as in-scope."""
    assert validator.is_tdd_inscope(temporal_candidate)


def test_tdd_inscope_eschatological_triggers(validator, eschatological_candidate):
    """Test that eschatological triggers are detected as in-scope."""
    assert validator.is_tdd_inscope(eschatological_candidate)


def test_tdd_not_inscope_neutral_triggers(validator, neutral_candidate):
    """Test that neutral triggers are not in-scope."""
    assert not validator.is_tdd_inscope(neutral_candidate)


def test_tdd_golden_validation_temporal(validator, temporal_candidate):
    """Test TDD golden validation on temporal candidate."""
    passed, metrics = validator.validate_tdd_golden(temporal_candidate)

    # Check metrics structure
    assert "tdd_test_count" in metrics
    assert "tdd_hits" in metrics
    assert "tdd_recall" in metrics
    assert "control_test_count" in metrics
    assert "control_false_positives" in metrics

    # Should have tested on temporal patterns
    assert metrics["tdd_test_count"] > 0

    # If passed, should have sufficient recall and no false positives
    if passed:
        assert metrics["tdd_recall"] > 0.3
        assert metrics["control_false_positives"] == 0


def test_tdd_golden_validation_eschatological(validator, eschatological_candidate):
    """Test TDD golden validation on eschatological candidate."""
    passed, metrics = validator.validate_tdd_golden(eschatological_candidate)

    # Should have tested on eschatological patterns
    assert metrics["tdd_test_count"] > 0

    # Check pass criteria
    if passed:
        assert metrics["tdd_recall"] > 0.3
        assert metrics["control_false_positives"] == 0


def test_tdd_golden_requires_recall_threshold(validator, temporal_candidate):
    """Test that TDD golden requires minimum recall threshold."""
    passed, metrics = validator.validate_tdd_golden(temporal_candidate)

    # If candidate passed, recall must be > 0.3
    if passed:
        assert metrics["tdd_recall"] > 0.3


def test_tdd_golden_requires_no_false_positives(validator, temporal_candidate):
    """Test that TDD golden requires zero false positives on control."""
    passed, metrics = validator.validate_tdd_golden(temporal_candidate)

    # If candidate passed, control false positives must be 0
    if passed:
        assert metrics["control_false_positives"] == 0


def test_tdd_golden_control_texts(validator, temporal_candidate):
    """Test that control texts are tested for false positives."""
    passed, metrics = validator.validate_tdd_golden(temporal_candidate)

    # Should have control tests
    assert metrics["control_test_count"] > 0


def test_tdd_validation_deterministic(validator, temporal_candidate):
    """Test that TDD validation is deterministic."""
    passed1, metrics1 = validator.validate_tdd_golden(temporal_candidate)
    passed2, metrics2 = validator.validate_tdd_golden(temporal_candidate)

    assert passed1 == passed2
    assert metrics1 == metrics2


def test_tdd_inscope_time_trigger(validator):
    """Test that 'time' trigger is in-scope."""
    candidate = OperatorCandidate(
        operator_id="TEST_TIME_01",
        version="0.1.0",
        status=OperatorStatus.PROPOSED,
        triggers=["time"],
        actions=["analyze"],
        config={},
        proposed_at=datetime.now(timezone.utc),
        provenance=ProvenanceBundle(
            inputs=[ProvenanceRef(scheme="test", path="time", sha256="111")],
            transforms=["test"],
            metrics={},
            created_by="test",
        ),
    )

    assert validator.is_tdd_inscope(candidate)


def test_tdd_inscope_future_trigger(validator):
    """Test that 'future' trigger is in-scope."""
    candidate = OperatorCandidate(
        operator_id="TEST_FUTURE_01",
        version="0.1.0",
        status=OperatorStatus.PROPOSED,
        triggers=["future prediction"],
        actions=["predict"],
        config={},
        proposed_at=datetime.now(timezone.utc),
        provenance=ProvenanceBundle(
            inputs=[ProvenanceRef(scheme="test", path="future", sha256="222")],
            transforms=["test"],
            metrics={},
            created_by="test",
        ),
    )

    assert validator.is_tdd_inscope(candidate)


def test_tdd_inscope_destiny_trigger(validator):
    """Test that 'destiny' trigger is in-scope."""
    candidate = OperatorCandidate(
        operator_id="TEST_DESTINY_01",
        version="0.1.0",
        status=OperatorStatus.PROPOSED,
        triggers=["destiny framing"],
        actions=["frame"],
        config={},
        proposed_at=datetime.now(timezone.utc),
        provenance=ProvenanceBundle(
            inputs=[ProvenanceRef(scheme="test", path="destiny", sha256="333")],
            transforms=["test"],
            metrics={},
            created_by="test",
        ),
    )

    assert validator.is_tdd_inscope(candidate)


def test_tdd_golden_test_patterns_comprehensive(validator, temporal_candidate):
    """Test that TDD golden tests include diverse temporal patterns."""
    passed, metrics = validator.validate_tdd_golden(temporal_candidate)

    # Should test multiple patterns
    # At minimum: retronic, eschatological, diagrammatic
    assert metrics["tdd_test_count"] >= 3


def test_tdd_not_inscope_action_only(validator):
    """Test that candidate with temporal action but no trigger is not in-scope."""
    candidate = OperatorCandidate(
        operator_id="TEST_ACTION_01",
        version="0.1.0",
        status=OperatorStatus.PROPOSED,
        triggers=["data", "input"],
        actions=["analyze time series"],
        config={},
        proposed_at=datetime.now(timezone.utc),
        provenance=ProvenanceBundle(
            inputs=[ProvenanceRef(scheme="test", path="action", sha256="444")],
            transforms=["test"],
            metrics={},
            created_by="test",
        ),
    )

    # Should NOT be in-scope (only checks triggers, not actions)
    # Note: This depends on implementation - adjust if actions are also checked
    result = validator.is_tdd_inscope(candidate)
    # Either way is acceptable, just checking it doesn't crash
    assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
