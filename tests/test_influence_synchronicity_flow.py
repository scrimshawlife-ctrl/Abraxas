"""Tests for influence/synchronicity shadow flow and guardrails."""

from __future__ import annotations

from abraxas.mda.run import run_mda
from abraxas.runes.operators.influence_detect import apply_influence_detect
from abraxas.runes.operators.synchronicity_map import apply_synchronicity_map


def _observation(domain: str, ts: str):
    return {
        "domain": domain,
        "timestamp_utc": ts,
        "vectors": {
            "V1_SIGNAL_DENSITY": 0.4,
            "V8_EMOTIONAL_CLIMATE": 0.6,
            "V13_ARCHETYPAL_ACTIVATION": 0.7,
        },
    }


def test_shadow_only_flow_does_not_mutate_prediction_state():
    env = {
        "observations": [
            _observation("astrology", "2025-01-01T00:00:00Z"),
            _observation("physics", "2025-01-02T00:00:00Z"),
        ],
        "git_hash": "abc123",
    }

    _, out = run_mda(env, abraxas_version="1.5.0")

    assert out["domain_aggregates"] == {}
    assert out["dsp"] == []
    assert out["fusion_graph"] == {}
    assert "shadow" in out
    assert "influence_v0_1" in out["shadow"]
    assert "synchronicity_v0_1" in out["shadow"]


def test_no_domain_prior_equivalence():
    frames = [
        _observation("astrology", "2025-01-01T00:00:00Z"),
        _observation("economics", "2025-01-01T00:00:00Z"),
    ]
    ics = apply_influence_detect(frames)
    metrics_a = ics["ics"]["astrology"]
    metrics_b = ics["ics"]["economics"]
    assert metrics_a == metrics_b


def test_not_computable_outputs():
    ics = apply_influence_detect([])
    assert ics["ics"]["_global"]["not_computable"], "ICS must mark not_computable when inputs missing"

    synch = apply_synchronicity_map([])
    assert synch["envelopes"] == []
    assert synch["not_computable"] is True
