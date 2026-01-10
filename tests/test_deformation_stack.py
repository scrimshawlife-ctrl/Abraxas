from __future__ import annotations

from abraxas.runes.operators.deformation_stack import DeformationParams, apply_deformation_stack


def test_deformation_stack_deterministic():
    watchlist = {
        "schema_version": "coupling_watchlist.v0.1",
        "edges_top": [
            {"edge": "A--B", "persistence": 4, "mean_density": 0.4, "mean_intensity": 0.5, "score": 0.6},
            {"edge": "A--C", "persistence": 4, "mean_density": 0.4, "mean_intensity": 0.5, "score": 0.6},
        ],
        "clusters_top": [{"cluster_id": "c1", "density_score": 0.7}],
        "watchlist_hash": "x",
    }
    out_a = apply_deformation_stack(watchlist=watchlist, prev_watchlist=None, params=DeformationParams())
    out_b = apply_deformation_stack(watchlist=watchlist, prev_watchlist=None, params=DeformationParams())
    assert out_a == out_b


def test_deformation_stack_handles_missing_prev():
    watchlist = {"schema_version": "coupling_watchlist.v0.1", "edges_top": [], "clusters_top": [], "watchlist_hash": "x"}
    out = apply_deformation_stack(watchlist=watchlist, prev_watchlist=None, params=DeformationParams())
    assert out["alerts"]["not_computable"] is True
    assert out["alerts"]["edge_alerts"] == []


def test_alert_thresholds_respected():
    prev = {
        "schema_version": "coupling_watchlist.v0.1",
        "edges_top": [{"edge": "A--B", "persistence": 2, "score": 0.2}],
        "clusters_top": [],
        "watchlist_hash": "p",
    }
    cur = {
        "schema_version": "coupling_watchlist.v0.1",
        "edges_top": [{"edge": "A--B", "persistence": 3, "score": 0.31}],
        "clusters_top": [],
        "watchlist_hash": "c",
    }
    params = DeformationParams(alert_min_score_delta=0.10, alert_min_persistence_delta=1)
    out = apply_deformation_stack(watchlist=cur, prev_watchlist=prev, params=params)
    assert out["alerts"]["not_computable"] is False
    assert out["alerts"]["edge_alerts"][0]["edge"] == "A--B"
