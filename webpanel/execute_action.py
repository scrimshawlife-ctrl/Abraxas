from __future__ import annotations

from typing import Any, Dict, List, Tuple, Optional

from webpanel.models import RunState


def _find_latest(run_state: RunState, kind: str) -> Optional[Dict[str, Any]]:
    for result in reversed(run_state.step_results):
        if isinstance(result, dict) and result.get("kind") == kind:
            return result
    return None


def _truncate(items: List[Any], limit: int) -> List[Any]:
    return list(items[:limit])


def next_micro_step(run_state: RunState) -> Dict[str, Any]:
    selected_action = run_state.selected_action or {}
    action_id = selected_action.get("action_id") or "unknown"
    action_kind = selected_action.get("kind")
    progress = run_state.selected_action_progress or {
        "kind": "SelectedActionProgress.v0",
        "action_id": action_id,
        "phase": 0,
        "completed": False,
    }
    phase = int(progress.get("phase", 0))

    compressed = _find_latest(run_state, "compress_signal_v0")
    extracted = _find_latest(run_state, "extract_structure_v0")
    if action_kind in ("request_missing_integrity", "generate_question_set") and compressed is None:
        return {
            "micro_step_id": f"ms_{action_id}_{phase}",
            "phase": phase,
            "completed": False,
            "produces": {"artifact_kind": "ExecutionError.v0", "error": "missing_compress_signal_v0"},
        }
    if action_kind == "request_missing_integrity" and extracted is None:
        return {
            "micro_step_id": f"ms_{action_id}_{phase}",
            "phase": phase,
            "completed": False,
            "produces": {"artifact_kind": "ExecutionError.v0", "error": "missing_extract_structure_v0"},
        }

    if action_kind == "request_missing_integrity":
        if phase == 0:
            unknowns = extracted.get("unknowns", []) if extracted else []
            refs = extracted.get("evidence_refs", []) if extracted else []
            items = [
                {"id": "inv_eval", "desc": "Provide invariance artifacts or mark not_evaluated"},
                {"id": "prov_refs", "desc": "Provide provenance refs/ids if available"},
            ]
            if run_state.signal.drift_flags:
                items.append({"id": "drift_notes", "desc": "Explain drift flags source (if present)"})
            return {
                "micro_step_id": f"ms_{action_id}_{phase}",
                "phase": phase,
                "completed": False,
                "produces": {
                    "artifact_kind": "IntegrityRequest.v0",
                    "items": items,
                    "unknown_paths": _truncate([u.get("path") for u in unknowns if isinstance(u, dict)], 10),
                    "evidence_refs": _truncate([r.get("path") for r in refs if isinstance(r, dict)], 10),
                },
            }
        if phase == 1:
            if run_state.requires_human_confirmation and run_state.human_ack is None:
                return {
                    "micro_step_id": f"ms_{action_id}_{phase}",
                    "phase": phase,
                    "completed": False,
                    "produces": {"artifact_kind": "AckReminder.v0", "note": "Awaiting explicit ACK."},
                }
            return {
                "micro_step_id": f"ms_{action_id}_{phase}",
                "phase": phase,
                "completed": False,
                "produces": {"artifact_kind": "AckReminder.v0", "note": "ACK already satisfied."},
            }
        return {
            "micro_step_id": f"ms_{action_id}_{phase}",
            "phase": phase,
            "completed": True,
            "produces": {"artifact_kind": "ActionComplete.v0"},
        }

    if action_kind == "generate_question_set":
        if phase == 0:
            questions = compressed.get("next_questions", []) if compressed else []
            return {
                "micro_step_id": f"ms_{action_id}_{phase}",
                "phase": phase,
                "completed": False,
                "produces": {
                    "artifact_kind": "QuestionSet.v0",
                    "questions": _truncate(list(questions), 6),
                },
            }
        return {
            "micro_step_id": f"ms_{action_id}_{phase}",
            "phase": phase,
            "completed": True,
            "produces": {"artifact_kind": "ActionComplete.v0"},
        }

    if action_kind == "enter_observe_only":
        if phase == 0:
            return {
                "micro_step_id": f"ms_{action_id}_{phase}",
                "phase": phase,
                "completed": False,
                "produces": {
                    "artifact_kind": "ObserveOnly.v0",
                    "note": "Execution lane is observe-only; no external actions.",
                },
            }
        return {
            "micro_step_id": f"ms_{action_id}_{phase}",
            "phase": phase,
            "completed": True,
            "produces": {"artifact_kind": "ActionComplete.v0"},
        }

    return {
        "micro_step_id": f"ms_{action_id}_{phase}",
        "phase": phase,
        "completed": False,
        "produces": {"artifact_kind": "ExecutionError.v0", "error": "unknown_action_kind"},
    }


def execute_one(run_state: RunState) -> Tuple[RunState, Dict[str, Any]]:
    selected_action = run_state.selected_action or {}
    action_id = selected_action.get("action_id") or "unknown"
    action_kind = selected_action.get("kind") or "unknown"

    if run_state.selected_action_progress is None:
        run_state.selected_action_progress = {
            "kind": "SelectedActionProgress.v0",
            "action_id": action_id,
            "phase": 0,
            "completed": False,
        }

    micro = next_micro_step(run_state)
    produces = micro.get("produces", {})
    if isinstance(produces, dict) and produces.get("artifact_kind") == "ExecutionError.v0":
        completed = False
        phase_after = run_state.selected_action_progress.get("phase", 0)
    else:
        phase_after = int(run_state.selected_action_progress.get("phase", 0)) + 1
        completed = bool(micro.get("completed", False))
        run_state.selected_action_progress["phase"] = phase_after
        run_state.selected_action_progress["completed"] = completed

    result = {
        "kind": "execute_selected_action_v0",
        "action_id": action_id,
        "action_kind": action_kind,
        "micro_step_id": micro.get("micro_step_id"),
        "phase_after": phase_after,
        "completed": completed,
        "produces": produces,
    }
    run_state.last_execution_result = result
    return run_state, result
