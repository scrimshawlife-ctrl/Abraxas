from __future__ import annotations


def classify_arbitration_outcome(conflict_class: str) -> str:
    if conflict_class == "NO_CONFLICT":
        return "MERGED"
    if conflict_class == "DUPLICATE_CONFLICT":
        return "MERGED"
    if conflict_class == "MERGEABLE_CONFLICT":
        return "MERGED"
    if conflict_class == "TARGET_CONFLICT":
        return "SERIALIZED"
    if conflict_class == "TEMPORAL_CONFLICT":
        return "DELAYED"
    if conflict_class == "AUTHORITY_CONFLICT":
        return "ESCALATED"
    if conflict_class == "SIDE_EFFECT_CONFLICT":
        return "DENIED"
    if conflict_class == "POLICY_CONFLICT":
        return "BLOCKED"
    return "NOT_COMPUTABLE"
