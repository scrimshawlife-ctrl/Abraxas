from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import json
import time

DEFAULT_REJECTIONS_PATH = Path.home() / ".aal" / "aalmanac" / "rejections.jsonl"


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")


def append_rejection(
    entry: Dict[str, Any],
    *,
    reason: str,
    rejection_path: Optional[Path] = None,
) -> None:
    target = rejection_path or DEFAULT_REJECTIONS_PATH
    _ensure_dir(target)
    payload = dict(entry)
    payload["rejected_reason"] = reason
    payload["rejected_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True) + "\n")
