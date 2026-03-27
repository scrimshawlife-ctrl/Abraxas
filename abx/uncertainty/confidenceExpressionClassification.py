from __future__ import annotations


def classify_confidence_expression(expression_mode: str) -> str:
    allowed = {
        "NUMERIC",
        "CATEGORICAL",
        "INTERVAL",
        "QUALITATIVE",
        "SUPPRESSED",
        "ABSTAIN_FROM_CONFIDENCE",
        "NOT_COMPUTABLE",
    }
    return expression_mode if expression_mode in allowed else "NOT_COMPUTABLE"
