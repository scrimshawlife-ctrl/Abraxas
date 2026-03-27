from __future__ import annotations


def classify_overlap_state(*, same_target: bool, same_domain: bool, domain_policy: str) -> str:
    if not same_domain:
        return "INDEPENDENT_CONCURRENT"
    if not same_target and domain_policy in {"NON_CONFLICTING_OVERLAP", "INDEPENDENT_CONCURRENT"}:
        return "NON_CONFLICTING_OVERLAP"
    if same_target and domain_policy == "MERGEABLE":
        return "MERGEABLE_OVERLAP"
    if same_target and domain_policy == "SERIALIZE_REQUIRED":
        return "SERIALIZE_REQUIRED"
    if same_domain:
        return "SHARED_DOMAIN_CONCURRENT"
    return "NOT_COMPUTABLE"


def classify_concurrency_posture(overlap_states: list[str]) -> str:
    if not overlap_states:
        return "NOT_COMPUTABLE"
    state_set = set(overlap_states)
    if "SERIALIZE_REQUIRED" in state_set:
        return "ARBITRATION_REQUIRED"
    if "MERGEABLE_OVERLAP" in state_set:
        return "MERGEABLE_CONCURRENT"
    if state_set <= {"INDEPENDENT_CONCURRENT", "NON_CONFLICTING_OVERLAP"}:
        return "CONCURRENCY_READY"
    if "NOT_COMPUTABLE" in state_set:
        return "NOT_COMPUTABLE"
    return "PARTIAL"
