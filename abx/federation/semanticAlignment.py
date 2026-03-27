from __future__ import annotations

from abx.federation.continuityAlignment import continuity_alignment_status
from abx.federation.lifecycleAlignment import lifecycle_alignment_status
from abx.federation.policyAlignment import policy_alignment_status
from abx.federation.trustAlignment import trust_alignment_status
from abx.federation.types import FederatedSemanticAlignmentRecord


def build_federated_semantic_alignment() -> list[FederatedSemanticAlignmentRecord]:
    trust = trust_alignment_status()
    lifecycle = lifecycle_alignment_status()
    continuity = continuity_alignment_status()
    policy = policy_alignment_status()
    rows = [
        FederatedSemanticAlignmentRecord("align.trust", "trust", trust[0], trust[1]),
        FederatedSemanticAlignmentRecord("align.lifecycle", "lifecycle", lifecycle[0], lifecycle[1]),
        FederatedSemanticAlignmentRecord("align.continuity", "continuity", continuity[0], continuity[1]),
        FederatedSemanticAlignmentRecord("align.policy", "policy", policy[0], policy[1]),
    ]
    return sorted(rows, key=lambda x: x.alignment_id)
