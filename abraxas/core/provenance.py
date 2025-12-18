"""Provenance tracking for all OAS operations."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class ProvenanceRef(BaseModel):
    """Reference to a provenance source with content hash."""

    scheme: str = Field(..., description="Source scheme: file, event, operator, etc.")
    path: str = Field(..., description="Path or identifier within scheme")
    sha256: str = Field(..., description="SHA256 hash of referenced content")

    def __hash__(self) -> int:
        return hash((self.scheme, self.path, self.sha256))


class ProvenanceBundle(BaseModel):
    """Complete provenance record for a transformation or decision."""

    inputs: list[ProvenanceRef] = Field(default_factory=list, description="Input references")
    transforms: list[str] = Field(default_factory=list, description="Ordered list of transform names applied")
    metrics: dict[str, float] = Field(default_factory=dict, description="Metrics computed during this operation")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = Field(default="oasis", description="System or component that created this bundle")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


def hash_canonical_json(obj: Any) -> str:
    """
    Compute stable SHA256 hash of JSON-serializable object.

    Uses canonical JSON encoding: sorted keys, no whitespace, deterministic float repr.
    """
    canonical = json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,  # Convert datetime and other types to string
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def hash_string(s: str) -> str:
    """Compute SHA256 hash of a string."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def hash_bytes(b: bytes) -> str:
    """Compute SHA256 hash of bytes."""
    return hashlib.sha256(b).hexdigest()
