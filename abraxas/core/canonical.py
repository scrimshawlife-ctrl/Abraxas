"""Canonical JSON encoding for deterministic signatures and provenance."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Union

JsonLike = Any


def canonical_json(obj: JsonLike) -> str:
    """
    Canonical JSON used for signatures/provenance.
    - UTF-8
    - Sorted keys
    - No whitespace variability
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(data: Union[str, bytes]) -> str:
    """Compute SHA256 hash of string or bytes, returning hex digest."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()
