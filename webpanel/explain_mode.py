from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from webpanel.continuity import build_continuity_report
from webpanel.gates import compute_gate_stack
from webpanel.models import RunState
from webpanel.oracle_output import extract_oracle_output, indicator_entries, flag_entries, oracle_hash_prefix
from webpanel.preference_kernel import normalize_prefs


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _stable_str(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return str(value)


def _top_indicators(oracle: Dict[str, Any], limit: int = 5) -> List[str]:
    flattened = indicator_entries(oracle.get("indicators"))
    items = [f"{path}={_stable_str(flattened[path])}" for path in sorted(flattened.keys())]
    return items[:limit]


def _top_flags(oracle: Dict[str, Any], limit: int = 5) -> List[str]:
    items = flag_entries(oracle.get("flags"))
    return sorted(items)[:limit]


def _oracle_stability_class(oracle: Optional[Dict[str, Any]], run: RunState) -> Optional[str]:
    if oracle:
        provenance = _safe_dict(oracle.get("provenance"))
        stability = _safe_dict(provenance.get("stability_status"))
        drift_class = stability.get("drift_class")
        if isinstance(drift_class, str) and drift_class.strip():
            return drift_class.strip()
    report = getattr(run, "stability_report", None)
    if isinstance(report, dict):
        drift_class = report.get("drift_class")
        if isinstance(drift_class, str) and drift_class.strip():
            return drift_class.strip()
    return None


def _select_next_action(run: RunState) -> Optional[Dict[str, Any]]:
    if isinstance(run.selected_action, dict):
        return run.selected_action
    if run.last_step_result and isinstance(run.last_step_result, dict):
        if run.last_step_result.get("kind") == "propose_actions_v0":
            actions = _safe_list(run.last_step_result.get("actions"))
            ordered = sorted(
                [action for action in actions if isinstance(action, dict)],
                key=lambda item: str(item.get("action_id") or item.get("title") or ""),
            )
            if ordered:
                return ordered[0]
    return None


def build_run_brief(
    run: RunState,
    prev: Optional[RunState],
    current_policy_hash: str,
) -> Dict[str, Any]:
    gate_stack = compute_gate_stack(run, current_policy_hash)
    top_gate = gate_stack[0] if gate_stack else None

    session_max = int(getattr(run, "session_max_steps", 0) or 0)
    session_used = int(getattr(run, "session_steps_used", 0) or 0)
    session_remaining = max(session_max - session_used, 0) if session_max > 0 else None
    session_section = None
    if session_max or getattr(run, "session_active", False):
        session_section = {
            "active": bool(getattr(run, "session_active", False)),
            "used": session_used,
            "max": session_max,
            "remaining": session_remaining,
        }

    continuity_section = None
    if prev is not None:
        continuity = build_continuity_report(run, prev, current_policy_hash)
        summary_lines = _safe_list(continuity.get("summary_lines"))[:3]
        continuity_section = {"summary_lines": summary_lines}

    oracle = extract_oracle_output(run)
    oracle_section = None
    oracle_input_hash_prefix = None
    if oracle:
        oracle_input_hash_prefix = oracle_hash_prefix(oracle, "input_hash")
        oracle_section = {
            "tier": oracle.get("tier"),
            "lane": oracle.get("lane"),
            "top_indicators": _top_indicators(oracle),
            "flags": _top_flags(oracle),
            "input_hash_prefix": oracle_input_hash_prefix,
            "stability_class": _oracle_stability_class(oracle, run),
        }

    next_action = _select_next_action(run)
    next_action_section = None
    if next_action:
        rationale = _safe_list(next_action.get("rationale"))
        risk_flags = _safe_list(next_action.get("risk_flags"))
        next_action_section = {
            "id": next_action.get("action_id"),
            "title": next_action.get("title") or next_action.get("kind"),
            "top_rationale": [str(item) for item in rationale][:3],
            "risk_flags": [str(item) for item in risk_flags][:3],
        }

    prefs_section = None
    if getattr(run, "prefs", None):
        prefs = normalize_prefs(run.prefs)
        prefs_section = {
            "verbosity": prefs.get("verbosity"),
            "focus": prefs.get("focus"),
            "risk_tolerance": prefs.get("risk_tolerance"),
            "show": sorted(_safe_list(prefs.get("show"))),
            "hide": sorted(_safe_list(prefs.get("hide"))),
        }

    brief_lines: List[str] = []
    if top_gate:
        brief_lines.append(f"Gate: {top_gate.get('code')} · {top_gate.get('message')}")
    if run.pause_required:
        reason = run.pause_reason or "paused"
        brief_lines.append(f"Pause: {reason}")
    if oracle_section:
        brief_lines.append(
            f"Oracle: {oracle_section.get('tier')} / {oracle_section.get('lane')}"
        )
        if oracle_section.get("top_indicators"):
            brief_lines.append(
                "Indicators: " + ", ".join(oracle_section["top_indicators"])
            )
    if session_section:
        brief_lines.append(
            f"Session: {session_section['used']}/{session_section['max']} used"
        )
    if continuity_section and continuity_section.get("summary_lines"):
        brief_lines.append(
            "Continuity: " + "; ".join(continuity_section["summary_lines"])
        )
    if next_action_section:
        brief_lines.append(
            "Next action: " + _stable_str(next_action_section.get("title") or "n/a")
        )
    if prefs_section:
        brief_lines.append(
            "Pins: "
            + _stable_str(prefs_section.get("verbosity"))
            + " / "
            + _stable_str(prefs_section.get("risk_tolerance"))
        )

    brief_lines = brief_lines[:12]

    provenance = {
        "policy_hash_prefix": (current_policy_hash or "")[:8],
        "oracle_input_hash_prefix": oracle_input_hash_prefix,
        "prev_run_id": getattr(prev, "run_id", None) if prev else None,
    }

    return {
        "schema": "run_brief.v1",
        "run_id": run.run_id,
        "brief_lines": brief_lines,
        "sections": {
            "gate": {
                "code": top_gate.get("code"),
                "message": top_gate.get("message"),
                "remedy": top_gate.get("remedy"),
            }
            if top_gate
            else None,
            "session": session_section,
            "continuity": continuity_section,
            "oracle": oracle_section,
            "next_action": next_action_section,
            "pins": prefs_section,
        },
        "provenance": provenance,
    }
