from __future__ import annotations


def classify_readiness(*, sufficiency_state: str, consequence_level: str) -> str:
    if sufficiency_state == "NOT_COMPUTABLE":
        return "NOT_COMPUTABLE"
    if sufficiency_state == "CONFLICTING_EVIDENCE":
        return "DEFERRED_PENDING_EVIDENCE"
    if sufficiency_state == "BURDEN_UNMET":
        return "ABSTAINED" if consequence_level == "LOW" else "ESCALATED"
    if sufficiency_state == "BURDEN_PROVISIONALLY_MET":
        return "READY_PROVISIONALLY"
    if sufficiency_state == "ESCALATION_REQUIRED":
        return "ESCALATED"
    return "READY_TO_DECIDE"
