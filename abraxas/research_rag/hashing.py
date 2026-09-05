"""Deterministic content hashes for ingest idempotency."""

from __future__ import annotations

from typing import Mapping

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.research_rag.types import Payload


def payload_content_hash(payload: Payload) -> str:
    """SHA-256 of the ingest payload. Idempotency key uses this plus Source ID."""
    if isinstance(payload, bytes):
        return sha256_hex(payload)
    if isinstance(payload, str):
        return sha256_hex(payload)
    if isinstance(payload, Mapping):
        return sha256_hex(canonical_json(dict(payload)))
    raise TypeError(f"unsupported_payload_type:{type(payload).__name__}")


def chunk_content_hash(excerpt: str, locator_url: str = "") -> str:
    return sha256_hex(canonical_json({"excerpt": excerpt, "locator_url": locator_url}))


def chunk_id_for(source_id: str, payload_hash: str, index: int) -> str:
    return f"{source_id}:{payload_hash[:12]}:{index:04d}"
