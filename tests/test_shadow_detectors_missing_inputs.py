"""Missing Inputs Tests for Shadow Detectors

Verifies that detectors return not_computable status when required inputs are missing.
"""

from __future__ import annotations

from abraxas.detectors.shadow import compliance_remix, meta_awareness, negative_space
from abraxas.detectors.shadow.types import DetectorStatus


def test_compliance_remix_missing_required_inputs():
    """Test Compliance vs Remix detector with missing required inputs."""
    # Missing all required fields
    empty_context = {}
    result = compliance_remix.compute_detector(empty_context)
    assert result.status == DetectorStatus.NOT_COMPUTABLE
    assert result.value is None
    assert "drift_score" in result.missing_keys or "lifecycle_state" in result.missing_keys


def test_compliance_remix_with_some_inputs():
    """Test Compliance vs Remix detector with some inputs present."""
    # Has some but not all required inputs
    partial_context = {
        "drift": {"drift_score": 0.5},
        # Missing lifecycle_state and tau_velocity
    }
    result = compliance_remix.compute_detector(partial_context)
    assert result.status == DetectorStatus.NOT_COMPUTABLE
    assert result.value is None
    assert len(result.missing_keys) > 0


def test_compliance_remix_with_all_required_inputs():
    """Test Compliance vs Remix detector with all required inputs."""
    # Has all required inputs
    context = {
        "drift": {"drift_score": 0.5, "similarity_early_late": 0.5},
        "lifecycle_state": "Front",
        "tau": {"tau_velocity": 0.5, "tau_half_life": 24.0},
    }
    result = compliance_remix.compute_detector(context)
    assert result.status == DetectorStatus.OK
    assert result.value is not None
    # Missing_keys should be empty or only contain optional keys
    for key in result.missing_keys:
        assert key not in ["drift_score", "lifecycle_state", "tau_velocity"]


def test_meta_awareness_missing_text():
    """Test Meta-Awareness detector with missing text input."""
    # Missing text (required for keyword detection)
    context_no_text = {
        "dmx": {"overall_manipulation_risk": 0.5, "bucket": "MED"},
        "rdv": {"irony": 0.3, "humor": 0.2},
    }
    result = meta_awareness.compute_detector(context_no_text)
    assert result.status == DetectorStatus.NOT_COMPUTABLE
    assert result.value is None
    assert "text" in result.missing_keys


def test_meta_awareness_with_empty_text():
    """Test Meta-Awareness detector with empty text."""
    # Empty text is also not computable
    context_empty_text = {
        "text": "",
        "dmx": {"overall_manipulation_risk": 0.5},
    }
    result = meta_awareness.compute_detector(context_empty_text)
    assert result.status == DetectorStatus.NOT_COMPUTABLE
    assert result.value is None


def test_meta_awareness_with_text():
    """Test Meta-Awareness detector with valid text input."""
    context = {
        "text": "Some valid text content",
        "dmx": {"overall_manipulation_risk": 0.5, "bucket": "MED"},
    }
    result = meta_awareness.compute_detector(context)
    assert result.status == DetectorStatus.OK
    assert result.value is not None


def test_negative_space_missing_history():
    """Test Negative Space detector with insufficient history."""
    context = {
        "symbol_pool": [
            {"narrative_id": "topic_A", "source": "source1"},
        ],
    }

    # No history
    result_no_history = negative_space.compute_detector(context, history=None)
    assert result_no_history.status == DetectorStatus.NOT_COMPUTABLE
    assert result_no_history.value is None
    assert "sufficient_history" in result_no_history.missing_keys

    # Insufficient history (< 3 entries by default)
    insufficient_history = [
        {"symbol_pool": [{"narrative_id": "topic_A"}]},
        {"symbol_pool": [{"narrative_id": "topic_B"}]},
    ]
    result_insufficient = negative_space.compute_detector(context, insufficient_history)
    assert result_insufficient.status == DetectorStatus.NOT_COMPUTABLE
    assert result_insufficient.value is None


def test_negative_space_with_sufficient_history():
    """Test Negative Space detector with sufficient history."""
    context = {
        "symbol_pool": [
            {"narrative_id": "topic_A", "source": "source1"},
        ],
    }

    sufficient_history = [
        {"symbol_pool": [{"narrative_id": "topic_A"}, {"narrative_id": "topic_B"}]},
        {"symbol_pool": [{"narrative_id": "topic_A"}, {"narrative_id": "topic_C"}]},
        {"symbol_pool": [{"narrative_id": "topic_A"}, {"narrative_id": "topic_D"}]},
    ]

    result = negative_space.compute_detector(context, sufficient_history)
    assert result.status == DetectorStatus.OK
    assert result.value is not None


def test_missing_keys_are_sorted():
    """Test that missing_keys lists are always sorted."""
    # Empty context to trigger maximum missing keys
    contexts = [
        {},  # Compliance remix
        {},  # Meta awareness
        {"symbol_pool": []},  # Negative space
    ]

    detectors = [
        compliance_remix.compute_detector,
        meta_awareness.compute_detector,
        lambda ctx: negative_space.compute_detector(ctx, history=[]),
    ]

    for context, detector_fn in zip(contexts, detectors):
        result = detector_fn(context)
        if result.missing_keys:
            assert result.missing_keys == sorted(result.missing_keys)


def test_optional_vs_required_inputs():
    """Test that detectors distinguish between required and optional inputs."""
    # Compliance remix with only required inputs
    minimal_context = {
        "drift": {"drift_score": 0.5},
        "lifecycle_state": "Front",
        "tau": {"tau_velocity": 0.5},
    }

    result = compliance_remix.compute_detector(minimal_context)

    # Should be OK even without optional inputs
    assert result.status == DetectorStatus.OK
    assert result.value is not None

    # Optional inputs may be listed in used_keys even if not present
    # (they default to 0.0 or other defaults)
