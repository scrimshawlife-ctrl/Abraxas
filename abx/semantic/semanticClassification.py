from __future__ import annotations


def classify_semantic_drift(*, drift_state: str, drift_kind: str) -> str:
    if drift_state == "NOT_COMPUTABLE":
        return "NOT_COMPUTABLE"
    if drift_state in {"SEMANTIC_BREAK", "SEMANTIC_DRIFT_DETECTED"}:
        return drift_state
    if drift_state in {"SEMANTIC_ALIAS_ACTIVE", "SEMANTIC_DEPRECATION_ACTIVE"}:
        return drift_state
    if drift_kind == "UNKNOWN":
        return "SEMANTIC_UNKNOWN"
    return "MEANING_PRESERVED"
