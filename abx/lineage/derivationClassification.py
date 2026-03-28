from __future__ import annotations


def classify_derivation(*, provenance_state: str, transform_chain: str) -> str:
    if provenance_state == "NOT_COMPUTABLE":
        return "NOT_COMPUTABLE"
    if not transform_chain:
        return "DERIVATION_UNKNOWN"
    if provenance_state == "PROVENANCE_BROKEN":
        return "STALE_DERIVED_STATE"
    if provenance_state == "PROVENANCE_STALE":
        return "STALE_DERIVED_STATE"
    return "DERIVATION_VALID"
