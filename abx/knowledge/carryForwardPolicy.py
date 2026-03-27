from __future__ import annotations

from abx.knowledge.types import CarryForwardPolicyRecord


def build_carry_forward_policy() -> CarryForwardPolicyRecord:
    return CarryForwardPolicyRecord(
        policy_id="carry-forward-policy-v1",
        state="allowed_carry_forward",
        eligible_surfaces=["memory.baseline.current", "memory.continuity.index"],
        prohibited_surfaces=["memory.operator.notes", "memory.scorecard.backlog"],
    )
