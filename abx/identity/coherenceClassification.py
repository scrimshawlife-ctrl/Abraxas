from __future__ import annotations


def classify_coherence(*, coherence_state: str, downstream_state: str) -> str:
    if coherence_state in {"NOT_COMPUTABLE", "BLOCKED", "DUPLICATE_ENTITY_CONFIRMED", "MERGE_ILLEGITIMATE", "SPLIT_ILLEGITIMATE"}:
        return coherence_state
    if coherence_state in {
        "REFERENTIALLY_COHERENT",
        "ALIAS_ACTIVE_COHERENT",
        "MERGE_ACTIVE_COHERENT",
        "SPLIT_ACTIVE_COHERENT",
        "DUPLICATE_ENTITY_SUSPECTED",
    }:
        return coherence_state
    if downstream_state == "DOWNSTREAM_CONFLICT":
        return "DUPLICATE_ENTITY_SUSPECTED"
    return "REFERENTIALLY_COHERENT"
