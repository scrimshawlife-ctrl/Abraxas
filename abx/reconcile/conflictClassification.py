from __future__ import annotations


def classify_conflict(*, conflict_state: str, severity: str) -> str:
    if conflict_state == "NOT_COMPUTABLE":
        return "NOT_COMPUTABLE"
    if conflict_state == "CONFLICT_UNKNOWN":
        return "CONFLICT_UNKNOWN"
    if conflict_state == "BLOCKING_CONFLICT":
        return "BLOCKING_CONFLICT"
    if conflict_state == "COSMETIC_MISMATCH":
        return "COSMETIC_MISMATCH"
    return conflict_state
