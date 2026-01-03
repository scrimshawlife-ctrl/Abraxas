"""ABX-INVARIANCE_CHECK rune operator."""

from __future__ import annotations

from typing import Any, Dict, List


def apply_invariance_check(*, hashes: List[str], strict_execution: bool = True) -> Dict[str, Any]:
    if len(set(hashes)) > 1:
        raise ValueError("Determinism violation: output hashes differ across repetitions.")
    return {"invariant": True, "count": len(hashes)}
