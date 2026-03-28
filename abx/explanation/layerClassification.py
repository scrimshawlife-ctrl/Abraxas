from __future__ import annotations


def classify_layer(*, layer_state: str, boundary_state: str) -> str:
    if boundary_state == "NOT_COMPUTABLE":
        return "NOT_COMPUTABLE"
    if boundary_state in {"BOUNDARY_EXCEEDED", "BOUNDARY_AMBIGUOUS"}:
        return boundary_state
    if layer_state in {
        "OBSERVED_LAYER",
        "INFERRED_LAYER",
        "INTERPRETIVE_LAYER",
        "SPECULATIVE_LAYER",
        "CAUSAL_CLAIM_LAYER",
    }:
        return layer_state
    return "INFERRED_LAYER"
