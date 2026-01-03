from __future__ import annotations

from abraxas.runes.operators.atlas_synch_cluster import (
    AtlasSynchClusterParams,
    apply_atlas_synch_cluster,
)


def test_clustered_bundle_has_stage_and_shadow_only():
    atlas = {
        "year": 2025,
        "window": "weekly",
        "jetstreams": [{"source_motif": "m1", "target_motif": "m2", "strength": 0.9}],
    }
    out = apply_atlas_synch_cluster(atlas, AtlasSynchClusterParams(seed=1, min_strength=0.1, top_k=10))
    assert out["shadow_only"] is True
    assert out["stage"] == "clustered"
    assert "clusters" in out


def test_clustered_determinism_same_inputs_same_output():
    atlas = {
        "year": 2025,
        "window": "weekly",
        "jetstreams": [{"source_motif": "m1", "target_motif": "m2", "strength": 0.9}],
    }
    params = AtlasSynchClusterParams(seed=1, min_strength=0.1, top_k=10)
    a = apply_atlas_synch_cluster(atlas, params)
    b = apply_atlas_synch_cluster(atlas, params)
    assert a == b


def test_clustered_not_computable_when_no_topology():
    atlas = {"year": 2025, "window": "weekly", "jetstreams": [], "pressure_cells": []}
    out = apply_atlas_synch_cluster(atlas, AtlasSynchClusterParams())
    assert out["not_computable"] is True
    assert out["clusters"] == []
