from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from abraxas.core.canonical import canonical_json
from abraxas.viz.react_component_manifest import build_manifest


def run_manifest(repo_root: Path, out_path: Path) -> Dict[str, Any]:
    manifest = build_manifest(repo_root)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(canonical_json(manifest), encoding="utf-8")
    return manifest
