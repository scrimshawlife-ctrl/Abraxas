from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from abraxas.core.canonical import canonical_json
from abraxas.viz.webgl_scene import build_scene_spec


def run_webgl_scene_spec(input_path: Path, out_path: Path) -> Dict[str, Any]:
    packet = json.loads(input_path.read_text(encoding="utf-8"))
    spec = build_scene_spec(packet)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(canonical_json(spec), encoding="utf-8")
    return spec
