"""Emit deterministic visual control sequences from atlas packs."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from abraxas.visuals.mapping import build_visual_frames
from abraxas.visuals.overlays import build_overlay_signals
from abraxas.visuals.events import emit_overlay_events
from abraxas.visuals.schema import VisualControlFrame


def emit_visual_controls(
    atlas_pack: Dict[str, Any],
    *,
    bridge_set: Optional[Dict[str, Any]] = None,
    alerts: Optional[Dict[str, Any]] = None,
) -> List[VisualControlFrame]:
    overlay_signals = build_overlay_signals(atlas_pack=atlas_pack, bridge_set=bridge_set, alerts=alerts)
    return build_visual_frames(atlas_pack, overlay_signals=overlay_signals)


def emit_visual_controls_and_events(
    atlas_pack: Dict[str, Any],
    *,
    bridge_set: Optional[Dict[str, Any]] = None,
    alerts: Optional[Dict[str, Any]] = None,
) -> Tuple[List[VisualControlFrame], Dict[str, Any]]:
    frames = emit_visual_controls(atlas_pack, bridge_set=bridge_set, alerts=alerts)
    events = emit_overlay_events(bridge_set=bridge_set, alerts=alerts, atlas_pack=atlas_pack)
    return frames, events
