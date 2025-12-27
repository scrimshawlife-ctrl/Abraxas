from __future__ import annotations

from typing import Any


def horizon_bucket(horizon: Any) -> str:
    """
    Normalize horizons into stable bins.
    """
    s = str(horizon or "").strip().lower()
    if s in ("day", "days"):
        return "days"
    if s in ("week", "weeks"):
        return "weeks"
    if s in ("month", "months"):
        return "months"
    if s in ("year", "years"):
        return "years"
    return "unknown"
