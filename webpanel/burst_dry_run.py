from __future__ import annotations

from typing import Any, Dict, List

from .policy import compute_policy_hash, get_policy_snapshot
from .policy_gate import policy_ack_required


def _hash_prefix(value: str | None, length: int = 8) -> str | None:
    if not value:
        return None
    return value[:length]


def _session_remaining(run: Any) -> int:
    if not bool(getattr(run, "session_active", False)):
        return 0
    max_steps = int(getattr(run, "session_max_steps", 0) or 0)
    used = int(getattr(run, "session_steps_used", 0) or 0)
    remaining = max(0, max_steps - used)
    return remaining


def _build_steps(run: Any, effective_n: int) -> List[Dict[str, Any]]:
    runplan = getattr(run, "runplan", None)
    if not runplan or not getattr(runplan, "steps", None):
        return []
    steps = []
    start_index = int(getattr(run, "current_step_index", 0) or 0)
    for index in range(start_index, min(start_index + effective_n, len(runplan.steps))):
        step = runplan.steps[index]
        notes: List[str] = [f"step_id:{step.step_id}", f"produces:{step.produces}"]
        if getattr(step, "requires_human_confirmation", False):
            notes.append("requires_human_confirmation")
        entry: Dict[str, Any] = {
            "index": index,
            "title": step.kind,
            "would_consume": True,
            "notes": notes,
        }
        if step.kind == "select_action_v0":
            action_id = getattr(run, "selected_action_id", None)
            if action_id:
                entry["action_id"] = action_id
        steps.append(entry)
    return steps


def simulate_burst(run: Any, n: int) -> Dict[str, Any]:
    current_hash = compute_policy_hash(get_policy_snapshot())
    blockers: List[str] = []
    if policy_ack_required(run, current_hash):
        blockers.append("policy_ack_required")

    session_active = bool(getattr(run, "session_active", False))
    max_steps = int(getattr(run, "session_max_steps", 0) or 0)
    used = int(getattr(run, "session_steps_used", 0) or 0)
    if max_steps > 0 and used >= max_steps:
        blockers.append("session_exhausted")
    if not session_active:
        blockers.append("session_inactive")

    if not bool(getattr(run, "agency_enabled", False)):
        blockers.append("agency_off")

    requested_n = max(0, int(n))
    session_remaining = _session_remaining(run)
    effective_n = min(requested_n, session_remaining, 5)

    steps: List[Dict[str, Any]] = []
    if not blockers:
        steps = _build_steps(run, effective_n)
        if not steps and effective_n > 0:
            steps = [
                {
                    "index": int(getattr(run, "current_step_index", 0) or 0),
                    "title": "unknown_step",
                    "would_consume": False,
                    "notes": ["metadata unavailable"],
                }
            ]

    return {
        "schema": "burst_preview.v0",
        "run_id": getattr(run, "run_id", ""),
        "requested_n": requested_n,
        "effective_n": effective_n,
        "steps": steps[:5],
        "blockers": blockers[:5],
        "provenance": {
            "policy_hash_prefix": _hash_prefix(current_hash),
            "session_remaining": session_remaining,
            "agency_mode": getattr(run, "agency_mode", "off"),
        },
    }
