"""ABX-DETERMINISTIC_COMMIT_ORDER rune operator."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def apply_deterministic_commit_order(
    *,
    results: List[Dict[str, Any]],
    strict_execution: bool = True,
) -> Dict[str, Any]:
    ordered = sorted(results, key=_sort_key)
    if results != ordered:
        raise ValueError("Commit results are not deterministically ordered.")
    return {"ordered": True, "count": len(results)}


def _sort_key(result: Dict[str, Any]) -> Tuple[Any, ...]:
    key = result.get("key")
    if isinstance(key, list):
        return tuple(key)
    if isinstance(key, tuple):
        return key
    return (str(key),)
