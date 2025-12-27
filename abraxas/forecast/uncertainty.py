from __future__ import annotations

from typing import Any


H_MUL = {
    "days": 1.00,
    "weeks": 1.05,
    "months": 1.15,
    "years": 1.35,
    "unknown": 1.10,
}


def horizon_uncertainty_multiplier(horizon: Any) -> float:
    s = str(horizon or "").strip().lower()
    if s in ("day", "days"):
        return 1.00
    if s in ("week", "weeks"):
        return 1.05
    if s in ("month", "months"):
        return 1.15
    if s in ("year", "years"):
        return 1.35
    return float(H_MUL.get(s, 1.10))
