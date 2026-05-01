from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from abraxas.core.canonical import canonical_json
from abraxas.viz.svg_ledger import build_ledger_run


def run_svg_artifact_ledger(manifest_path: Path, out_path: Path, previous_path: Optional[Path] = None) -> Dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    previous = None
    if previous_path is not None and previous_path.exists():
        previous = json.loads(previous_path.read_text(encoding="utf-8"))

    run = build_ledger_run(manifest=manifest, previous=previous)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(canonical_json(run), encoding="utf-8")
    return run
