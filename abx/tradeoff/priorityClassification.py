from __future__ import annotations


def classify_priority(*, priority_state: str, tie_breaker: str) -> str:
    if priority_state in {"BLOCKED", "NOT_COMPUTABLE", "PRIORITY_CONFLICT", "PRIORITY_UNKNOWN"}:
        return priority_state
    if priority_state in {
        "CANON_PRIORITY",
        "SITUATIONAL_PRIORITY",
        "TEMPORARY_PRIORITY_OVERRIDE",
        "EMERGENCY_PRIORITY_OVERRIDE",
        "TIE_BREAK_PRIORITY",
    }:
        return priority_state
    if tie_breaker == "policy_order":
        return "CANON_PRIORITY"
    return "SITUATIONAL_PRIORITY"
