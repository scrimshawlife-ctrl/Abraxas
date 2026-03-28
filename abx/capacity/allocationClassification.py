from __future__ import annotations


def classify_commitment(*, commitment_state: str, allocation_state: str) -> str:
    if commitment_state == "NOT_COMPUTABLE" or allocation_state == "NOT_COMPUTABLE":
        return "NOT_COMPUTABLE"
    if commitment_state == "BLOCKED":
        return "BLOCKED"
    if commitment_state == "COMMITMENT_UNKNOWN":
        return "COMMITMENT_UNKNOWN"
    return commitment_state
