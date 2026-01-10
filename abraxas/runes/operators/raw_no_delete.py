"""ABX-RAW_NO_DELETE rune operator."""

from __future__ import annotations

from typing import Any, Dict, List


def apply_raw_no_delete(
    *,
    steps: List[Dict[str, Any]],
    allow_raw_delete: bool,
    strict_execution: bool = True,
) -> Dict[str, Any]:
    if allow_raw_delete:
        return {"allowed": True, "raw_deletes": 0}
    raw_deletes = [step for step in steps if step.get("artifact_type") == "raw"]
    if raw_deletes:
        raise ValueError("Raw deletion not permitted without explicit flag.")
    return {"allowed": True, "raw_deletes": len(raw_deletes)}
