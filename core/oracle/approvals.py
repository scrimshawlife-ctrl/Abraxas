"""IntakeApprovalPacket.v1 - Operator-reviewed intake approval.

Rules:
- authority locked
- approved defaults false
- unresolved conflicts block approval
- operator review required
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any, List
import json

from pydantic import BaseModel

from core.models.governance import Authority

VALID_STATUSES = {"pending", "approved", "rejected", "blocked"}


class IntakeApprovalPacket(BaseModel):
    schema_version: str = "IntakeApprovalPacket.v1"
    approval_id: str
    intake_hash: str
    stabilization_hash: str
    conflict_hashes: List[str]
    approval_required: bool
    approved: bool
    authority: Authority
    status: str

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")
        # approved defaults false - cannot be true if conflicts exist
        if self.approved and self.conflict_hashes:
            raise ValueError(
                "approval cannot be granted when unresolved conflicts exist"
            )

    @property
    def resolution_required_via_conflicts(self) -> bool:
        return bool(self.conflict_hashes)

    def approval_hash(self) -> str:
        canonical = json.dumps(
            {
                "approval_id": self.approval_id,
                "intake_hash": self.intake_hash,
                "stabilization_hash": self.stabilization_hash,
                "conflict_hashes": sorted(self.conflict_hashes),
                "approval_required": self.approval_required,
                "approved": self.approved,
                "status": self.status,
            },
            sort_keys=True,
        ).encode("utf-8")
        return sha256(canonical).hexdigest()


def build_approval_packet(
    approval_id: str,
    intake_hash: str,
    stabilization_hash: str,
    conflict_hashes: List[str],
    authority: Authority,
    approved: bool = False,
) -> IntakeApprovalPacket:
    """Build an IntakeApprovalPacket.

    Unresolved conflicts block approval.
    approved defaults to False (operator review required).
    """
    if not authority.is_locked():
        raise ValueError("authority must be locked")

    # Unresolved conflicts block approval
    if conflict_hashes:
        return IntakeApprovalPacket(
            approval_id=approval_id,
            intake_hash=intake_hash,
            stabilization_hash=stabilization_hash,
            conflict_hashes=conflict_hashes,
            approval_required=True,
            approved=False,
            authority=authority,
            status="blocked",
        )

    # No conflicts: approval_required=True, operator must set approved=True explicitly
    status = "approved" if approved else "pending"
    return IntakeApprovalPacket(
        approval_id=approval_id,
        intake_hash=intake_hash,
        stabilization_hash=stabilization_hash,
        conflict_hashes=[],
        approval_required=True,
        approved=approved,
        authority=authority,
        status=status,
    )
