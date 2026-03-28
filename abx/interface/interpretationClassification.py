from __future__ import annotations


def classify_acceptance(*, acceptance_state: str, interpretation_state: str) -> str:
    if acceptance_state == "NOT_COMPUTABLE" or interpretation_state == "NOT_COMPUTABLE":
        return "NOT_COMPUTABLE"
    if acceptance_state in {"REJECTED", "COERCED_DEFAULTED", "INTERPRETATION_MISMATCH"}:
        return acceptance_state
    return acceptance_state
