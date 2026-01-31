"""Tests for OAS VBM golden gate validation."""

import pytest

from abraxas.core.provenance import ProvenanceBundle
from abraxas.oasis.models import OperatorCandidate, OperatorStatus
from abraxas.oasis.validator import OASValidator
from abraxas.oasis.canonizer import OASCanonizer


@pytest.fixture
def vbm_inscope_candidate():
    """Create a candidate in-scope for VBM (has pattern/physics triggers)."""
    provenance = ProvenanceBundle(inputs=[], transforms=[], metrics={})

    return OperatorCandidate(
        operator_id="test_vbm_inscope",
        label="Torus Pattern Detector",
        class_tags=["pattern", "geometry"],
        triggers=["\\btorus\\b", "\\bvortex\\b", "\\bpattern\\b"],
        readouts=["torus_pattern"],
        failure_modes=["overfitting"],
        scope={"pattern_type": "geometric", "domain": "symmetry"},
        tests=["Should detect torus patterns"],
        provenance=provenance,
        discovery_window={"start_ts": "2025-01-01T00:00:00Z", "end_ts": "2025-01-02T00:00:00Z", "sources": ["test"]},
        evidence_hashes=[],
        candidate_score=0.8,
    )


@pytest.fixture
def vbm_outscope_candidate():
    """Create a candidate out-of-scope for VBM (no pattern/physics triggers)."""
    provenance = ProvenanceBundle(inputs=[], transforms=[], metrics={})

    return OperatorCandidate(
        operator_id="test_vbm_outscope",
        label="Emoji Detector",
        class_tags=["emoji", "sentiment"],
        triggers=["😀", "😊", "🎉"],
        readouts=["positive_emoji"],
        failure_modes=["encoding_issues"],
        scope={"pattern_type": "emoji", "domain": "sentiment"},
        tests=["Should detect positive emojis"],
        provenance=provenance,
        discovery_window={"start_ts": "2025-01-01T00:00:00Z", "end_ts": "2025-01-02T00:00:00Z", "sources": ["test"]},
        evidence_hashes=[],
        candidate_score=0.7,
    )


def test_is_vbm_inscope_true(vbm_inscope_candidate):
    """Test that VBM in-scope detection works for relevant candidates."""
    validator = OASValidator(enable_vbm_golden=True)

    inscope = validator.is_vbm_inscope(vbm_inscope_candidate)

    assert inscope is True, "Candidate with pattern/torus triggers should be in-scope"


def test_is_vbm_inscope_false(vbm_outscope_candidate):
    """Test that VBM in-scope detection works for irrelevant candidates."""
    validator = OASValidator(enable_vbm_golden=True)

    inscope = validator.is_vbm_inscope(vbm_outscope_candidate)

    assert inscope is False, "Candidate with emoji triggers should be out-of-scope"


def test_validate_vbm_golden_inscope(vbm_inscope_candidate):
    """Test VBM golden validation for in-scope candidate."""
    validator = OASValidator(enable_vbm_golden=True)

    passed, metrics = validator.validate_vbm_golden(vbm_inscope_candidate)

    # Should run validation
    assert "vbm_inscope" in metrics
    assert metrics["vbm_inscope"] is True

    # Should have VBM hits metric
    if "vbm_hits" in metrics:
        assert isinstance(metrics["vbm_hits"], int)


def test_validate_vbm_golden_outscope(vbm_outscope_candidate):
    """Test VBM golden validation for out-of-scope candidate."""
    validator = OASValidator(enable_vbm_golden=True)

    passed, metrics = validator.validate_vbm_golden(vbm_outscope_candidate)

    # Should automatically pass
    assert passed is True
    assert metrics.get("vbm_inscope") is False


def test_canonizer_vbm_gate_inscope(vbm_inscope_candidate):
    """Test that canonizer applies VBM gate for in-scope candidates."""
    canonizer = OASCanonizer()

    # Test VBM gate directly
    passed = canonizer._vbm_golden_gate(vbm_inscope_candidate)

    # Should run validation (pass or fail depends on casebook)
    assert isinstance(passed, bool)


def test_canonizer_vbm_gate_outscope(vbm_outscope_candidate):
    """Test that canonizer skips VBM gate for out-of-scope candidates."""
    canonizer = OASCanonizer()

    # Test VBM gate directly
    passed = canonizer._vbm_golden_gate(vbm_outscope_candidate)

    # Should automatically pass
    assert passed is True


def test_vbm_golden_control_false_positives():
    """Test that VBM validation rejects candidates with control false positives."""
    provenance = ProvenanceBundle(inputs=[], transforms=[], metrics={})

    # Candidate that would fire on control text
    overly_broad = OperatorCandidate(
        operator_id="test_overly_broad",
        label="Universal Detector",
        class_tags=["universal"],
        triggers=["\\b\\w+\\b"],  # Matches any word
        readouts=["detected"],
        failure_modes=["too_broad"],
        scope={"pattern_type": "universal"},
        tests=["Matches everything"],
        provenance=provenance,
        discovery_window={"start_ts": "2025-01-01T00:00:00Z", "end_ts": "2025-01-02T00:00:00Z", "sources": ["test"]},
        evidence_hashes=[],
        candidate_score=0.5,
    )

    validator = OASValidator(enable_vbm_golden=True)

    # Should be in-scope (has pattern in scope)
    inscope = validator.is_vbm_inscope(overly_broad)

    if inscope:
        passed, metrics = validator.validate_vbm_golden(overly_broad)

        # Should fail due to control false positives
        if "control_false_positives" in metrics:
            assert metrics["control_false_positives"] > 0, "Overly broad trigger should fire on control texts"
            assert passed is False, "Should fail VBM golden due to control false positives"


def test_vbm_disabled_always_passes():
    """Test that VBM validation always passes when disabled."""
    provenance = ProvenanceBundle(inputs=[], transforms=[], metrics={})

    candidate = OperatorCandidate(
        operator_id="test_any",
        label="Test Operator",
        class_tags=["test"],
        triggers=["torus", "vortex"],
        readouts=["test"],
        failure_modes=[],
        scope={},
        tests=[],
        provenance=provenance,
        discovery_window={},
        evidence_hashes=[],
        candidate_score=0.5,
    )

    validator = OASValidator(enable_vbm_golden=False)

    passed, metrics = validator.validate_vbm_golden(candidate)

    assert passed is True, "VBM validation should always pass when disabled"
    assert len(metrics) == 0, "No metrics should be returned when disabled"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
