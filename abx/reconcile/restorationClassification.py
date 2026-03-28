from __future__ import annotations


def classify_restoration(*, restoration_state: str, validation_state: str) -> str:
    if restoration_state == "NOT_COMPUTABLE":
        return "NOT_COMPUTABLE"
    if restoration_state == "RESTORATION_FAILED" or validation_state == "BLOCKED":
        return "BLOCKED"
    if restoration_state == "COSMETIC_ALIGNMENT_ONLY":
        return "COSMETIC_ALIGNMENT_ONLY"
    if validation_state in {"PENDING_VALIDATION", "VALIDATION_REQUIRED"}:
        return "PROVISIONAL_OR_PENDING"
    return restoration_state
