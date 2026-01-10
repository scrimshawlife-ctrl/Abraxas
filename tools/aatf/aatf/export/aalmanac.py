from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json


def export_aalmanac_bundle(output_dir: Path) -> Dict[str, Any]:
    payload = {
        "schema_version": "aatf.export.aalmanac.v0",
        "items": [],
    }
    out = output_dir / "aalmanac.v0.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return {"path": str(out), "count": 0}
