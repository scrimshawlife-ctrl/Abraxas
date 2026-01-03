"""Emit deterministic visual control sequences from atlas packs."""

from __future__ import annotations

from typing import Any, Dict, List

from abraxas.visuals.mapping import build_visual_frames
from abraxas.visuals.schema import VisualControlFrame


def emit_visual_controls(atlas_pack: Dict[str, Any]) -> List[VisualControlFrame]:
    return build_visual_frames(atlas_pack)
