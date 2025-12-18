"""Tests for OAS models and pydantic schemas."""

import pytest
from datetime import datetime, timezone

from abraxas.core.provenance import ProvenanceBundle, ProvenanceRef, hash_canonical_json
from abraxas.oasis.models import (
    OperatorStatus,
    OperatorCandidate,
    ValidationReport,
    StabilizationState,
    CanonDecision,
)


def test_operator_status_enum():
    """Test OperatorStatus enum values."""
    assert OperatorStatus.STAGING.value == "staging"
    assert OperatorStatus.CANONICAL.value == "canonical"
    assert OperatorStatus.LEGACY.value == "legacy"
    assert OperatorStatus.DEPRECATED.value == "deprecated"


def test_provenance_ref_creation():
    """Test ProvenanceRef creation and hashing."""
    ref = ProvenanceRef(
        scheme="test",
        path="/test/path",
        sha256="abc123",
    )

    assert ref.scheme == "test"
    assert ref.path == "/test/path"
    assert ref.sha256 == "abc123"

    # Test hashability
    ref_set = {ref}
    assert len(ref_set) == 1


def test_provenance_bundle_creation():
    """Test ProvenanceBundle creation with defaults."""
    bundle = ProvenanceBundle(
        inputs=[ProvenanceRef(scheme="test", path="/test", sha256="123")],
        transforms=["transform1", "transform2"],
        metrics={"accuracy": 0.95},
    )

    assert len(bundle.inputs) == 1
    assert len(bundle.transforms) == 2
    assert bundle.metrics["accuracy"] == 0.95
    assert bundle.created_by == "oasis"
    assert isinstance(bundle.created_at, datetime)


def test_operator_candidate_creation():
    """Test OperatorCandidate model validation."""
    provenance = ProvenanceBundle(
        inputs=[],
        transforms=["test"],
        metrics={},
    )

    candidate = OperatorCandidate(
        operator_id="test_op_001",
        label="Test Operator",
        class_tags=["test", "demo"],
        triggers=["trigger1", "trigger2"],
        readouts=["readout1"],
        failure_modes=["mode1"],
        scope={"domain": "test"},
        tests=["test1"],
        provenance=provenance,
        discovery_window={
            "start_ts": "2025-01-01T00:00:00Z",
            "end_ts": "2025-01-02T00:00:00Z",
            "sources": ["test"],
        },
        evidence_hashes=["hash1", "hash2"],
        candidate_score=0.85,
    )

    assert candidate.operator_id == "test_op_001"
    assert candidate.label == "Test Operator"
    assert len(candidate.triggers) == 2
    assert candidate.candidate_score == 0.85
    assert candidate.version == "1.0.0"
    assert candidate.status == OperatorStatus.STAGING


def test_operator_candidate_score_validation():
    """Test that candidate_score is validated between 0 and 1."""
    provenance = ProvenanceBundle(inputs=[], transforms=[], metrics={})

    # Valid score
    candidate = OperatorCandidate(
        operator_id="test",
        label="test",
        provenance=provenance,
        discovery_window={},
        candidate_score=0.5,
    )
    assert candidate.candidate_score == 0.5

    # Invalid score should raise validation error
    with pytest.raises(Exception):  # Pydantic validation error
        OperatorCandidate(
            operator_id="test",
            label="test",
            provenance=provenance,
            discovery_window={},
            candidate_score=1.5,  # Invalid: > 1.0
        )


def test_validation_report_creation():
    """Test ValidationReport model."""
    provenance = ProvenanceBundle(inputs=[], transforms=["validation"], metrics={})

    report = ValidationReport(
        passed=True,
        metrics_before={"entropy": 2.5, "false_rate": 0.3},
        metrics_after={"entropy": 2.0, "false_rate": 0.2},
        deltas={"entropy": -0.5, "false_rate": -0.1},
        notes=["Validation successful"],
        provenance=provenance,
    )

    assert report.passed is True
    assert report.deltas["entropy"] == -0.5
    assert len(report.notes) == 1
    assert isinstance(report.timestamp, datetime)


def test_stabilization_state():
    """Test StabilizationState model."""
    state = StabilizationState(
        operator_id="test_op",
        cycles_required=3,
        cycles_completed=2,
        stable=False,
    )

    assert state.operator_id == "test_op"
    assert state.cycles_required == 3
    assert state.cycles_completed == 2
    assert state.stable is False
    assert isinstance(state.started_at, datetime)
    assert state.completed_at is None


def test_canon_decision():
    """Test CanonDecision model."""
    provenance = ProvenanceBundle(inputs=[], transforms=["canonization"], metrics={})
    ledger_ref = ProvenanceRef(scheme="ledger", path="/ledger", sha256="abc")

    decision = CanonDecision(
        adopted=True,
        reason="All gates passed",
        operator_id="test_op",
        version="1.0.0",
        ledger_ref=ledger_ref,
        metrics_delta={"entropy": -0.1},
        provenance=provenance,
    )

    assert decision.adopted is True
    assert decision.reason == "All gates passed"
    assert decision.operator_id == "test_op"
    assert decision.decided_by == "oasis_canonizer"
    assert isinstance(decision.decided_at, datetime)


def test_hash_canonical_json_determinism():
    """Test that hash_canonical_json is deterministic."""
    obj = {"b": 2, "a": 1, "c": [3, 2, 1]}

    hash1 = hash_canonical_json(obj)
    hash2 = hash_canonical_json(obj)

    assert hash1 == hash2

    # Different order should produce same hash
    obj2 = {"c": [3, 2, 1], "a": 1, "b": 2}
    hash3 = hash_canonical_json(obj2)

    assert hash1 == hash3


def test_operator_candidate_serialization():
    """Test that OperatorCandidate can be serialized and deserialized."""
    provenance = ProvenanceBundle(inputs=[], transforms=["test"], metrics={})

    candidate = OperatorCandidate(
        operator_id="test_op",
        label="Test",
        provenance=provenance,
        discovery_window={},
    )

    # Serialize
    data = candidate.model_dump()
    assert isinstance(data, dict)

    # Deserialize
    candidate2 = OperatorCandidate(**data)
    assert candidate2.operator_id == candidate.operator_id
    assert candidate2.label == candidate.label


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
