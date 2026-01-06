"""Test forecast.term.classify capability contract.

Tests determinism, classification accuracy, and provenance.
"""

from __future__ import annotations

import pytest

from abraxas.forecast.rune_adapter import classify_term_deterministic


def test_classify_term_stable():
    """Test classification of stable terms."""
    profile = {
        "consensus_gap_term": 0.30,
        "half_life_days": 20.0,
        "manipulation_risk": 0.40,
        "momentum": "stable",
        "flags": []
    }
    result = classify_term_deterministic(profile, seed=123)

    assert result["term_class"] == "stable"
    assert result["provenance"] is not None
    assert result["provenance"]["operation_id"] == "forecast.term.classify"
    assert "inputs_sha256" in result["provenance"]
    assert result["not_computable"] is None


def test_classify_term_emerging():
    """Test classification of emerging terms."""
    profile = {
        "consensus_gap_term": 0.45,
        "half_life_days": 10.0,
        "manipulation_risk": 0.30,
        "momentum": "rising",
        "flags": []
    }
    result = classify_term_deterministic(profile, seed=123)

    assert result["term_class"] == "emerging"
    assert result["not_computable"] is None


def test_classify_term_contested():
    """Test classification of contested terms."""
    profile = {
        "consensus_gap_term": 0.70,
        "half_life_days": 15.0,
        "manipulation_risk": 0.50,
        "momentum": "stable",
        "flags": []
    }
    result = classify_term_deterministic(profile, seed=123)

    assert result["term_class"] == "contested"
    assert result["not_computable"] is None


def test_classify_term_volatile():
    """Test classification of volatile terms."""
    profile = {
        "consensus_gap_term": 0.40,
        "half_life_days": 5.0,
        "manipulation_risk": 0.60,
        "momentum": "spiking",
        "flags": []
    }
    result = classify_term_deterministic(profile, seed=123)

    assert result["term_class"] == "volatile"
    assert result["not_computable"] is None


def test_classify_term_unknown():
    """Test classification when consensus is missing."""
    profile = {
        "consensus_gap_term": 0.0,
        "half_life_days": 10.0,
        "manipulation_risk": 0.30,
        "momentum": "stable",
        "flags": ["CONSENSUS_MISSING"]
    }
    result = classify_term_deterministic(profile, seed=123)

    assert result["term_class"] == "unknown"
    assert result["not_computable"] is None


def test_classify_term_determinism():
    """Test that same profile produces same hash."""
    profile = {
        "consensus_gap_term": 0.35,
        "half_life_days": 18.0,
        "manipulation_risk": 0.45,
        "momentum": "stable",
        "flags": []
    }
    result1 = classify_term_deterministic(profile, seed=42)
    result2 = classify_term_deterministic(profile, seed=42)

    # Term class should be identical
    assert result1["term_class"] == result2["term_class"]

    # Provenance inputs_sha256 should be identical
    assert result1["provenance"]["inputs_sha256"] == result2["provenance"]["inputs_sha256"]


def test_classify_term_golden():
    """Golden test: Verify stable output for known profiles."""
    test_cases = [
        ({"consensus_gap_term": 0.30, "half_life_days": 20.0, "manipulation_risk": 0.40, "momentum": "stable", "flags": []}, "stable"),
        ({"consensus_gap_term": 0.45, "half_life_days": 10.0, "manipulation_risk": 0.30, "momentum": "rising", "flags": []}, "emerging"),
        ({"consensus_gap_term": 0.70, "half_life_days": 15.0, "manipulation_risk": 0.50, "momentum": "stable", "flags": []}, "contested"),
        ({"consensus_gap_term": 0.40, "half_life_days": 5.0, "manipulation_risk": 0.60, "momentum": "spiking", "flags": []}, "volatile"),
        ({"consensus_gap_term": 0.0, "half_life_days": 10.0, "manipulation_risk": 0.30, "momentum": "stable", "flags": ["CONSENSUS_MISSING"]}, "unknown"),
    ]

    for profile, expected_class in test_cases:
        result = classify_term_deterministic(profile, seed=123)
        assert result["term_class"] == expected_class
        assert result["provenance"]["operation_id"] == "forecast.term.classify"
        assert result["not_computable"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
