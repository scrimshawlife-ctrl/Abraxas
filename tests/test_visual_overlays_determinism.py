from __future__ import annotations

from abraxas.visuals.emit import emit_visual_controls


def test_visual_overlays_deterministic():
    atlas = {
        "pressure_cells": [
            {"window_utc": "w1", "vector": "A", "intensity": 0.8, "motif_edges": ["A--B"]},
            {"window_utc": "w1", "vector": "B", "intensity": 0.8, "motif_edges": ["A--B"]},
            {"window_utc": "w2", "vector": "A", "intensity": 0.4, "motif_edges": ["A--B"]},
            {"window_utc": "w2", "vector": "B", "intensity": 0.4, "motif_edges": ["A--B"]},
        ],
        "jetstreams": [],
        "cyclones": [],
        "calm_zones": [],
    }
    bridge_set = {"bridge_edges": [{"edge": "A--B"}]}
    alerts = {"edge_alerts": [{"edge": "A--B"}]}

    frames_a = [frame.model_dump() for frame in emit_visual_controls(atlas, bridge_set=bridge_set, alerts=alerts)]
    frames_b = [frame.model_dump() for frame in emit_visual_controls(atlas, bridge_set=bridge_set, alerts=alerts)]
    assert frames_a == frames_b
    w1 = [frame for frame in frames_a if frame["window_utc"] == "w1"][0]
    assert w1["provenance"]["overlay_present"] is True


def test_visual_no_overlays_does_not_break():
    atlas = {"pressure_cells": [], "jetstreams": [], "cyclones": [], "calm_zones": []}
    frames = [frame.model_dump() for frame in emit_visual_controls(atlas)]
    assert isinstance(frames, list)
