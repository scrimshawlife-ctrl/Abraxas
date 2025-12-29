"""Tests for Shadow Structural Metrics determinism.

Verifies that all metrics produce identical results for identical inputs.
"""

import pytest

# Import via rune operator (proper access path)
from abraxas.runes.operators.sso import apply_sso


def test_sei_determinism():
    """Verify SEI produces identical results for same inputs."""
    context = {
        "symbol_pool": [
            {"sentiment": "positive"},
            {"sentiment": "positive"},
            {"sentiment": "negative"},
            {"sentiment": "neutral"},
            {"sentiment": "neutral"},
        ],
        "time_window_hours": 24,
        "metrics_requested": ["SEI"],
    }

    result1 = apply_sso(context)
    result2 = apply_sso(context)

    # Values should be identical
    sei1 = result1["ssm_bundle"]["metrics"]["SEI"]["value"]
    sei2 = result2["ssm_bundle"]["metrics"]["SEI"]["value"]

    assert sei1 == sei2

    # Provenance inputs should hash to same value
    prov1 = result1["ssm_bundle"]["metrics"]["SEI"]["provenance"]
    prov2 = result2["ssm_bundle"]["metrics"]["SEI"]["provenance"]

    # Inputs hash should be same (deterministic input extraction)
    assert prov1["inputs_hash"] == prov2["inputs_hash"]


def test_clip_determinism():
    """Verify CLIP produces identical results for same inputs."""
    context = {
        "symbol_pool": [
            {"text": "This is a simple test sentence."},
            {"text": "Another sentence with complexity."},
        ],
        "metrics_requested": ["CLIP"],
    }

    result1 = apply_sso(context)
    result2 = apply_sso(context)

    clip1 = result1["ssm_bundle"]["metrics"]["CLIP"]["value"]
    clip2 = result2["ssm_bundle"]["metrics"]["CLIP"]["value"]

    assert clip1 == clip2


def test_nor_determinism():
    """Verify NOR produces identical results for same inputs."""
    context = {
        "symbol_pool": [
            {"narrative_id": "narrative_A"},
            {"narrative_id": "narrative_B"},
            {"narrative_id": "narrative_A"},
            {"narrative_id": "narrative_C"},
        ],
        "metrics_requested": ["NOR"],
    }

    result1 = apply_sso(context)
    result2 = apply_sso(context)

    nor1 = result1["ssm_bundle"]["metrics"]["NOR"]["value"]
    nor2 = result2["ssm_bundle"]["metrics"]["NOR"]["value"]

    assert nor1 == nor2


def test_all_metrics_determinism():
    """Verify all six metrics produce deterministic results."""
    context = {
        "symbol_pool": [
            {
                "sentiment": "positive",
                "text": "Test content",
                "narrative_id": "N1",
                "opinion_score": 0.5,
                "exposed_count": 100,
                "transmission_count": 30,
                "source": "source_A",
            }
        ],
        "time_window_hours": 48,
    }

    result1 = apply_sso(context)
    result2 = apply_sso(context)

    for metric_id in ["SEI", "CLIP", "NOR", "PTS", "SCG", "FVC"]:
        val1 = result1["ssm_bundle"]["metrics"][metric_id]["value"]
        val2 = result2["ssm_bundle"]["metrics"][metric_id]["value"]

        assert val1 == val2, f"Metric {metric_id} is not deterministic"
