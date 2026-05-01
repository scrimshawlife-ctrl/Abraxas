from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from abraxas.core.canonical import canonical_json
from abraxas.viz.controlled_hover_scaffold import build_scaffold


def run(hover_packet_path: Path, ci_proof_path: Path, component_manifest_path: Path, out_path: Path) -> Dict[str, Any]:
    hover_packet = json.loads(hover_packet_path.read_text(encoding="utf-8"))
    ci_proof = json.loads(ci_proof_path.read_text(encoding="utf-8"))
    component_manifest = json.loads(component_manifest_path.read_text(encoding="utf-8"))
    scaffold = build_scaffold(hover_packet, ci_proof, component_manifest)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(canonical_json(scaffold), encoding="utf-8")
    return scaffold
