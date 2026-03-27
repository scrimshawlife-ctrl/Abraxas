from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Lane = Literal["SHADOW", "CANARY", "ACTIVE", "DEPRECATED"]


@dataclass(frozen=True)
class PromotionEligibilityArtifact:
    artifact_type: str
    artifact_id: str
    module_id: str
    current_lane: Lane
    target_lane: Lane
    eligible: bool
    missing_evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LanePolicyArtifact:
    artifact_type: str
    artifact_id: str
    violations: list[str] = field(default_factory=list)
    status: str = "VALID"


def evaluate_promotion_eligibility(
    *,
    module_id: str,
    current_lane: Lane,
    target_lane: Lane,
    evidence: dict,
) -> PromotionEligibilityArtifact:
    required = ["contract_present", "tests_present", "invariance_present", "proof_present", "lineage_present"]
    missing = [key for key in required if not bool(evidence.get(key))]

    # Cannot promote SHADOW directly to ACTIVE without canary evidence.
    if current_lane == "SHADOW" and target_lane == "ACTIVE":
        if not bool(evidence.get("canary_passed")):
            missing.append("canary_passed")

    eligible = len(missing) == 0
    return PromotionEligibilityArtifact(
        artifact_type="PromotionEligibilityArtifact.v1",
        artifact_id=f"promotion-{module_id}-{current_lane}-to-{target_lane}",
        module_id=module_id,
        current_lane=current_lane,
        target_lane=target_lane,
        eligible=eligible,
        missing_evidence=sorted(set(missing)),
    )


def enforce_lane_policy(*, lane: Lane, influence_policy: str, influences_active_path: bool) -> LanePolicyArtifact:
    violations: list[str] = []

    if lane == "SHADOW" and influences_active_path:
        violations.append("shadow_leakage_into_active")
    if lane == "CANARY" and influence_policy not in {"NONE", "BOUNDED"}:
        violations.append("canary_influence_not_bounded")
    if lane == "ACTIVE" and influence_policy == "NONE":
        violations.append("active_lane_missing_influence_contract")

    status = "VALID" if not violations else "BROKEN"
    return LanePolicyArtifact(
        artifact_type="LanePolicyArtifact.v1",
        artifact_id=f"lane-policy-{lane.lower()}",
        violations=violations,
        status=status,
    )
