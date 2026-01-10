"""ABX-NO_TIME_BRANCHING rune operator."""

from __future__ import annotations

from typing import Any, Dict


def apply_no_time_branching(
    *,
    payload: Dict[str, Any],
    strict_execution: bool = True,
) -> Dict[str, Any]:
    forbidden = _find_time_branching(payload)
    if forbidden:
        raise ValueError("Time-based branching keys detected: " + ", ".join(sorted(forbidden)))
    return {"ok": True, "checked_keys": len(payload)}


def _find_time_branching(payload: Dict[str, Any]) -> set[str]:
    forbidden = set()
    for key in payload.keys():
        lower = str(key).lower()
        if any(term in lower for term in ("elapsed", "duration", "timeout")):
            forbidden.add(str(key))
    return forbidden
