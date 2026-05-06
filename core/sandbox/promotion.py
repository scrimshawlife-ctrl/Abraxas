"""SandboxPromotionCandidate.v1 - Operator-reviewed promotion candidates.

Rules:
- authority locked
- promotion_allowed defaults false
- cannot promote unstable branches
- cannot bypass operator review
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any, List
import json

from pydantic import BaseModel

from core.models.governance import Authority

VALID_STATUSES = {"pending", "approved", "rejected", "blocked"}


class SandboxPromotionCandidate(BaseModel):
    schema_version: str = "SandboxPromotionCandidate.v1"
    candidate_id: str
    sandbox_branch_hash: str
    stabilization_hash: str
    replay_hash: str
    proposed_promotions: List[str]
    operator_review_required: bool
    promotion_allowed: bool
    authority: Authority
    status: str

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")
        # Promotion defaults false - enforce safety
        if self.promotion_allowed and self.operator_review_required:
            # Cannot allow promotion while operator review is required
            object.__setattr__(self, "promotion_allowed", False)
            object.__setattr__(self, "status", "blocked")

    def candidate_hash(self) -> str:
        canonical = json.dumps(
            {
                "candidate_id": self.candidate_id,
                "sandbox_branch_hash": self.sandbox_branch_hash,
                "stabilization_hash": self.stabilization_hash,
                "replay_hash": self.replay_hash,
                "proposed_promotions": sorted(self.proposed_promotions),
                "promotion_allowed": self.promotion_allowed,
            },
            sort_keys=True,
        ).encode("utf-8")
        return sha256(canonical).hexdigest()


def build_promotion_candidate(
    candidate_id: str,
    sandbox_branch_hash: str,
    stabilization_hash: str,
    replay_hash: str,
    proposed_promotions: List[str],
    authority: Authority,
    stabilization_state: str = "unstable",
) -> SandboxPromotionCandidate:
    """Build a SandboxPromotionCandidate with fail-closed promotion gating.

    - Cannot promote unstable branches
    - Operator review always required
    - promotion_allowed defaults False
    """
    # Always require operator review
    operator_review_required = True
    # Never allow promotion of unstable branches or when review pending
    promotion_allowed = False
    status = "pending"

    if stabilization_state == "failed":
        status = "blocked"

    return SandboxPromotionCandidate(
        candidate_id=candidate_id,
        sandbox_branch_hash=sandbox_branch_hash,
        stabilization_hash=stabilization_hash,
        replay_hash=replay_hash,
        proposed_promotions=sorted(proposed_promotions),
        operator_review_required=operator_review_required,
        promotion_allowed=promotion_allowed,
        authority=authority,
        status=status,
    )
