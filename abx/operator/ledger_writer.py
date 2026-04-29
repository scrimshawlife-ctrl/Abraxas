from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Optional


def write_operator_queue(queue: Mapping[str, Any], base_dir: Optional[Path] = None) -> Optional[str]:
    root = base_dir or Path("out")
    if not root.exists():
        return None
    target_dir = root / "operator"
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / "operator_queue.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(queue), sort_keys=True) + "\n")
    return path.as_posix()
