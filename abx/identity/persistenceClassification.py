from __future__ import annotations


def classify_persistence(*, persistence_state: str, continuity_ref: str) -> str:
    if persistence_state in {"NOT_COMPUTABLE", "CONTINUITY_UNKNOWN", "IDENTITY_BREAK"}:
        return persistence_state
    if persistence_state in {
        "PERSISTENT_CANONICAL_IDENTITY",
        "REMAPPED_CANONICAL_IDENTITY",
        "DEPRECATED_IDENTIFIER",
        "DISPLAY_ALIAS_ONLY",
        "IMPORTED_IDENTITY_SHADOW",
    }:
        return persistence_state
    if continuity_ref == "unknown":
        return "CONTINUITY_UNKNOWN"
    return "PERSISTENT_CANONICAL_IDENTITY"
