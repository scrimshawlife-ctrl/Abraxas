"""Tests for individual Shadow Structural Metrics correctness.

Verifies that each metric computes expected values for known inputs.
"""

import math

import pytest

from abraxas.runes.operators.sso import apply_sso


def test_sei_balanced_distribution():
    """Verify SEI ≈ 1.0 for perfectly balanced sentiment."""
    # Perfectly balanced: 1/3 each sentiment
    context = {
        "symbol_pool": [
            {"sentiment": "positive"},
            {"sentiment": "positive"},
            {"sentiment": "positive"},
            {"sentiment": "negative"},
            {"sentiment": "negative"},
            {"sentiment": "negative"},
            {"sentiment": "neutral"},
            {"sentiment": "neutral"},
            {"sentiment": "neutral"},
        ],
        "metrics_requested": ["SEI"],
    }

    result = apply_sso(context)
    sei = result["ssm_bundle"]["metrics"]["SEI"]["value"]

    # Should be very close to 1.0 (max entropy)
    assert sei > 0.95


def test_sei_homogeneous_distribution():
    """Verify SEI ≈ 0.0 for homogeneous sentiment."""
    # All positive
    context = {
        "symbol_pool": [{"sentiment": "positive"} for _ in range(10)],
        "metrics_requested": ["SEI"],
    }

    result = apply_sso(context)
    sei = result["ssm_bundle"]["metrics"]["SEI"]["value"]

    # Should be very close to 0.0 (min entropy)
    assert sei < 0.05


def test_clip_empty_text():
    """Verify CLIP = 0.0 for empty text."""
    context = {"symbol_pool": [{"text": ""}], "metrics_requested": ["CLIP"]}

    result = apply_sso(context)
    clip = result["ssm_bundle"]["metrics"]["CLIP"]["value"]

    assert clip == 0.0


def test_nor_zero_narratives():
    """Verify NOR ≈ 0.0 for zero or one narrative."""
    context = {"symbol_pool": [{"narrative_id": "N1"}], "metrics_requested": ["NOR"]}

    result = apply_sso(context)
    nor = result["ssm_bundle"]["metrics"]["NOR"]["value"]

    # Should be low (minimal overload)
    assert nor < 0.3


def test_nor_many_narratives():
    """Verify NOR increases with narrative count."""
    # Many unique narratives
    context = {
        "symbol_pool": [{"narrative_id": f"N{i}"} for i in range(20)],
        "metrics_requested": ["NOR"],
    }

    result = apply_sso(context)
    nor = result["ssm_bundle"]["metrics"]["NOR"]["value"]

    # Should be high (saturation)
    assert nor > 0.8


def test_pts_zero_change():
    """Verify PTS ≈ 0.5 for zero opinion change."""
    context = {
        "symbol_pool": [{"opinion_score": 0.5}, {"opinion_score": 0.5}],
        "metrics_requested": ["PTS"],
    }

    result = apply_sso(context)
    pts = result["ssm_bundle"]["metrics"]["PTS"]["value"]

    # Sigmoid(0) = 0.5
    assert 0.45 < pts < 0.55


def test_scg_critical_threshold():
    """Verify SCG ≈ 0.0 when R ≈ 1 (critical)."""
    context = {
        "symbol_pool": [{"exposed_count": 100, "transmission_count": 100}],
        "metrics_requested": ["SCG"],
    }

    result = apply_sso(context)
    scg = result["ssm_bundle"]["metrics"]["SCG"]["value"]

    # R = 1 → SCG ≈ 0
    assert scg < 0.15


def test_scg_super_critical():
    """Verify SCG > 0.5 when R > 1 (viral)."""
    context = {
        "symbol_pool": [{"exposed_count": 100, "transmission_count": 500}],
        "metrics_requested": ["SCG"],
    }

    result = apply_sso(context)
    scg = result["ssm_bundle"]["metrics"]["SCG"]["value"]

    # R = 5 → SCG should be high
    assert scg > 0.4


def test_fvc_single_source():
    """Verify FVC ≈ 1.0 for single source (max filtering)."""
    context = {
        "symbol_pool": [{"source": "A"} for _ in range(10)],
        "metrics_requested": ["FVC"],
    }

    result = apply_sso(context)
    fvc = result["ssm_bundle"]["metrics"]["FVC"]["value"]

    # All from one source → max filtering
    assert fvc > 0.95


def test_fvc_diverse_sources():
    """Verify FVC decreases with source diversity."""
    # 10 different sources
    context = {
        "symbol_pool": [{"source": f"source_{i}"} for i in range(10)],
        "metrics_requested": ["FVC"],
    }

    result = apply_sso(context)
    fvc = result["ssm_bundle"]["metrics"]["FVC"]["value"]

    # Many sources → low filtering
    assert fvc < 0.2


def test_all_metrics_bounded():
    """Verify all metrics are bounded to [0, 1]."""
    context = {
        "symbol_pool": [
            {
                "sentiment": "positive",
                "text": "Test content with various properties",
                "narrative_id": "N1",
                "opinion_score": 0.8,
                "exposed_count": 50,
                "transmission_count": 100,
                "source": "test_source",
            }
        ]
    }

    result = apply_sso(context)

    for metric_id in ["SEI", "CLIP", "NOR", "PTS", "SCG", "FVC"]:
        value = result["ssm_bundle"]["metrics"][metric_id]["value"]

        assert 0.0 <= value <= 1.0, f"Metric {metric_id} out of bounds: {value}"
