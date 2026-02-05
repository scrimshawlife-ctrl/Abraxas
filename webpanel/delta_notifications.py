from __future__ import annotations

from typing import Dict, List, Optional

from webpanel.gates import compute_gate_stack
from webpanel.models import RunState
from webpanel.oracle_output import extract_oracle_output, oracle_hash_prefix

_PRIORITY = [
    "gate_changed",
    "drift_class_changed",
    "oracle_input_hash_changed",
    "risk_notes_changed",
]


def _drift_class(run: RunState) -> Optional[str]:
    oracle = extract_oracle_output(run)
    if oracle:
        provenance = oracle.get("provenance", {})
        stability = provenance.get("stability_status", {})
        drift = stability.get("drift_class")
        if isinstance(drift, str) and drift.strip():
            return drift.strip()
    report = getattr(run, "stability_report", None)
    if isinstance(report, dict):
        drift = report.get("drift_class")
        if isinstance(drift, str) and drift.strip():
            return drift.strip()
    return None


def _top_gate_code(run: RunState, current_policy_hash: str) -> Optional[str]:
    stack = compute_gate_stack(run, current_policy_hash)
    if not stack:
        return None
    code = stack[0].get("code")
    return str(code) if code else None


def _risk_notes(run: RunState) -> Optional[str]:
    context = getattr(run, "context", None)
    if context is None:
        return None
    risk_profile = getattr(context, "risk_profile", None)
    if risk_profile is None:
        return None
    notes = getattr(risk_profile, "risk_notes", None)
    if isinstance(notes, str) and notes.strip():
        return notes.strip()
    return None


def compute_delta_notifications(
    current: RunState,
    prev: Optional[RunState],
    current_policy_hash: str,
) -> Dict[str, object]:
    if prev is None:
        return {"schema": "delta_notify.v0", "has_changes": False, "changes": []}

    changes: Dict[str, str] = {}

    current_gate = _top_gate_code(current, current_policy_hash)
    prev_gate = _top_gate_code(prev, current_policy_hash)
    if current_gate != prev_gate:
        changes["gate_changed"] = f"Top gate changed: {prev_gate or 'none'} → {current_gate or 'none'}"

    current_drift = _drift_class(current) or "unknown"
    prev_drift = _drift_class(prev) or "unknown"
    if current_drift != prev_drift:
        changes["drift_class_changed"] = (
            f"Drift class changed: {prev_drift} → {current_drift}"
        )

    current_oracle = extract_oracle_output(current)
    prev_oracle = extract_oracle_output(prev)
    current_input_hash = oracle_hash_prefix(current_oracle, "input_hash") if current_oracle else None
    prev_input_hash = oracle_hash_prefix(prev_oracle, "input_hash") if prev_oracle else None
    if current_input_hash != prev_input_hash:
        changes["oracle_input_hash_changed"] = (
            f"Oracle input hash changed: {prev_input_hash or 'none'} → {current_input_hash or 'none'}"
        )

    current_notes = _risk_notes(current) or ""
    prev_notes = _risk_notes(prev) or ""
    if current_notes != prev_notes:
        changes["risk_notes_changed"] = "Risk notes changed."

    ordered: List[Dict[str, str]] = []
    for code in _PRIORITY:
        if code in changes:
            ordered.append({"code": code, "message": changes[code]})
    ordered = ordered[:6]

    return {
        "schema": "delta_notify.v0",
        "has_changes": bool(ordered),
        "changes": ordered,
    }
