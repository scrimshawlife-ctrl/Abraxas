"""IntakeEnvelope.v1 - Governed intake envelope for oracle source ingestion.

Rules:
- authority locked
- deterministic payload hashing
- timestamp_index monotonic
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any, Optional
import json

from pydantic import BaseModel

from core.models.governance import Authority

VALID_SOURCE_TYPES = {
    "document",
    "receipt",
    "projection",
    "topology",
    "telemetry",
    "replay",
    "stabilization",
    "sandbox",
}

VALID_INTAKE_STATUSES = {
    "pending",
    "normalized",
    "conflict_detected",
    "approved",
    "rejected",
    "not_computable",
}


class IntakeEnvelope(BaseModel):
    schema_version: str = "IntakeEnvelope.v1"
    intake_id: str
    source_id: str
    source_type: str
    intake_timestamp_index: int
    raw_payload_hash: str
    normalized_payload_hash: Optional[str] = None
    authority: Authority
    intake_status: str

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")
        if self.source_type not in VALID_SOURCE_TYPES:
            raise ValueError(f"source_type must be one of {VALID_SOURCE_TYPES}")
        if self.intake_status not in VALID_INTAKE_STATUSES:
            raise ValueError(f"intake_status must be one of {VALID_INTAKE_STATUSES}")
        if self.intake_timestamp_index < 0:
            raise ValueError("intake_timestamp_index must be non-negative")

    def envelope_hash(self) -> str:
        canonical = json.dumps(
            {
                "intake_id": self.intake_id,
                "source_id": self.source_id,
                "source_type": self.source_type,
                "intake_timestamp_index": self.intake_timestamp_index,
                "raw_payload_hash": self.raw_payload_hash,
                "normalized_payload_hash": self.normalized_payload_hash,
                "intake_status": self.intake_status,
            },
            sort_keys=True,
        ).encode("utf-8")
        return sha256(canonical).hexdigest()


def hash_payload(payload: Any) -> str:
    """Deterministically hash an arbitrary payload."""
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return sha256(serialized).hexdigest()


def build_intake_envelope(
    intake_id: str,
    source_id: str,
    source_type: str,
    intake_timestamp_index: int,
    raw_payload: Any,
    authority: Authority,
    normalized_payload: Any = None,
    intake_status: str = "pending",
) -> IntakeEnvelope:
    """Build a deterministic IntakeEnvelope from a raw payload."""
    if not authority.is_locked():
        raise ValueError("authority must be locked")

    raw_hash = hash_payload(raw_payload)
    norm_hash: Optional[str] = None
    if normalized_payload is not None:
        norm_hash = hash_payload(normalized_payload)

    return IntakeEnvelope(
        intake_id=intake_id,
        source_id=source_id,
        source_type=source_type,
        intake_timestamp_index=intake_timestamp_index,
        raw_payload_hash=raw_hash,
        normalized_payload_hash=norm_hash,
        authority=authority,
        intake_status=intake_status,
    )
