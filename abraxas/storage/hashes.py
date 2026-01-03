"""Deterministic hashing primitives for CAS.

Performance Drop v1.0 - SHA-256 based content addressing.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def stable_hash_bytes(raw_bytes: bytes) -> str:
    """Compute stable SHA-256 hash of raw bytes.

    Args:
        raw_bytes: Raw byte content

    Returns:
        Hex-encoded SHA-256 hash
    """
    return hashlib.sha256(raw_bytes).hexdigest()


def stable_hash_json(obj: Any) -> str:
    """Compute stable SHA-256 hash of JSON-serializable object.

    Uses canonical JSON encoding: sorted keys, no whitespace,
    deterministic float representation.

    Args:
        obj: JSON-serializable object

    Returns:
        Hex-encoded SHA-256 hash
    """
    canonical = json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,  # Convert datetime and other types to string
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
