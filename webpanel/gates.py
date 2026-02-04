from __future__ import annotations

from typing import Any, Dict, List, Optional

from webpanel.oracle_output import extract_oracle_output
from webpanel.policy_gate import policy_ack_required


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _drift_class_from_oracle(oracle: Dict[str, Any]) -> Optional[str]:
    provenance = _safe_dict(oracle.get("provenance"))
    stability = _safe_dict(provenance.get("stability_status"))
    drift = stability.get("drift_class")
    if isinstance(drift, str) and drift.strip():
        return drift.strip()
    return None


def _drift_class_from_stability(run: Any) -> Optional[str]:
    report = getattr(run, "stability_report", None)
    if not isinstance(report, dict):
        return None
    drift = report.get("drift_class")
    if isinstance(drift, str) and drift.strip():
        return drift.strip()
    return None


def _effective_drift_class(run: Any) -> str:
    oracle = extract_oracle_output(run)
    if oracle:
        drift = _drift_class_from_oracle(oracle)
        if drift:
            return drift
    drift = _drift_class_from_stability(run)
    return drift or "unknown"


def compute_gate_stack(run: Any, current_policy_hash: Optional[str]) -> List[Dict[str, Any]]:
    gates: List[Dict[str, Any]] = []

    if policy_ack_required(run, current_policy_hash):
        gates.append(
            {
                "code": "policy_ack_required",
                "severity": "block",
                "message": "Policy changed since ingest.",
                "remedy": "ACK policy change.",
                "priority": 1,
            }
        )

    max_steps = int(getattr(run, "session_max_steps", 0) or 0)
    used_steps = int(getattr(run, "session_steps_used", 0) or 0)
    if max_steps > 0 and used_steps >= max_steps:
        gates.append(
            {
                "code": "session_exhausted",
                "severity": "block",
                "message": "Session budget exhausted.",
                "remedy": "Start a new session.",
                "priority": 2,
            }
        )
    if not bool(getattr(run, "session_active", False)):
        gates.append(
            {
                "code": "session_inactive",
                "severity": "block",
                "message": "Session inactive.",
                "remedy": "Start a session.",
                "priority": 3,
            }
        )

    drift_class = _effective_drift_class(run)
    if drift_class not in {"none", "unknown"}:
        gates.append(
            {
                "code": "drift_blocked",
                "severity": "block",
                "message": f"Drift class: {drift_class}.",
                "remedy": "Re-run stabilization.",
                "priority": 4,
            }
        )

    signal = getattr(run, "signal", None)
    provenance_status = getattr(signal, "provenance_status", None)
    if provenance_status in {"missing", "partial"}:
        gates.append(
            {
                "code": "provenance_missing",
                "severity": "warn",
                "message": f"Provenance status: {provenance_status}.",
                "remedy": "Provide provenance artifacts.",
                "priority": 5,
            }
        )

    invariance_status = getattr(signal, "invariance_status", None)
    if invariance_status == "fail":
        gates.append(
            {
                "code": "invariance_failed",
                "severity": "warn",
                "message": "Invariance check failed.",
                "remedy": "Provide invariance artifacts.",
                "priority": 5,
            }
        )

    actions_remaining = getattr(run, "actions_remaining", None)
    if actions_remaining is not None and actions_remaining <= 0:
        gates.append(
            {
                "code": "quota_exhausted",
                "severity": "block",
                "message": "Deferral quota exhausted.",
                "remedy": "Start a new deferral session.",
                "priority": 6,
            }
        )

    gates = sorted(gates, key=lambda g: (g.get("priority", 99), g.get("code", "")))
    return gates
