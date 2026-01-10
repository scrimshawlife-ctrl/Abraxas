"""Atlas-to-audio control CLI."""

from __future__ import annotations

import json
from pathlib import Path

from abraxas.atlas.construct import load_seedpack
from abraxas.sonification.emit import emit_audio_controls


def run_sonify_cmd(atlas_path: str, out_path: str) -> int:
    atlas_pack = load_seedpack(Path(atlas_path))
    frames = emit_audio_controls(atlas_pack)
    payload = [frame.model_dump() for frame in frames]
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return 0
