from __future__ import annotations


def classify_sufficiency(*, threshold_state: str, conflict_state: str) -> str:
    if threshold_state == "NOT_COMPUTABLE":
        return "NOT_COMPUTABLE"
    if conflict_state == "CONFLICTING_EVIDENCE":
        return "CONFLICTING_EVIDENCE"
    if threshold_state == "THRESHOLD_MET":
        return "BURDEN_MET"
    if threshold_state == "THRESHOLD_PROVISIONALLY_MET":
        return "BURDEN_PROVISIONALLY_MET"
    if threshold_state == "ESCALATION_REQUIRED":
        return "ESCALATION_REQUIRED"
    return "BURDEN_UNMET"
