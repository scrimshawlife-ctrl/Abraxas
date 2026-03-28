from __future__ import annotations


def classify_promotion(*, promotion_state: str) -> str:
    if promotion_state == "NOT_COMPUTABLE":
        return "NOT_COMPUTABLE"
    return promotion_state
