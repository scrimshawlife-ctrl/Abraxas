from __future__ import annotations


def classify_tradeoff(*, tradeoff_state: str, sacrifice_state: str, resolution_state: str) -> str:
    if "NOT_COMPUTABLE" in {tradeoff_state, sacrifice_state, resolution_state}:
        return "NOT_COMPUTABLE"
    if tradeoff_state == "TRADEOFF_HIDDEN" or sacrifice_state == "HIDDEN_SACRIFICE_RISK":
        return "TRADEOFF_HIDDEN"
    if resolution_state == "DOMINATION_SELECTED":
        return "DOMINATION_SELECTED"
    if resolution_state == "COMPROMISE_SELECTED":
        return "COMPROMISE_SELECTED"
    if sacrifice_state == "SACRIFICE_ACKNOWLEDGED":
        return "SACRIFICE_ACKNOWLEDGED"
    return "TRADEOFF_LEGIBLE"
