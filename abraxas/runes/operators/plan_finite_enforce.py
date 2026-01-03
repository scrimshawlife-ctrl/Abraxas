"""ABX-PLAN_FINITE_ENFORCE rune operator."""

from __future__ import annotations

from typing import Any, Dict, List


def apply_plan_finite_enforce(
    *,
    steps: List[Dict[str, Any]],
    strict_execution: bool = True,
) -> Dict[str, Any]:
    if steps is None:
        raise ValueError("Plan steps are required")
    if len(steps) != len({step.get("step_id") for step in steps}):
        raise ValueError("Plan steps must have unique step_id values")
    return {
        "finite": True,
        "step_count": len(steps),
    }
