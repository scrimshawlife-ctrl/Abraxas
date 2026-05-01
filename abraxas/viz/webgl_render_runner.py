from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from abraxas.core.canonical import canonical_json
from abraxas.viz.webgl_render_bundle import build_render_bundle


def run_render_bundle(input_path: Path, out_path: Path) -> Dict[str, Any]:
    scene_spec = json.loads(input_path.read_text(encoding="utf-8"))
    bundle = build_render_bundle(scene_spec)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(canonical_json(bundle), encoding="utf-8")
    return bundle
