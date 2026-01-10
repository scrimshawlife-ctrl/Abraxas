"""Atlas-to-visual control CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from abraxas.atlas.construct import load_seedpack
from abraxas.visuals.emit import emit_visual_controls_and_events


def _read_json(path: Optional[str]) -> Optional[Dict[str, Any]]:
    if not path:
        return None
    file_path = Path(path)
    if not file_path.exists():
        raise SystemExit(f"Overlay file not found: {path}")
    return json.loads(file_path.read_text(encoding="utf-8"))


def run_visualize_cmd(
    atlas_path: str,
    out_path: str,
    bridge_set_path: Optional[str] = None,
    alerts_path: Optional[str] = None,
    events_out_path: Optional[str] = None,
) -> int:
    atlas_pack = load_seedpack(Path(atlas_path))
    bridge_set = _read_json(bridge_set_path)
    alerts = _read_json(alerts_path)
    frames, events = emit_visual_controls_and_events(atlas_pack, bridge_set=bridge_set, alerts=alerts)
    payload = [frame.model_dump() for frame in frames]
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    if events_out_path:
        events_file = Path(events_out_path)
        events_file.parent.mkdir(parents=True, exist_ok=True)
        events_file.write_text(json.dumps(events, indent=2, sort_keys=True), encoding="utf-8")
    return 0
