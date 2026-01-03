from __future__ import annotations

from abraxas.runes.operators.atlas_coupling_watchlist import (
    CouplingWatchlistParams,
    apply_atlas_coupling_watchlist,
)


def test_watchlist_not_computable_when_no_inputs():
    atlas = {"schema_version": "atlas.v0.x", "pressure_cells": [], "synchronicity_clusters": []}
    out = apply_atlas_coupling_watchlist(atlas, CouplingWatchlistParams())
    assert out["shadow_only"] is True
    assert out["not_computable"] is True
    assert out["edges_top"] == []
    assert out["clusters_top"] == []


def test_watchlist_deterministic_same_inputs_same_output():
    atlas = {
        "schema_version": "atlas.v0.x",
        "year": 2025,
        "window": "weekly",
        "pressure_cells": [
            {"window_utc": "w1", "intensity": 0.9, "motif_edges": ["V1--V2", "V1--V3"]},
            {"window_utc": "w2", "intensity": 0.7, "motif_edges": ["V1--V2"]},
            {"window_utc": "w2", "intensity": 0.6, "motif_edges": ["V1--V2"]},
        ],
        "synchronicity_clusters": [
            {
                "cluster_id": "c1",
                "time_window": "w1",
                "density_score": 0.8,
                "domains": ["culture_memes"],
                "vectors": ["V1", "V2"],
            }
        ],
    }
    params = CouplingWatchlistParams(top_k_edges=10, top_k_clusters=10, min_persistence=2)
    out_a = apply_atlas_coupling_watchlist(atlas, params)
    out_b = apply_atlas_coupling_watchlist(atlas, params)
    assert out_a == out_b


def test_watchlist_ranking_stable_tie_breaks():
    atlas = {
        "schema_version": "atlas.v0.x",
        "pressure_cells": [
            {"window_utc": "w1", "intensity": 0.5, "motif_edges": ["A--B", "A--C"]},
            {"window_utc": "w2", "intensity": 0.5, "motif_edges": ["A--B", "A--C"]},
        ],
        "synchronicity_clusters": [],
    }
    out = apply_atlas_coupling_watchlist(atlas, CouplingWatchlistParams(top_k_edges=10, min_persistence=2))
    edges = out["edges_top"]
    assert len(edges) == 2
    assert edges[0]["edge"] < edges[1]["edge"]
