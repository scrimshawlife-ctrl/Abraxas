from __future__ import annotations


def classify_conflict_resolution_hint(conflict_class: str) -> str:
    if conflict_class == "NO_CONFLICT":
        return "PROCEED_PARALLEL"
    if conflict_class == "DUPLICATE_CONFLICT":
        return "MERGE_OR_SUPPRESS"
    if conflict_class == "TARGET_CONFLICT":
        return "SERIALIZE"
    if conflict_class == "AUTHORITY_CONFLICT":
        return "ARBITRATION_REQUIRED"
    if conflict_class == "POLICY_CONFLICT":
        return "DENY_AND_ESCALATE"
    if conflict_class == "TEMPORAL_CONFLICT":
        return "DELAY"
    if conflict_class == "SIDE_EFFECT_CONFLICT":
        return "ABORT_OR_COMPENSATE"
    if conflict_class == "MERGEABLE_CONFLICT":
        return "MERGE"
    return "NOT_COMPUTABLE"


def classify_conflict_posture(conflict_classes: list[str]) -> str:
    if not conflict_classes:
        return "NOT_COMPUTABLE"
    kinds = set(conflict_classes)
    if "POLICY_CONFLICT" in kinds or "SIDE_EFFECT_CONFLICT" in kinds:
        return "BLOCKED_BY_CONFLICT"
    if "AUTHORITY_CONFLICT" in kinds or "TARGET_CONFLICT" in kinds:
        return "ARBITRATION_REQUIRED"
    if kinds <= {"NO_CONFLICT", "MERGEABLE_CONFLICT"}:
        return "NON_CONFLICTING_CONCURRENT"
    if "TEMPORAL_CONFLICT" in kinds or "DUPLICATE_CONFLICT" in kinds:
        return "DEGRADED"
    return "PARTIAL"
