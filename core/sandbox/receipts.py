"""MutationProposalReceipt.v1 - Deterministic receipts for mutation proposals.

Rules:
- authority locked
- deterministic receipt hashing
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any
import json

from pydantic import BaseModel

from core.models.governance import Authority

VALID_STATUSES = {"issued", "validated", "invalidated", "expired"}


class MutationProposalReceipt(BaseModel):
    schema_version: str = "MutationProposalReceipt.v1"
    receipt_id: str
    mutation_hash: str
    branch_hash: str
    replay_hash: str
    stabilization_hash: str
    authority: Authority
    status: str

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")

    def receipt_hash(self) -> str:
        canonical = json.dumps(
            {
                "receipt_id": self.receipt_id,
                "mutation_hash": self.mutation_hash,
                "branch_hash": self.branch_hash,
                "replay_hash": self.replay_hash,
                "stabilization_hash": self.stabilization_hash,
                "status": self.status,
            },
            sort_keys=True,
        ).encode("utf-8")
        return sha256(canonical).hexdigest()


def build_mutation_receipt(
    receipt_id: str,
    mutation_hash: str,
    branch_hash: str,
    replay_hash: str,
    stabilization_hash: str,
    authority: Authority,
) -> MutationProposalReceipt:
    """Build a deterministic MutationProposalReceipt."""
    return MutationProposalReceipt(
        receipt_id=receipt_id,
        mutation_hash=mutation_hash,
        branch_hash=branch_hash,
        replay_hash=replay_hash,
        stabilization_hash=stabilization_hash,
        authority=authority,
        status="issued",
    )
