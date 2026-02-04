from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple


_STEP_STATE: Dict[str, int] = {}


def _load_external_core() -> Tuple[Optional[Any], Optional[Any]]:
    try:
        from abraxas.familiar.webpanel_bridge import core_ingest, core_step
    except Exception:
        return None, None
    return core_ingest, core_step


_EXTERNAL_CORE_INGEST, _EXTERNAL_CORE_STEP = _load_external_core()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def _safe_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _requires_ack(packet: Dict[str, Any]) -> bool:
    invariance_status = packet.get("invariance_status")
    provenance_status = packet.get("provenance_status")
    drift_flags = _safe_list(packet.get("drift_flags"))
    return (
        invariance_status == "fail"
        or provenance_status in ("partial", "missing")
        or len(drift_flags) > 0
    )


def _interaction_mode(packet: Dict[str, Any], requires_ack: bool) -> str:
    lane = packet.get("lane")
    if lane == "shadow":
        return "observe_only"
    if requires_ack:
        return "deliberate"
    return "present_options"


def _execution_lanes(packet: Dict[str, Any]) -> list:
    lane = packet.get("lane")
    return ["shadow"] if lane == "shadow" else ["canon", "shadow"]


def _unknowns(packet: Dict[str, Any]) -> list:
    unknowns = []
    regions = _safe_list(packet.get("not_computable_regions"))
    for region in regions:
        if isinstance(region, dict):
            unknowns.append(
                {
                    "region_id": region.get("region_id"),
                    "reason_code": region.get("reason_code"),
                }
            )
    return unknowns


def _try_kernel_result(packet: Dict[str, Any], run_id: str) -> Optional[Dict[str, Any]]:
    try:
        from abraxas.familiar.kernel.familiar_kernel import FamiliarKernel
    except Exception:
        return None

    try:
        kernel = FamiliarKernel()
        run_request = {
            "schema_version": "v0",
            "run_id": run_id,
            "inputs": {"signal_id": packet.get("signal_id", "")},
            "required_inputs": [],
            "requested_capabilities": [],
            "steps": [],
            "policy_snapshot": {
                "schema_version": "v0",
                "policy_id": "webpanel-default",
                "issued_at": None,
                "capability_grants": [],
                "metadata": {"source": "webpanel"},
            },
            "metadata": {"source": "webpanel"},
        }
        return kernel.run(run_request)
    except Exception:
        return None


def core_ingest(packet_dict: Dict[str, Any]) -> Dict[str, Any]:
    if _EXTERNAL_CORE_INGEST is not None:
        try:
            result = _EXTERNAL_CORE_INGEST(packet_dict)
            if isinstance(result, dict):
                return result
        except Exception:
            pass

    run_id = new_id("run")
    context_id = new_id("ctx")
    requires_ack = _requires_ack(packet_dict)
    mode = _interaction_mode(packet_dict, requires_ack)

    policy_basis = {"mvp": True}
    core_result = _try_kernel_result(packet_dict, run_id)
    if isinstance(core_result, dict):
        run_result = core_result.get("run_result") or {}
        if isinstance(run_result, dict):
            policy_basis["core_status"] = run_result.get("status")
            policy_basis["core_result_hash"] = run_result.get("result_hash")

    _STEP_STATE[run_id] = 0

    return {
        "run_id": run_id,
        "created_at_utc": now_utc(),
        "phase": 2,
        "signal": packet_dict,
        "context": {
            "context_id": context_id,
            "source_signal_id": packet_dict.get("signal_id"),
            "created_at_utc": now_utc(),
            "stable_elements": [],
            "unstable_elements": [],
            "unknowns": _unknowns(packet_dict),
            "assumptions_inherited": [],
            "execution_lanes_allowed": _execution_lanes(packet_dict),
            "risk_profile": {
                "risk_of_action": "medium",
                "risk_of_inaction": "medium",
                "risk_notes": "mvp: risk profile is structural until full policy wiring is present",
            },
            "requires_human_confirmation": requires_ack,
            "recommended_interaction_mode": mode,
            "policy_basis": policy_basis,
        },
        "requires_human_confirmation": requires_ack,
        "human_ack": None,
        "deferral_active": False,
        "quota_max_actions": None,
        "actions_taken": 0,
        "pause_required": requires_ack,
        "pause_reason": "awaiting_ack" if requires_ack else None,
    }


def core_step(run_id: str) -> Dict[str, Any]:
    if _EXTERNAL_CORE_STEP is not None:
        try:
            result = _EXTERNAL_CORE_STEP(run_id)
            if isinstance(result, dict):
                return result
        except Exception:
            pass

    actions_taken = _STEP_STATE.get(run_id, 0) + 1
    _STEP_STATE[run_id] = actions_taken
    return {
        "run_id": run_id,
        "actions_taken": actions_taken,
        "phase": 6,
    }
