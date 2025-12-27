from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


ORDER = {"days": 0, "weeks": 1, "months": 2, "years": 3}


def _normalize(horizon: str) -> str:
    h = str(horizon or "").strip().lower()
    if h.startswith("years"):
        return "years"
    if h in ORDER:
        return h
    return "years"


def compare_horizon(horizon: str, max_horizon: str) -> int:
    """Return +1 if horizon exceeds max_horizon, 0 if equal, -1 if below."""
    a = ORDER.get(_normalize(horizon), 99)
    b = ORDER.get(_normalize(max_horizon), 99)
    if a > b:
        return 1
    if a == b:
        return 0
    return -1


def enforce_horizon_policy(
    *,
    horizon: str,
    gate: Dict[str, Any],
    emit_shadow: bool = True,
) -> Tuple[List[str], Optional[str]]:
    """
    Return flags to apply to a prediction and optional shadow horizon.
    Shadow horizon is emitted when the prediction exceeds gate horizon_max.
    """
    flags: List[str] = []
    max_horizon = str(gate.get("horizon_max") or "years")
    if compare_horizon(horizon, max_horizon) > 0:
        flags.append("HORIZON_EXCEEDS_GATE")
        if emit_shadow:
            return flags, max_horizon
    return flags, None
