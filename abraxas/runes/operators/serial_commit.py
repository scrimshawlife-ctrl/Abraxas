"""ABX-SERIAL_COMMIT rune operator."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def apply_serial_commit(
    *,
    results: List[Dict[str, Any]],
    strict_execution: bool = True,
) -> Dict[str, Any]:
    ordered = sorted(results, key=_sort_key)
    return {"committed": ordered, "count": len(ordered)}


def _sort_key(result: Dict[str, Any]) -> Tuple[Any, ...]:
    key = result.get("key")
    if isinstance(key, list):
        return tuple(key)
    if isinstance(key, tuple):
        return key
    return (str(key),)
