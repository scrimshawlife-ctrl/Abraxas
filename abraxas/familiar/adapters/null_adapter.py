from __future__ import annotations

from typing import Any, Dict, List


class NullAdapter:
    """
    Deterministic no-op adapter used when ERS integration is absent.
    """

    def execute(self, run_plan: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        step_ids: List[str] = [step["step_id"] for step in run_plan.get("steps", [])]
        step_results = [{"step_id": step_id, "status": "skipped"} for step_id in step_ids]
        return {
            "schema_version": "v0",
            "outputs": {
                "executed_steps": step_ids,
            },
            "step_results": step_results,
        }
