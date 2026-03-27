from __future__ import annotations


def classify_failure_semantics(*, recoverability: str, degraded_state: str, integrity_impact: str) -> str:
    if integrity_impact == "HIGH":
        return "INTEGRITY_COMPROMISED_FAILURE"
    if recoverability == "RETRYABLE_FAILURE" and degraded_state == "DEGRADED_BUT_OPERABLE":
        return "RETRYABLE_FAILURE"
    if recoverability == "NON_RETRYABLE_FAILURE":
        return "NON_RETRYABLE_FAILURE"
    if recoverability == "HUMAN_INTERVENTION_REQUIRED":
        return "HUMAN_INTERVENTION_REQUIRED"
    return "NOT_COMPUTABLE"
