"""Test forecast.term_class_map.load capability contract.

Tests determinism, map loading, and provenance.
"""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from abraxas.forecast.rune_adapter import load_term_class_map_deterministic


def test_load_term_class_map_basic():
    """Test basic term class map loading."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        a2_data = {
            'raw_full': {
                'profiles': [
                    {'term': 'bitcoin', 'consensus_gap_term': 0.30, 'half_life_days': 20.0, 'manipulation_risk': 0.40, 'momentum': 'stable', 'flags': []},
                    {'term': 'ethereum', 'consensus_gap_term': 0.45, 'half_life_days': 10.0, 'manipulation_risk': 0.30, 'momentum': 'rising', 'flags': []},
                ]
            }
        }
        json.dump(a2_data, f)
        temp_path = f.name

    try:
        result = load_term_class_map_deterministic(temp_path, seed=123)

        assert result["term_class_map"] is not None
        assert len(result["term_class_map"]) == 2
        assert result["term_class_map"]["bitcoin"] == "stable"
        assert result["term_class_map"]["ethereum"] == "emerging"
        assert result["provenance"] is not None
        assert result["provenance"]["operation_id"] == "forecast.term_class_map.load"
        assert "inputs_sha256" in result["provenance"]
        assert result["not_computable"] is None
    finally:
        os.unlink(temp_path)


def test_load_term_class_map_empty_path():
    """Test that empty/invalid path returns empty map."""
    result = load_term_class_map_deterministic("", seed=123)

    assert result["term_class_map"] == {}
    assert result["not_computable"] is None


def test_load_term_class_map_nonexistent():
    """Test that nonexistent file returns empty map."""
    result = load_term_class_map_deterministic("/nonexistent/path.json", seed=123)

    assert result["term_class_map"] == {}
    assert result["not_computable"] is None


def test_load_term_class_map_views():
    """Test loading from views when raw_full not available."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        a2_data = {
            'views': {
                'profiles_top': [
                    {'term': 'cardano', 'consensus_gap_term': 0.70, 'half_life_days': 15.0, 'manipulation_risk': 0.50, 'momentum': 'stable', 'flags': []},
                ]
            }
        }
        json.dump(a2_data, f)
        temp_path = f.name

    try:
        result = load_term_class_map_deterministic(temp_path, seed=123)

        assert len(result["term_class_map"]) == 1
        assert result["term_class_map"]["cardano"] == "contested"
        assert result["not_computable"] is None
    finally:
        os.unlink(temp_path)


def test_load_term_class_map_determinism():
    """Test that same path produces same hash."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        a2_data = {
            'raw_full': {
                'profiles': [
                    {'term': 'dogecoin', 'consensus_gap_term': 0.40, 'half_life_days': 5.0, 'manipulation_risk': 0.60, 'momentum': 'spiking', 'flags': []},
                ]
            }
        }
        json.dump(a2_data, f)
        temp_path = f.name

    try:
        result1 = load_term_class_map_deterministic(temp_path, seed=42)
        result2 = load_term_class_map_deterministic(temp_path, seed=42)

        # Map should be identical
        assert result1["term_class_map"] == result2["term_class_map"]

        # Provenance inputs_sha256 should be identical
        assert result1["provenance"]["inputs_sha256"] == result2["provenance"]["inputs_sha256"]
    finally:
        os.unlink(temp_path)


def test_load_term_class_map_lowercases_terms():
    """Test that term keys are lowercased."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        a2_data = {
            'raw_full': {
                'profiles': [
                    {'term': 'BitCoin', 'consensus_gap_term': 0.30, 'half_life_days': 20.0, 'manipulation_risk': 0.40, 'momentum': 'stable', 'flags': []},
                ]
            }
        }
        json.dump(a2_data, f)
        temp_path = f.name

    try:
        result = load_term_class_map_deterministic(temp_path, seed=123)

        # Should be lowercased
        assert "bitcoin" in result["term_class_map"]
        assert "BitCoin" not in result["term_class_map"]
        assert result["term_class_map"]["bitcoin"] == "stable"
    finally:
        os.unlink(temp_path)


def test_load_term_class_map_golden():
    """Golden test: Verify stable output for known data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        a2_data = {
            'raw_full': {
                'profiles': [
                    {'term': 'stable_term', 'consensus_gap_term': 0.30, 'half_life_days': 20.0, 'manipulation_risk': 0.40, 'momentum': 'stable', 'flags': []},
                    {'term': 'emerging_term', 'consensus_gap_term': 0.45, 'half_life_days': 10.0, 'manipulation_risk': 0.30, 'momentum': 'rising', 'flags': []},
                    {'term': 'volatile_term', 'consensus_gap_term': 0.40, 'half_life_days': 5.0, 'manipulation_risk': 0.60, 'momentum': 'spiking', 'flags': []},
                ]
            }
        }
        json.dump(a2_data, f)
        temp_path = f.name

    try:
        result = load_term_class_map_deterministic(temp_path, seed=123)

        assert result["term_class_map"]["stable_term"] == "stable"
        assert result["term_class_map"]["emerging_term"] == "emerging"
        assert result["term_class_map"]["volatile_term"] == "volatile"
        assert result["provenance"]["operation_id"] == "forecast.term_class_map.load"
        assert result["not_computable"] is None
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
