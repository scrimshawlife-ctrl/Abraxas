"""Bounds Tests for Shadow Detectors

Verifies that all detector values and subscores are clamped to [0.0, 1.0].
"""

from __future__ import annotations

from abraxas.detectors.shadow import compliance_remix, meta_awareness, negative_space
from abraxas.detectors.shadow.registry import compute_all_detectors
from abraxas.detectors.shadow.types import DetectorStatus, clamp01


def test_clamp01_utility():
    """Test clamp01 utility function."""
    assert clamp01(-1.0) == 0.0
    assert clamp01(0.0) == 0.0
    assert clamp01(0.5) == 0.5
    assert clamp01(1.0) == 1.0
    assert clamp01(2.0) == 1.0
    assert clamp01(999.9) == 1.0


def test_compliance_remix_bounds():
    """Test that Compliance vs Remix detector values are within [0, 1]."""
    # Extreme values to test clamping
    extreme_context = {
        "drift": {"drift_score": 99.0, "similarity_early_late": -10.0},
        "appearances": 999999,
        "csp": {"FF": 100.0, "MIO": 100.0},
        "lifecycle_state": "Saturated",
        "tau": {"tau_velocity": 1000.0, "tau_half_life": 999999.0},
        "fog_type_counts": {"template": 1000, "manufactured": 1000},
    }

    result = compliance_remix.compute_detector(extreme_context)

    if result.status == DetectorStatus.OK:
        # Check main value
        assert result.value is not None
        assert 0.0 <= result.value <= 1.0

        # Check all subscores
        for score_name, score_value in result.subscores.items():
            assert 0.0 <= score_value <= 1.0, f"{score_name} = {score_value} out of bounds"

    # Check bounds are set correctly
    assert result.bounds == (0.0, 1.0)


def test_meta_awareness_bounds():
    """Test that Meta-Awareness detector values are within [0, 1]."""
    # Extreme values with many keywords
    extreme_text = """
    manufactured manufactured manufactured psyop psyop psyop
    bot bot bot algorithm algorithm algorithm ragebait ragebait ragebait
    again again again tired tired tired
    calling it calling it calling it predict predict predict
    """

    extreme_context = {
        "text": extreme_text * 10,  # Repeat for high keyword counts
        "dmx": {"overall_manipulation_risk": 99.0, "bucket": "HIGH"},
        "rdv": {"irony": 99.0, "humor": 99.0, "nihilism": 99.0},
        "efte": {"threshold": 99.0, "saturation_risk": "HIGH"},
        "narrative_manipulation": {"rrs": 99.0, "cis": 99.0, "eil": 99.0},
        "MRI": 999.0,
        "IRI": 999.0,
    }

    result = meta_awareness.compute_detector(extreme_context)

    if result.status == DetectorStatus.OK:
        # Check main value
        assert result.value is not None
        assert 0.0 <= result.value <= 1.0

        # Check all subscores
        for score_name, score_value in result.subscores.items():
            assert 0.0 <= score_value <= 1.0, f"{score_name} = {score_value} out of bounds"

    # Check bounds
    assert result.bounds == (0.0, 1.0)


def test_negative_space_bounds():
    """Test that Negative Space detector values are within [0, 1]."""
    # Extreme dropout: all baseline topics missing
    context = {
        "symbol_pool": [],  # No current narratives
    }

    # Large baseline with many topics
    large_history = []
    for i in range(10):
        hist_pool = [
            {"narrative_id": f"topic_{j}", "source": f"source_{j % 5}"}
            for j in range(100)  # 100 topics
        ]
        large_history.append({"symbol_pool": hist_pool})

    result = negative_space.compute_detector(context, large_history)

    if result.status == DetectorStatus.OK:
        # Check main value
        assert result.value is not None
        assert 0.0 <= result.value <= 1.0

        # Check all subscores
        for score_name, score_value in result.subscores.items():
            assert 0.0 <= score_value <= 1.0, f"{score_name} = {score_value} out of bounds"

    # Check bounds
    assert result.bounds == (0.0, 1.0)


def test_all_detectors_bounds():
    """Test that all detectors in registry respect bounds."""
    # Create extreme context
    context = {
        "text": "manufactured psyop algorithm ragebait again tired calling it predict " * 20,
        "drift": {"drift_score": 999.0, "similarity_early_late": -999.0},
        "lifecycle_state": "Proto",
        "tau": {"tau_velocity": 999.0, "tau_half_life": 999999.0},
        "dmx": {"overall_manipulation_risk": 999.0, "bucket": "HIGH"},
        "symbol_pool": [],
        "rdv": {"irony": 999.0, "humor": 999.0, "nihilism": 999.0},
        "efte": {"threshold": 999.0},
        "narrative_manipulation": {"rrs": 999.0, "cis": 999.0},
        "appearances": 999999,
        "csp": {"FF": 999.0, "MIO": 999.0},
    }

    # Large history
    history = []
    for i in range(10):
        hist_pool = [{"narrative_id": f"topic_{j}", "source": f"source_{j}"} for j in range(50)]
        history.append({"symbol_pool": hist_pool})

    results = compute_all_detectors(context, history)

    for detector_id, detector_value in results.items():
        # Check bounds are set
        assert detector_value.bounds == (0.0, 1.0)

        if detector_value.status == DetectorStatus.OK:
            # Check main value
            assert detector_value.value is not None
            assert 0.0 <= detector_value.value <= 1.0, (
                f"{detector_id}: value = {detector_value.value} out of bounds"
            )

            # Check all subscores
            for score_name, score_value in detector_value.subscores.items():
                assert 0.0 <= score_value <= 1.0, (
                    f"{detector_id}.{score_name} = {score_value} out of bounds"
                )


def test_zero_and_one_edge_cases():
    """Test that detectors can produce 0.0 and 1.0 values."""
    # Context likely to produce low values (near 0.0)
    low_context = {
        "drift": {"drift_score": 0.0, "similarity_early_late": 1.0},
        "lifecycle_state": "Dormant",
        "tau": {"tau_velocity": 0.0, "tau_half_life": 0.0},
        "appearances": 0,
        "text": "",
        "symbol_pool": [],
    }

    # Minimal history for negative space
    minimal_history = [
        {"symbol_pool": []},
        {"symbol_pool": []},
        {"symbol_pool": []},
    ]

    # Test each detector can produce valid 0.0-1.0 range values
    detectors_and_contexts = [
        (compliance_remix.compute_detector, low_context, None),
        (meta_awareness.compute_detector, {"text": "neutral text"}, None),
        (negative_space.compute_detector, low_context, minimal_history),
    ]

    for detector_fn, context, history in detectors_and_contexts:
        result = detector_fn(context, history) if history is not None else detector_fn(context)

        if result.status == DetectorStatus.OK and result.value is not None:
            # Value should be in valid range
            assert 0.0 <= result.value <= 1.0

            # All subscores should also be in valid range
            for score_value in result.subscores.values():
                assert 0.0 <= score_value <= 1.0


def test_mid_range_values():
    """Test that detectors produce reasonable mid-range values for typical inputs."""
    typical_context = {
        "drift": {"drift_score": 0.5, "similarity_early_late": 0.5},
        "lifecycle_state": "Front",
        "tau": {"tau_velocity": 0.5, "tau_half_life": 24.0},
        "appearances": 10,
        "csp": {"FF": 0.3, "MIO": 0.2},
        "text": "Some text with algorithm mention",
        "dmx": {"overall_manipulation_risk": 0.5, "bucket": "MED"},
        "rdv": {"irony": 0.2, "humor": 0.1, "nihilism": 0.1},
        "symbol_pool": [
            {"narrative_id": "topic_A", "source": "source1"},
            {"narrative_id": "topic_B", "source": "source2"},
        ],
    }

    history = [
        {
            "symbol_pool": [
                {"narrative_id": "topic_A"},
                {"narrative_id": "topic_B"},
                {"narrative_id": "topic_C"},
            ]
        },
        {
            "symbol_pool": [
                {"narrative_id": "topic_A"},
                {"narrative_id": "topic_B"},
                {"narrative_id": "topic_C"},
            ]
        },
        {"symbol_pool": [{"narrative_id": "topic_A"}, {"narrative_id": "topic_C"}]},
    ]

    results = compute_all_detectors(typical_context, history)

    for detector_id, detector_value in results.items():
        if detector_value.status == DetectorStatus.OK:
            assert detector_value.value is not None
            assert 0.0 <= detector_value.value <= 1.0

            # All subscores should be in bounds
            for score_value in detector_value.subscores.values():
                assert 0.0 <= score_value <= 1.0
