from __future__ import annotations


def resolve_prediction(pred: dict, outcome: dict | None) -> str:
    if outcome is None:
        return "UNRESOLVED"
    predicted = pred.get("predicted_outcome", "UNKNOWN")
    resolved = outcome.get("resolved_outcome", "NOT_COMPUTABLE")

    if predicted == "UNKNOWN" or resolved == "NOT_COMPUTABLE":
        return "NOT_COMPUTABLE"
    if predicted == "PARTIAL" or resolved == "PARTIAL":
        return "PARTIAL"
    if predicted == resolved:
        return "HIT"
    return "MISS"
