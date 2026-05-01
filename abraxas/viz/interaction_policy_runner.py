from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from abraxas.core.canonical import canonical_json
from abraxas.viz.interaction_policy import build_interaction_policy


def run_interaction_policy(viewer_spec_path: Path, component_manifest_path: Path, out_path: Path) -> Dict[str, Any]:
    viewer_spec = json.loads(viewer_spec_path.read_text(encoding="utf-8"))
    component_manifest = json.loads(component_manifest_path.read_text(encoding="utf-8"))
    policy = build_interaction_policy(viewer_spec, component_manifest)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(canonical_json(policy), encoding="utf-8")
    return policy
