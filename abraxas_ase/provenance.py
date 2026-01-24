from __future__ import annotations

import hashlib
import json
from typing import Any


def stable_json_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_items_for_run(items: list[dict]) -> str:
    """
    Deterministic content hash for the run.
    Note: items should already be parsed JSON objects in a deterministic order
    (we sort by (published_at, source, id) upstream).
    """
    payload = stable_json_dumps(items).encode("utf-8")
    return sha256_hex(payload)


def make_run_id(date_str: str, items_hash: str, version: str) -> str:
    base = f"{date_str}|{version}|{items_hash}"
    return sha256_hex(base.encode("utf-8"))[:16]
