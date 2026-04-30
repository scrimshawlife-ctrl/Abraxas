from __future__ import annotations


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def scoreable_resolution(item: dict) -> bool:
    return (
        item.get("status") == "RESOLVED"
        and item.get("predicted_outcome") in {"YES", "NO"}
        and item.get("resolved_outcome") in {"YES", "NO"}
    )
