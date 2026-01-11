from __future__ import annotations

from abraxas.visuals.events import emit_overlay_events


def test_overlay_events_deterministic():
    bridge = {
        "bridge_edges": [
            {"edge": "A--B", "score": 0.6, "persistence": 3, "mean_density": 0.4, "mean_intensity": 0.5}
        ],
        "bridge_set_hash": "b",
    }
    alerts = {
        "edge_alerts": [{"edge": "A--B", "type": "delta", "score_delta": 0.2, "persistence_delta": 1}],
        "cluster_alerts": [],
        "alerts_hash": "a",
    }
    atlas = {"synchronicity_clusters": [{"cluster_id": "c1", "time_window": "w1"}], "atlas_hash": "h"}
    out_a = emit_overlay_events(bridge_set=bridge, alerts=alerts, atlas_pack=atlas)
    out_b = emit_overlay_events(bridge_set=bridge, alerts=alerts, atlas_pack=atlas)
    assert out_a == out_b
    assert out_a["schema_version"] == "overlay_events.v0.1"
    assert isinstance(out_a["events"], list)


def test_overlay_events_empty_not_computable():
    out = emit_overlay_events(bridge_set=None, alerts=None, atlas_pack=None)
    assert out["not_computable"] is True
    assert out["events"] == []
