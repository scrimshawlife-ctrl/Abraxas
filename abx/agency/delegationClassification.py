from __future__ import annotations


def classify_delegation_state(*, handoff_type: str, depth: int, max_depth: int) -> str:
    if depth > max_depth:
        return "RECURSIVE_DELEGATION_BLOCKED"
    if handoff_type == "DIRECT_EXECUTION":
        return "DIRECT_EXECUTION"
    if handoff_type == "ASSISTED_HANDOFF":
        return "ASSISTED_HANDOFF"
    if handoff_type == "BOUNDED_DELEGATION":
        return "BOUNDED_DELEGATION"
    if handoff_type == "ESCALATION":
        return "ESCALATION"
    if handoff_type == "RETRY_REDELIVERY":
        return "RETRY_REDELIVERY"
    return "NOT_COMPUTABLE"


def classify_delegation_posture(chain_states: dict[str, str]) -> str:
    if not chain_states:
        return "NOT_COMPUTABLE"
    values = set(chain_states.values())
    if "RECURSIVE_DELEGATION_BLOCKED" in values:
        return "BLOCKED"
    if "BOUNDED_DELEGATION" in values:
        return "DELEGATION_READY"
    if values == {"DIRECT_EXECUTION"}:
        return "DIRECT_ONLY"
    return "PARTIAL"
