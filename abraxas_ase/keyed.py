from __future__ import annotations

import hashlib
import hmac
import os
from typing import Optional


def read_key_or_none() -> Optional[bytes]:
    raw = os.environ.get("ASE_KEY", "")
    if not raw:
        return None
    return raw.encode("utf-8")


def require_key() -> bytes:
    key = read_key_or_none()
    if not key:
        raise RuntimeError("ASE_KEY environment variable is required for academic/enterprise tiers.")
    return key


def sha256_hex_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def key_fingerprint(key: bytes) -> str:
    return sha256_hex_bytes(key)[:8]


def hmac_hex(key: bytes, payload: bytes) -> str:
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def keyed_id(key: bytes, payload: str, n: int = 16) -> str:
    return hmac_hex(key, payload.encode("utf-8"))[:n]
