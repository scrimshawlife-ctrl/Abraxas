"""Tests for deterministic visual control output."""

from __future__ import annotations

import json

from abraxas.visuals.emit import emit_visual_controls
from abraxas.visuals.mapping import VISUAL_CONSTANTS, build_visual_frames


def _sample_atlas_pack() -> dict:
    window_a = "2025-01-01T00:00:00Z/2025-01-08T00:00:00Z"
    window_b = "2025-01-08T00:00:00Z/2025-01-15T00:00:00Z"
    return {
        "atlas_version": "atlas.v1.0",
        "year": 2025,
        "window_granularity": "weekly",
        "frames_count": 4,
        "pressure_cells": [
            {"cell_id": "V1:" + window_a, "vector": "V1_SIGNAL_DENSITY", "window_utc": window_a, "intensity": 0.2, "gradient": None, "provenance_refs": []},
            {"cell_id": "V2:" + window_a, "vector": "V2_SIGNAL_INTEGRITY", "window_utc": window_a, "intensity": 0.4, "gradient": None, "provenance_refs": []},
            {"cell_id": "V1:" + window_b, "vector": "V1_SIGNAL_DENSITY", "window_utc": window_b, "intensity": 0.6, "gradient": 0.4, "provenance_refs": []},
            {"cell_id": "V2:" + window_b, "vector": "V2_SIGNAL_INTEGRITY", "window_utc": window_b, "intensity": 0.3, "gradient": -0.1, "provenance_refs": []},
        ],
        "jetstreams": [
            {
                "jet_id": "V1_SIGNAL_DENSITY:up:" + window_a + ":" + window_b,
                "vectors_involved": ["V1_SIGNAL_DENSITY"],
                "directionality": [window_a, window_b],
                "strength": 0.2,
                "persistence": 2,
                "provenance_refs": [],
            }
        ],
        "cyclones": [
            {
                "cyclone_id": window_a + ":V1_SIGNAL_DENSITY",
                "window_utc": window_a,
                "center_vectors": ["V1_SIGNAL_DENSITY", "V2_SIGNAL_INTEGRITY"],
                "domain_overlap": 1.0,
                "rotation_direction": "cw",
                "coherence_score": 0.5,
                "rarity_score": 0.4,
                "provenance_refs": [],
            }
        ],
        "calm_zones": [
            {
                "zone_id": "V2_SIGNAL_INTEGRITY:" + window_a + ":" + window_b,
                "vectors_suppressed": ["V2_SIGNAL_INTEGRITY"],
                "duration_windows": [window_a, window_b],
                "stability_score": 5.0,
                "provenance_refs": [],
            }
        ],
        "synchronicity_clusters": [
            {
                "cluster_id": "cluster1",
                "domains": ["linguistics", "meteorology"],
                "vectors": ["V1_SIGNAL_DENSITY"],
                "time_window": "86400s",
                "density_score": 0.5,
                "provenance_refs": [],
            }
        ],
        "provenance": {"atlas_hash": "atlas_hash"},
    }


def test_visual_controls_deterministic():
    atlas_pack = _sample_atlas_pack()
    first = [frame.model_dump() for frame in emit_visual_controls(atlas_pack)]
    second = [frame.model_dump() for frame in emit_visual_controls(atlas_pack)]
    assert first == second


def test_visual_controls_within_bounds():
    atlas_pack = _sample_atlas_pack()
    frames = build_visual_frames(atlas_pack)
    for frame in frames:
        assert VISUAL_CONSTANTS.hue_min <= frame.hue_range[0] <= frame.hue_range[1] <= VISUAL_CONSTANTS.hue_max
        assert VISUAL_CONSTANTS.saturation_min <= frame.saturation_level <= VISUAL_CONSTANTS.saturation_max
        assert VISUAL_CONSTANTS.luminance_min <= frame.luminance_level <= VISUAL_CONSTANTS.luminance_max
        assert 0.0 <= frame.motion_vector_strength <= 1.0
        assert 0.0 <= frame.distortion_intensity <= 1.0
        assert 0.0 <= frame.layering_depth <= 1.0
        assert 0.0 <= frame.noise_floor <= 1.0
        assert 0.0 <= frame.stillness_probability <= 1.0


def test_calm_zone_stillness_noise_monotonic():
    atlas_pack = _sample_atlas_pack()
    atlas_pack["calm_zones"][0]["stability_score"] = 2.0
    low_frame = emit_visual_controls(atlas_pack)[0]
    atlas_pack["calm_zones"][0]["stability_score"] = 8.0
    high_frame = emit_visual_controls(atlas_pack)[0]
    assert high_frame.stillness_probability > low_frame.stillness_probability
    assert high_frame.noise_floor <= low_frame.noise_floor


def test_cyclone_distortion_only():
    atlas_pack = _sample_atlas_pack()
    with_cyclone = [frame.model_dump() for frame in emit_visual_controls(atlas_pack)]
    atlas_pack["cyclones"] = []
    without_cyclone = [frame.model_dump() for frame in emit_visual_controls(atlas_pack)]

    assert with_cyclone[0]["distortion_intensity"] > without_cyclone[0]["distortion_intensity"]
    for key in ("hue_range", "saturation_level", "luminance_level", "motion_vector_strength", "noise_floor", "stillness_probability"):
        assert with_cyclone[0][key] == without_cyclone[0][key]


def test_no_analysis_invoked(monkeypatch):
    import abraxas.runes.invoke as invoke

    def _boom(*_args, **_kwargs):
        raise AssertionError("Analysis invocation triggered during visualization")

    monkeypatch.setattr(invoke, "invoke_capability", _boom)
    atlas_pack = _sample_atlas_pack()
    emit_visual_controls(atlas_pack)


def test_no_semantic_leakage():
    atlas_pack = _sample_atlas_pack()
    payload = json.dumps([frame.model_dump() for frame in emit_visual_controls(atlas_pack)]).lower()
    forbidden = ["emotion", "emotional", "mood", "narrative", "predict", "prediction", "cause", "because", "symbol"]
    assert not any(term in payload for term in forbidden)
