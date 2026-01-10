"""Emit deterministic audio control sequences from atlas packs."""

from __future__ import annotations

from typing import Any, Dict, List

from abraxas.sonification.mapping import build_audio_frames
from abraxas.sonification.schema import AudioControlFrame


def emit_audio_controls(atlas_pack: Dict[str, Any]) -> List[AudioControlFrame]:
    return build_audio_frames(atlas_pack)
