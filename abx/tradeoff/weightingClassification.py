from __future__ import annotations


def classify_weighting(*, weighting_state: str, weighting_source: str) -> str:
    if weighting_state in {"BLOCKED", "NOT_COMPUTABLE", "HIDDEN_WEIGHTING_SUSPECTED", "VALUE_CONFLICT_UNRESOLVED"}:
        return weighting_state
    if weighting_state in {
        "CANON_WEIGHTING_ACTIVE",
        "LOCAL_WEIGHTING_ACTIVE",
        "TEMPORARY_WEIGHTING_ACTIVE",
        "EMERGENCY_WEIGHTING_ACTIVE",
    }:
        return weighting_state
    if weighting_source.startswith("runtime/"):
        return "LOCAL_WEIGHTING_ACTIVE"
    return "CANON_WEIGHTING_ACTIVE"
