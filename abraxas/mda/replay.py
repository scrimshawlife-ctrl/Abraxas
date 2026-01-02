from __future__ import annotations

from typing import Any, Dict
import json
import os


def append_jsonl(path: str, record: Dict[str, Any]) -> None:
    """
    Deterministic replay stream: append one JSON object per line.
    Caller must ensure record contains stable/hardened fields (hashes, input_hash, etc.).
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

