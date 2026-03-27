from __future__ import annotations

from typing import Any, Dict, List, Optional

from .gates import compute_gate_stack
from .oracle_output import extract_oracle_output

PROFILE_LABELS = {
    "read_only_audit": "Read-only Audit",
    "deep_review": "Deep Review",
    "guided_execute_2": "Guided Execute (2)",
}


def _oracle_flags(oracle: Optional[Dict[str, Any]]) -> List[str]:
    if not oracle:
        return []
    flags = oracle.get("flags")
    if isinstance(flags, list):
        return [str(flag) for flag in flags if str(flag).strip()]
    if isinstance(flags, dict):
        return [str(key) for key, value in flags.items() if value]
    return []


def _oracle_drift_class(oracle: Optional[Dict[str, Any]]) -> str:
    if not oracle:
        return "unknown"
    provenance = oracle.get("provenance")
    if not isinstance(provenance, dict):
        return "unknown"
    stability_status = provenance.get("stability_status")
    if not isinstance(stability_status, dict):
        return "unknown"
    drift = stability_status.get("drift_class")
    if isinstance(drift, str) and drift.strip():
        return drift.strip()
    return "unknown"


def _evidence_state(oracle: Optional[Dict[str, Any]]) -> str:
    if not oracle:
        return "none"
    evidence = oracle.get("evidence")
    count = len(evidence) if isinstance(evidence, list) else 0
    if count == 0:
        return "none"
    if count <= 3:
        return "limited"
    return "present"


def _latest_proposals(run: Any) -> Optional[List[Dict[str, Any]]]:
    last = getattr(run, "last_step_result", None)
    if isinstance(last, dict) and last.get("kind") == "propose_actions_v0":
        actions = last.get("actions")
        return actions if isinstance(actions, list) else None
    for result in reversed(getattr(run, "step_results", []) or []):
        if isinstance(result, dict) and result.get("kind") == "propose_actions_v0":
            actions = result.get("actions")
            return actions if isinstance(actions, list) else None
    return None


def recommend_profile(
    run: Any,
    prev: Optional[Any],
    current_policy_hash: str,
) -> Dict[str, Any]:
    gate_stack = compute_gate_stack(run, current_policy_hash)
    gate_codes = [gate.get("code", "") for gate in gate_stack if gate.get("code")]
    top_gate = gate_codes[0] if gate_codes else None

    oracle = extract_oracle_output(run)
    drift_class = _oracle_drift_class(oracle)
    oracle_present = bool(oracle)
    oracle_flags = _oracle_flags(oracle)
    evidence_state = _evidence_state(oracle)

    reasons: List[str] = []
    if top_gate in {"policy_ack_required", "session_exhausted", "session_inactive"}:
        if top_gate:
            reasons.append(f"gate:{top_gate}")
        recommendation = "read_only_audit"
        confidence = "high"
    elif drift_class not in {"none", "unknown"} or "stabilization_required" in oracle_flags:
        if drift_class not in {"none", "unknown"}:
            reasons.append(f"drift:{drift_class}")
        if "stabilization_required" in oracle_flags:
            reasons.append("flag:stabilization_required")
        recommendation = "deep_review"
        confidence = "high"
    else:
        proposals = _latest_proposals(run)
        has_proposals = bool(proposals)
        agency_enabled = bool(getattr(run, "agency_enabled", False))
        session_active = bool(getattr(run, "session_active", False))
        if has_proposals and (agency_enabled or session_active):
            reasons.append("proposals_available")
            if agency_enabled:
                reasons.append("agency_enabled")
            elif session_active:
                reasons.append("session_active")
            recommendation = "guided_execute_2"
            confidence = "medium"
        else:
            reasons.append("default")
            recommendation = "read_only_audit"
            confidence = "low"

    return {
        "schema": "profile_recommendation.v0",
        "recommended_profile_id": recommendation,
        "reasons": reasons[:5],
        "confidence": confidence,
        "provenance": {
            "gate_codes": gate_codes,
            "drift_class": drift_class,
            "oracle_present": oracle_present,
            "evidence_state": evidence_state,
        },
    }
