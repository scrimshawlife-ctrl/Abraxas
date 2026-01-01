from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def append_chained_jsonl(path: str, record: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    prev_hash: Optional[str] = None
    if os.path.exists(path):
        with open(path, "rb") as f:
            lines = f.read().splitlines()
            if lines:
                try:
                    prev = json.loads(lines[-1].decode("utf-8"))
                    prev_hash = prev.get("step_hash")
                except Exception:
                    prev_hash = None

    record = dict(record)
    record.setdefault("ts", _utc_now_iso())
    record["prev_hash"] = prev_hash
    record["step_hash"] = _sha(json.dumps(record, sort_keys=True, ensure_ascii=False))

    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
