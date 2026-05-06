"""IntakeConflictPacket.v1 - Conflict detection for oracle intake.

Rules:
- authority locked
- duplicate deterministic sources must collapse cleanly
- unresolved authority conflicts fail closed
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any, List
import json

from pydantic import BaseModel

from core.models.governance import Authority

VALID_CONFLICT_TYPES = {
    "provenance_mismatch",
    "normalization_mismatch",
    "replay_mismatch",
    "lineage_break",
    "authority_violation",
    "duplicate_source",
}

VALID_SEVERITIES = {"low", "medium", "high", "critical"}
VALID_STATUSES = {"unresolved", "resolved", "collapsed", "failed"}


class IntakeConflictPacket(BaseModel):
    schema_version: str = "IntakeConflictPacket.v1"
    conflict_id: str
    conflicting_source_hashes: List[str]
    conflict_type: str
    severity: str
    authority: Authority
    resolution_required: bool
    status: str

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")
        if self.conflict_type not in VALID_CONFLICT_TYPES:
            raise ValueError(f"conflict_type must be one of {VALID_CONFLICT_TYPES}")
        if self.severity not in VALID_SEVERITIES:
            raise ValueError(f"severity must be one of {VALID_SEVERITIES}")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")

    def conflict_hash(self) -> str:
        canonical = json.dumps(
            {
                "conflict_id": self.conflict_id,
                "conflicting_source_hashes": sorted(self.conflicting_source_hashes),
                "conflict_type": self.conflict_type,
                "severity": self.severity,
                "resolution_required": self.resolution_required,
                "status": self.status,
            },
            sort_keys=True,
        ).encode("utf-8")
        return sha256(canonical).hexdigest()


def detect_duplicate_sources(source_hashes: List[str]) -> List[str]:
    """Detect duplicate source hashes. Returns list of duplicated hashes."""
    seen: dict[str, int] = {}
    for h in source_hashes:
        seen[h] = seen.get(h, 0) + 1
    return [h for h, count in seen.items() if count > 1]


def build_conflict_packet(
    conflict_id: str,
    conflicting_source_hashes: List[str],
    conflict_type: str,
    authority: Authority,
    severity: str = "medium",
    resolution_required: bool = True,
) -> IntakeConflictPacket:
    """Build an IntakeConflictPacket.

    Duplicate deterministic sources collapse cleanly (status=collapsed).
    Authority violations fail closed (status=failed).
    """
    if not authority.is_locked():
        raise ValueError("authority must be locked")

    # Authority violations fail closed
    if conflict_type == "authority_violation":
        return IntakeConflictPacket(
            conflict_id=conflict_id,
            conflicting_source_hashes=conflicting_source_hashes,
            conflict_type=conflict_type,
            severity="critical",
            authority=authority,
            resolution_required=True,
            status="failed",
        )

    # Duplicate deterministic sources collapse cleanly
    if conflict_type == "duplicate_source":
        duplicates = detect_duplicate_sources(conflicting_source_hashes)
        if duplicates:
            return IntakeConflictPacket(
                conflict_id=conflict_id,
                conflicting_source_hashes=conflicting_source_hashes,
                conflict_type=conflict_type,
                severity=severity,
                authority=authority,
                resolution_required=False,
                status="collapsed",
            )

    return IntakeConflictPacket(
        conflict_id=conflict_id,
        conflicting_source_hashes=conflicting_source_hashes,
        conflict_type=conflict_type,
        severity=severity,
        authority=authority,
        resolution_required=resolution_required,
        status="unresolved",
    )
