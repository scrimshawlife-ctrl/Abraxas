from __future__ import annotations


def classify_ratification_state(*, unmet_criteria: list[str], waived_criteria: list[str], audit_readiness_state: str) -> str:
    if audit_readiness_state in {"BLOCKED", "EVIDENCE_INCOMPLETE", "NOT_COMPUTABLE"}:
        return "NOT_RATIFIABLE"
    if unmet_criteria:
        return "NOT_RATIFIABLE"
    if waived_criteria:
        return "CONDITIONALLY_RATIFIABLE"
    if audit_readiness_state == "AUDIT_READY_WITH_GAPS":
        return "CONDITIONALLY_RATIFIABLE"
    if audit_readiness_state == "AUDIT_READY":
        return "READY_FOR_RATIFICATION"
    return "NOT_COMPUTABLE"
