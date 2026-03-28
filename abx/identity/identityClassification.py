from __future__ import annotations


def classify_identity_resolution(*, resolution_state: str, canonical_entity: str) -> str:
    if resolution_state in {"BLOCKED", "NOT_COMPUTABLE", "REFERENTIAL_MISMATCH", "REFERENCE_AMBIGUOUS", "UNRESOLVED_REFERENCE"}:
        return resolution_state
    if resolution_state in {
        "CANONICAL_IDENTITY_RESOLVED",
        "ALIAS_RESOLVED",
        "FOREIGN_REFERENCE_RESOLVED",
        "TRANSIENT_HANDLE_RESOLVED",
    }:
        return resolution_state
    if canonical_entity == "unknown":
        return "UNRESOLVED_REFERENCE"
    return "CANONICAL_IDENTITY_RESOLVED"
