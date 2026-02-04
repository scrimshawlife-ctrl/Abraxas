from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from webpanel.models import RunState


class ExecutionChecklist(BaseModel):
    kind: str = "ExecutionChecklist.v0"
    checklist_id: str
    run_id: str
    selected_action_id: str
    gates_required: List[str] = Field(default_factory=list)
    preconditions: List[str] = Field(default_factory=list)
    required_inputs: List[str] = Field(default_factory=list)
    produces: Dict[str, Any] = Field(default_factory=dict)
    stop_conditions: List[str] = Field(default_factory=list)
    notes: str


def _latest_compressed(run_state: RunState) -> Optional[Dict[str, Any]]:
    for result in reversed(run_state.step_results):
        if isinstance(result, dict) and result.get("kind") == "compress_signal_v0":
            return result
    return None


def build_checklist(run_state: RunState, selected_action: Dict[str, Any]) -> Dict[str, Any]:
    action_id = selected_action.get("action_id") or "unknown"
    checklist_id = f"chk_{run_state.run_id}_{action_id}"
    gates_required: List[str] = []
    if run_state.requires_human_confirmation and not run_state.human_ack:
        gates_required.append("ack_required")
    gates_required.append("quota_required")

    preconditions = [
        "deferral_active == true",
        "actions_remaining > 0",
    ]
    if selected_action.get("kind") == "request_missing_integrity":
        preconditions.append("provide invariance artifacts OR mark not_evaluated explicitly")
        preconditions.append("provide provenance refs if available")

    required_inputs: List[str] = []
    preview = selected_action.get("preview_effect") or {}
    if isinstance(preview, dict):
        produces = preview.get("produces")
        if produces:
            required_inputs.append(f"produce:{produces}")
        if "items_count" in preview:
            required_inputs.append(f"items_count:{preview.get('items_count')}")
        if "count" in preview:
            required_inputs.append(f"count:{preview.get('count')}")

    compressed = _latest_compressed(run_state)
    if compressed and isinstance(compressed.get("next_questions"), list):
        for question in compressed["next_questions"]:
            required_inputs.append(f"question:{question}")

    stop_conditions = [
        "pause when quota exhausted",
        "pause on drift escalation or invariance fail (if later implemented)",
    ]

    notes = "Selection only; execution requires explicit gating."

    checklist = ExecutionChecklist(
        checklist_id=checklist_id,
        run_id=run_state.run_id,
        selected_action_id=action_id,
        gates_required=gates_required,
        preconditions=preconditions,
        required_inputs=required_inputs,
        produces=preview if isinstance(preview, dict) else {},
        stop_conditions=stop_conditions,
        notes=notes,
    )
    return checklist.model_dump()
