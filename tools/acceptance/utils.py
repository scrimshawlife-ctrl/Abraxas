from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(payload: Any) -> str:
    """Return canonical JSON string for deterministic hashing."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def sha256(payload: str) -> str:
    """Return SHA-256 hash for string payload."""
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
