"""IntakeNormalizationPacket.v1 - Deterministic normalization of intake payloads.

Rules:
- authority locked
- normalization deterministic
- identical source => identical normalized hash
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any, Dict, List
import json

from pydantic import BaseModel

from core.models.governance import Authority

VALID_STATUSES = {"complete", "failed", "not_computable"}


class IntakeNormalizationPacket(BaseModel):
    schema_version: str = "IntakeNormalizationPacket.v1"
    normalization_id: str
    source_hash: str
    normalized_hash: str
    normalization_steps: List[str]
    deterministic_normalization_hash: str
    authority: Authority
    status: str

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")


def normalize_payload(raw_payload: Any) -> Dict[str, Any]:
    """Deterministically normalize an intake payload.

    Normalization rules (deterministic):
    1. Sort all dict keys recursively.
    2. Strip None values from top-level.
    3. Convert all string values to lower-case if they are string-type fields.
    """
    if isinstance(raw_payload, dict):
        cleaned = {k: normalize_payload(v) for k, v in sorted(raw_payload.items()) if v is not None}
        return cleaned
    if isinstance(raw_payload, list):
        return [normalize_payload(item) for item in raw_payload]
    if isinstance(raw_payload, str):
        return raw_payload.strip().lower()
    return raw_payload


def hash_normalized(normalized: Any) -> str:
    serialized = json.dumps(normalized, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return sha256(serialized).hexdigest()


def build_normalization_packet(
    normalization_id: str,
    source_hash: str,
    raw_payload: Any,
    authority: Authority,
) -> IntakeNormalizationPacket:
    """Build a deterministic IntakeNormalizationPacket from a raw payload."""
    if not authority.is_locked():
        raise ValueError("authority must be locked")

    if not source_hash:
        return IntakeNormalizationPacket(
            normalization_id=normalization_id,
            source_hash=source_hash,
            normalized_hash="",
            normalization_steps=[],
            deterministic_normalization_hash="",
            authority=authority,
            status="not_computable",
        )

    steps: List[str] = [
        "sort_keys",
        "strip_none",
        "lowercase_strings",
    ]

    normalized = normalize_payload(raw_payload)
    norm_hash = hash_normalized(normalized)

    # Deterministic normalization hash: hash of (source_hash + norm_hash + steps)
    det_hash_input = json.dumps(
        {
            "normalization_id": normalization_id,
            "source_hash": source_hash,
            "normalized_hash": norm_hash,
            "steps": steps,
        },
        sort_keys=True,
    ).encode("utf-8")
    det_hash = sha256(det_hash_input).hexdigest()

    return IntakeNormalizationPacket(
        normalization_id=normalization_id,
        source_hash=source_hash,
        normalized_hash=norm_hash,
        normalization_steps=steps,
        deterministic_normalization_hash=det_hash,
        authority=authority,
        status="complete",
    )
