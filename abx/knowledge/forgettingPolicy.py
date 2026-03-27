from __future__ import annotations

from abx.knowledge.types import ForgettingPolicyRecord


def build_forgetting_policy() -> ForgettingPolicyRecord:
    return ForgettingPolicyRecord(
        policy_id="forgetting-policy-v1",
        expiry_states=["STALE", "EXPIRED"],
        archival_only_states=["ARCHIVAL"],
    )
