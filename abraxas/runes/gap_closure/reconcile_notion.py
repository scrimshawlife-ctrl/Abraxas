from __future__ import annotations


def sanitize_promotion_recommendation(value: str | None) -> str:
    recommendation = str(value or "HOLD").upper()
    if recommendation == "PROMOTE":
        return "HOLD"
    return recommendation
