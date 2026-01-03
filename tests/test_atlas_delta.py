"""Tests for deterministic delta atlas generation."""

from __future__ import annotations

import json

import pytest

from abraxas.atlas.compare import build_delta_pack


def _base_atlas() -> dict:
    window_a = "2024-01-01T00:00:00Z/2024-01-08T00:00:00Z"
    return {
        "atlas_version": "atlas.v1.0",
        "year": 2024,
        "window_granularity": "weekly",
        "frames_count": 2,
        "pressure_cells": [
            {"cell_id": "V1:" + window_a, "vector": "V1_SIGNAL_DENSITY", "window_utc": window_a, "intensity": 0.2, "gradient": 0.1, "provenance_refs": ["p1"]},
        ],
        "jetstreams": [
            {"jet_id": "V1_SIGNAL_DENSITY", "vectors_involved": ["V1_SIGNAL_DENSITY"], "directionality": [window_a], "strength": 0.1, "persistence": 1, "provenance_refs": ["j1"]},
        ],
        "cyclones": [
            {"cyclone_id": window_a + ":V1", "window_utc": window_a, "center_vectors": ["V1_SIGNAL_DENSITY"], "domain_overlap": 1.0, "rotation_direction": "cw", "coherence_score": 0.2, "rarity_score": 0.3, "provenance_refs": ["c1"]},
        ],
        "calm_zones": [
            {"zone_id": "V1_SIGNAL_DENSITY", "vectors_suppressed": ["V1_SIGNAL_DENSITY"], "duration_windows": [window_a], "stability_score": 2.0, "provenance_refs": ["z1"]},
        ],
        "synchronicity_clusters": [
            {"cluster_id": "cluster", "domains": ["a"], "vectors": ["V1_SIGNAL_DENSITY"], "time_window": "86400s", "density_score": 0.4, "provenance_refs": ["s1"]},
        ],
        "provenance": {"atlas_hash": "base_hash"},
    }


def _compare_atlas() -> dict:
    base = _base_atlas()
    base["year"] = 2025
    base["pressure_cells"][0]["intensity"] = 0.5
    base["pressure_cells"][0]["gradient"] = 0.2
    base["jetstreams"][0]["strength"] = 0.2
    base["jetstreams"][0]["persistence"] = 2
    base["cyclones"][0]["coherence_score"] = 0.4
    base["cyclones"][0]["rarity_score"] = 0.1
    base["calm_zones"][0]["stability_score"] = 4.0
    base["calm_zones"][0]["duration_windows"] = [
        "2024-01-01T00:00:00Z/2024-01-08T00:00:00Z",
        "2024-01-08T00:00:00Z/2024-01-15T00:00:00Z",
    ]
    base["synchronicity_clusters"][0]["density_score"] = 0.6
    base["provenance"]["atlas_hash"] = "compare_hash"
    return base


def test_delta_deterministic():
    base = _base_atlas()
    compare = _compare_atlas()
    hashes = {
        build_delta_pack(base, compare, comparison_label="2024→2025").provenance["delta_hash"]
        for _ in range(12)
    }
    assert len(hashes) == 1


def test_delta_zero_on_self():
    base = _base_atlas()
    delta = build_delta_pack(base, base, comparison_label="self")
    for item in delta.delta_pressures:
        assert item["delta_intensity"] == 0.0
        assert item["delta_gradient"] == 0.0


def test_delta_appearance_disappearance():
    base = _base_atlas()
    compare = _compare_atlas()
    compare["cyclones"] = []
    delta = build_delta_pack(base, compare, comparison_label="drop")
    assert any(item["disappeared"] for item in delta.delta_cyclones)


def test_delta_remove_primitive_localized():
    base = _base_atlas()
    compare = _compare_atlas()
    compare["jetstreams"] = []
    delta = build_delta_pack(base, compare, comparison_label="jetless")
    assert any(item["delta_strength"] is None for item in delta.delta_jetstreams)
    assert delta.delta_pressures[0]["delta_intensity"] == 0.3


def test_no_analysis_invoked(monkeypatch):
    import abraxas.runes.invoke as invoke

    def _boom(*_args, **_kwargs):
        raise AssertionError("Analysis invocation triggered during delta computation")

    monkeypatch.setattr(invoke, "invoke_capability", _boom)
    build_delta_pack(_base_atlas(), _compare_atlas(), comparison_label="safe")
