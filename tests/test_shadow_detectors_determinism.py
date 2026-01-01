"""Determinism Tests for Shadow Detectors

Verifies that shadow detectors produce identical outputs for identical inputs.
"""

from __future__ import annotations

from abraxas.detectors.shadow import compliance_remix, meta_awareness, negative_space
from abraxas.detectors.shadow.registry import compute_all_detectors, serialize_detector_results
from abraxas.detectors.shadow.types import DetectorStatus


def test_compliance_remix_determinism():
    """Test Compliance vs Remix detector produces deterministic output."""
    context = {
        "drift": {"drift_score": 0.7, "similarity_early_late": 0.3},
        "novelty": {"new_to_window": True},
        "appearances": 5,
        "csp": {"COH": True, "FF": 0.4, "MIO": 0.3},
        "lifecycle_state": "Proto",
        "tau": {"tau_velocity": 0.8, "tau_half_life": 12.0, "observation_count": 10},
        "fog_type_counts": {"template": 2, "manufactured": 1},
        "weather_types": ["MW-03"],
    }

    result1 = compliance_remix.compute_detector(context)
    result2 = compliance_remix.compute_detector(context)

    # Results should be identical
    assert result1.status == result2.status
    assert result1.value == result2.value
    assert result1.subscores == result2.subscores
    assert result1.missing_keys == result2.missing_keys

    # Serialization should be deterministic
    dict1 = result1.model_dump()
    dict2 = result2.model_dump()
    assert dict1 == dict2


def test_meta_awareness_determinism():
    """Test Meta-Awareness detector produces deterministic output."""
    context = {
        "text": "This looks like a manufactured psyop. The algorithm is pushing ragebait again.",
        "dmx": {"overall_manipulation_risk": 0.65, "bucket": "HIGH"},
        "rdv": {"irony": 0.4, "humor": 0.3, "nihilism": 0.2},
        "efte": {"threshold": 0.7, "saturation_risk": "HIGH", "declining_engagement": True},
        "narrative_manipulation": {"rrs": 0.6, "cis": 0.5, "eil": 0.4},
        "network_campaign": {"cus": 0.6},
        "MRI": 65.0,
        "IRI": 40.0,
    }

    result1 = meta_awareness.compute_detector(context)
    result2 = meta_awareness.compute_detector(context)

    # Results should be identical
    assert result1.status == result2.status
    assert result1.value == result2.value
    assert result1.subscores == result2.subscores
    assert result1.missing_keys == result2.missing_keys

    # Serialization should be deterministic
    dict1 = result1.model_dump()
    dict2 = result2.model_dump()
    assert dict1 == dict2


def test_negative_space_determinism():
    """Test Negative Space detector produces deterministic output."""
    context = {
        "symbol_pool": [
            {"narrative_id": "topic_A", "source": "source1"},
            {"narrative_id": "topic_B", "source": "source1"},
        ],
        "timestamp": "2025-01-01T12:00:00Z",
    }

    history = [
        {
            "symbol_pool": [
                {"narrative_id": "topic_A", "source": "source1"},
                {"narrative_id": "topic_B", "source": "source2"},
                {"narrative_id": "topic_C", "source": "source3"},
            ]
        },
        {
            "symbol_pool": [
                {"narrative_id": "topic_A", "source": "source1"},
                {"narrative_id": "topic_B", "source": "source2"},
                {"narrative_id": "topic_C", "source": "source3"},
            ]
        },
        {
            "symbol_pool": [
                {"narrative_id": "topic_A", "source": "source1"},
                {"narrative_id": "topic_C", "source": "source3"},
            ]
        },
    ]

    result1 = negative_space.compute_detector(context, history)
    result2 = negative_space.compute_detector(context, history)

    # Results should be identical
    assert result1.status == result2.status
    assert result1.value == result2.value
    assert result1.subscores == result2.subscores
    assert result1.missing_keys == result2.missing_keys

    # Serialization should be deterministic
    dict1 = result1.model_dump()
    dict2 = result2.model_dump()
    assert dict1 == dict2


def test_registry_compute_all_determinism():
    """Test that compute_all_detectors produces deterministic output."""
    context = {
        "text": "Test text with manufactured content",
        "drift": {"drift_score": 0.5, "similarity_early_late": 0.5},
        "lifecycle_state": "Front",
        "tau": {"tau_velocity": 0.5, "tau_half_life": 24.0},
        "dmx": {"overall_manipulation_risk": 0.5, "bucket": "MED"},
        "symbol_pool": [
            {"narrative_id": "topic_A", "source": "source1"},
            {"narrative_id": "topic_B", "source": "source2"},
        ],
    }

    history = [
        {
            "symbol_pool": [
                {"narrative_id": "topic_A", "source": "source1"},
                {"narrative_id": "topic_B", "source": "source2"},
                {"narrative_id": "topic_C", "source": "source3"},
            ]
        },
        {
            "symbol_pool": [
                {"narrative_id": "topic_A", "source": "source1"},
                {"narrative_id": "topic_B", "source": "source2"},
                {"narrative_id": "topic_C", "source": "source3"},
            ]
        },
        {
            "symbol_pool": [
                {"narrative_id": "topic_A", "source": "source1"},
                {"narrative_id": "topic_C", "source": "source3"},
            ]
        },
    ]

    results1 = compute_all_detectors(context, history)
    results2 = compute_all_detectors(context, history)

    # Serialize and compare
    serialized1 = serialize_detector_results(results1)
    serialized2 = serialize_detector_results(results2)

    assert serialized1 == serialized2


def test_sorted_keys_in_output():
    """Test that all dict outputs have sorted keys for determinism."""
    context = {
        "text": "Test",
        "drift": {"drift_score": 0.5},
        "lifecycle_state": "Front",
        "tau": {"tau_velocity": 0.5},
        "dmx": {"overall_manipulation_risk": 0.5},
        "symbol_pool": [{"narrative_id": "topic_A"}],
    }

    history = [
        {"symbol_pool": [{"narrative_id": "topic_A"}, {"narrative_id": "topic_B"}]},
        {"symbol_pool": [{"narrative_id": "topic_A"}, {"narrative_id": "topic_C"}]},
        {"symbol_pool": [{"narrative_id": "topic_A"}, {"narrative_id": "topic_D"}]},
    ]

    results = compute_all_detectors(context, history)

    for detector_id, detector_value in results.items():
        serialized = detector_value.model_dump()

        # Check subscores are sorted
        if "subscores" in serialized and serialized["subscores"]:
            subscores_keys = list(serialized["subscores"].keys())
            assert subscores_keys == sorted(subscores_keys)

        # Check missing_keys are sorted
        if "missing_keys" in serialized and serialized["missing_keys"]:
            missing_keys = serialized["missing_keys"]
            assert missing_keys == sorted(missing_keys)

        # Check evidence dict is sorted (if present)
        if "evidence" in serialized and serialized["evidence"]:
            if isinstance(serialized["evidence"], dict):
                evidence_keys = list(serialized["evidence"].keys())
                assert evidence_keys == sorted(evidence_keys)
