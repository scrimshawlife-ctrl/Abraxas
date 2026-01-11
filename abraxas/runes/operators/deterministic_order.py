"""ABX-DETERMINISTIC_ORDER rune operator."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def apply_deterministic_order(
    *,
    steps: List[Dict[str, Any]],
    strict_execution: bool = True,
) -> Dict[str, Any]:
    ordered = sorted(steps, key=_sort_key)
    if steps != ordered:
        raise ValueError("Plan steps are not deterministically ordered.")
    return {"ordered": True, "count": len(steps)}


def _sort_key(step: Dict[str, Any]) -> Tuple[str, str, int]:
    return (
        step.get("action", ""),
        step.get("path", ""),
        int(step.get("bytes_expected") or 0),
    )
