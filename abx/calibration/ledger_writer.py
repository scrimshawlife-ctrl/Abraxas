from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Optional


def write_calibration_report(report: Mapping[str, Any], base_dir: Optional[Path] = None) -> Optional[str]:
    root = base_dir or Path("out")
    if not root.exists():
        return None
    target_dir = root / "pse"
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / "calibration_drift_report.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(report), sort_keys=True) + "\n")
    return path.as_posix()
