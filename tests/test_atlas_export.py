"""Tests for deterministic atlas export."""

from __future__ import annotations

import json

import pytest

from abraxas.atlas.construct import build_atlas_pack, load_seedpack
from abraxas.schema.tvm import TVM_VECTOR_IDS


def _sample_seedpack() -> dict:
    windows = [
        ("2025-01-01T00:00:00Z", "2025-01-08T00:00:00Z"),
        ("2025-01-08T00:00:00Z", "2025-01-15T00:00:00Z"),
        ("2025-01-15T00:00:00Z", "2025-01-22T00:00:00Z"),
        ("2025-01-22T00:00:00Z", "2025-01-29T00:00:00Z"),
    ]
    base_values = [
        {"V1_SIGNAL_DENSITY": 0.1, "V2_SIGNAL_INTEGRITY": 0.2, "V3_DISTRIBUTION_DYNAMICS": 0.3},
        {"V1_SIGNAL_DENSITY": 0.2, "V2_SIGNAL_INTEGRITY": 0.1, "V3_DISTRIBUTION_DYNAMICS": 0.4},
        {"V1_SIGNAL_DENSITY": 0.05, "V2_SIGNAL_INTEGRITY": 0.25, "V3_DISTRIBUTION_DYNAMICS": 0.2},
        {"V1_SIGNAL_DENSITY": 0.15, "V2_SIGNAL_INTEGRITY": 0.18, "V3_DISTRIBUTION_DYNAMICS": 0.35},
    ]
    frames = []
    for idx, (start, end) in enumerate(windows):
        base = base_values[idx]
        frames.append(
            {
                "window_start_utc": start,
                "window_end_utc": end,
                "domain": "linguistics",
                "vectors": {key: {"score": val} for key, val in base.items()},
                "provenance": {"frame_hash": f"frame_ling_{idx}"},
            }
        )
        frames.append(
            {
                "window_start_utc": start,
                "window_end_utc": end,
                "domain": "meteorology",
                "vectors": {key: {"score": val + 0.01} for key, val in base.items()},
                "provenance": {"frame_hash": f"frame_met_{idx}"},
            }
        )

    influence = {
        "ics": {
            "linguistics": {"CDEC": 0.0, "not_computable": []},
            "meteorology": {"CDEC": 0.0, "not_computable": []},
        },
        "provenance": {"inputs_hash": "influence_hash"},
    }
    synchronicity = {
        "shadow_only": True,
        "envelopes": [
            {
                "domains_involved": ("linguistics", "meteorology"),
                "vectors_activated": ["V1_SIGNAL_DENSITY"],
                "metrics": {"TCI": 0.4, "SIS": 0.5, "CPA": 0.3, "RAC": 0.6, "PUR": 0.2},
                "time_window": "86400s",
                "rarity_estimate": 0.2,
                "persistence_score": 0.8,
                "provenance": {"inputs_hash": "sync_hash"},
            }
        ],
        "provenance": {"inputs_hash": "sync_bundle_hash"},
    }
    return {"schema_version": "seedpack.v0.2", "year": 2025, "frames": frames, "influence": influence, "synchronicity": synchronicity}


def test_atlas_hash_deterministic():
    seedpack = _sample_seedpack()
    hashes = {build_atlas_pack(seedpack, window_granularity="weekly").provenance["atlas_hash"] for _ in range(12)}
    assert len(hashes) == 1


def test_atlas_rebuild_from_seedpack(tmp_path):
    seedpack = _sample_seedpack()
    path = tmp_path / "seedpack.json"
    path.write_text(json.dumps(seedpack, indent=2, sort_keys=True), encoding="utf-8")
    loaded = load_seedpack(path)
    pack_a = build_atlas_pack(seedpack, window_granularity="weekly")
    pack_b = build_atlas_pack(loaded, window_granularity="weekly")
    assert pack_a.provenance["atlas_hash"] == pack_b.provenance["atlas_hash"]


def test_atlas_no_analysis_invocations(monkeypatch):
    import abraxas.runes.invoke as invoke

    def _boom(*_args, **_kwargs):
        raise AssertionError("Analysis invocation triggered during atlas export")

    monkeypatch.setattr(invoke, "invoke_capability", _boom)
    seedpack = _sample_seedpack()
    build_atlas_pack(seedpack, window_granularity="weekly")


def test_atlas_no_causal_strings():
    seedpack = _sample_seedpack()
    pack = build_atlas_pack(seedpack, window_granularity="weekly")
    payload = json.dumps(pack.model_dump()).lower()
    forbidden = ["predict", "prediction", "cause", "because", "interpret", "inference"]
    assert not any(term in payload for term in forbidden)


def test_atlas_window_removal_localized():
    seedpack = _sample_seedpack()
    pack_full = build_atlas_pack(seedpack, window_granularity="weekly")
    reduced_frames = [frame for frame in seedpack["frames"] if frame["window_start_utc"] != "2025-01-08T00:00:00Z"]
    reduced_seedpack = {**seedpack, "frames": reduced_frames}
    pack_reduced = build_atlas_pack(reduced_seedpack, window_granularity="weekly")

    assert pack_full.frames_count - pack_reduced.frames_count == 2
    assert len(pack_full.pressure_cells) - len(pack_reduced.pressure_cells) == len(TVM_VECTOR_IDS)
    assert pack_full.jetstreams == pack_reduced.jetstreams == []
    assert pack_full.calm_zones == pack_reduced.calm_zones == []
    assert pack_full.cyclones == pack_reduced.cyclones == []
