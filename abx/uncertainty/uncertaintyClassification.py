from __future__ import annotations


def classify_uncertainty(*, uncertainty_level: str, downgrade_required: str) -> str:
    if uncertainty_level not in {"LOW", "MODERATE", "HIGH", "MIXED", "UNKNOWN"}:
        return "NOT_COMPUTABLE"
    if downgrade_required == "YES":
        return "OUTPUT_DOWNGRADE_REQUIRED"
    return f"UNCERTAINTY_{uncertainty_level}"
