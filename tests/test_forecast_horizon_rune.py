"""Test forecast.horizon.classify capability contract.

Tests determinism and classification accuracy.
"""

from __future__ import annotations

import pytest

from abraxas.forecast.rune_adapter import classify_horizon_deterministic


def test_classify_horizon_basic():
    """Test basic horizon classification."""
    # Test singular forms
    assert classify_horizon_deterministic("day")["horizon_bucket"] == "days"
    assert classify_horizon_deterministic("week")["horizon_bucket"] == "weeks"
    assert classify_horizon_deterministic("month")["horizon_bucket"] == "months"
    assert classify_horizon_deterministic("year")["horizon_bucket"] == "years"

    # Test plural forms
    assert classify_horizon_deterministic("days")["horizon_bucket"] == "days"
    assert classify_horizon_deterministic("weeks")["horizon_bucket"] == "weeks"
    assert classify_horizon_deterministic("months")["horizon_bucket"] == "months"
    assert classify_horizon_deterministic("years")["horizon_bucket"] == "years"


def test_classify_horizon_case_insensitive():
    """Test that classification is case-insensitive."""
    assert classify_horizon_deterministic("DAY")["horizon_bucket"] == "days"
    assert classify_horizon_deterministic("Week")["horizon_bucket"] == "weeks"
    assert classify_horizon_deterministic("MONTHS")["horizon_bucket"] == "months"


def test_classify_horizon_whitespace():
    """Test that whitespace is trimmed."""
    assert classify_horizon_deterministic("  day  ")["horizon_bucket"] == "days"
    assert classify_horizon_deterministic("\tweeks\n")["horizon_bucket"] == "weeks"


def test_classify_horizon_unknown():
    """Test that unknown values are classified as 'unknown'."""
    assert classify_horizon_deterministic("unknown")["horizon_bucket"] == "unknown"
    assert classify_horizon_deterministic("invalid")["horizon_bucket"] == "unknown"
    assert classify_horizon_deterministic(42)["horizon_bucket"] == "unknown"
    assert classify_horizon_deterministic(None)["horizon_bucket"] == "unknown"
    assert classify_horizon_deterministic("")["horizon_bucket"] == "unknown"


def test_classify_horizon_provenance():
    """Test that provenance is included."""
    result = classify_horizon_deterministic("days", seed=123)

    assert result["horizon_bucket"] == "days"
    assert result["provenance"] is not None
    assert result["provenance"]["operation_id"] == "forecast.horizon.classify"
    assert "inputs_hash" in result["provenance"]
    assert "timestamp" in result["provenance"]
    assert result["not_computable"] is None


def test_classify_horizon_determinism():
    """Test that same input produces same hash."""
    result1 = classify_horizon_deterministic("weeks", seed=42)
    result2 = classify_horizon_deterministic("weeks", seed=42)

    # Bucket should be identical
    assert result1["horizon_bucket"] == result2["horizon_bucket"]

    # Provenance inputs_hash should be identical
    assert result1["provenance"]["inputs_hash"] == result2["provenance"]["inputs_hash"]


def test_classify_horizon_golden():
    """Golden test: Verify stable output for known inputs."""
    test_cases = [
        ("day", "days"),
        ("week", "weeks"),
        ("month", "months"),
        ("year", "years"),
        ("invalid", "unknown"),
        (None, "unknown"),
        (123, "unknown"),
    ]

    for horizon_input, expected_bucket in test_cases:
        result = classify_horizon_deterministic(horizon_input, seed=123)
        assert result["horizon_bucket"] == expected_bucket
        assert result["provenance"]["operation_id"] == "forecast.horizon.classify"
        assert result["not_computable"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
