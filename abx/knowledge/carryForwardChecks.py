from __future__ import annotations

from abx.knowledge.carryForwardPolicy import build_carry_forward_policy
from abx.knowledge.memoryLifecycle import build_memory_lifecycle


def run_carry_forward_checks() -> dict[str, object]:
    policy = build_carry_forward_policy()
    stale = []
    prohibited_active = []
    for row in build_memory_lifecycle():
        if row.memory_id in policy.eligible_surfaces and row.lifecycle_state in {"STALE", "EXPIRED", "RETIRED"}:
            stale.append(row.memory_id)
        if row.memory_id in policy.prohibited_surfaces and row.lifecycle_state in {"ACTIVE", "GOVERNED_DERIVED"}:
            prohibited_active.append(row.memory_id)
    return {
        "policy": policy.__dict__,
        "staleCarryForward": sorted(stale),
        "prohibitedButActive": sorted(prohibited_active),
    }
