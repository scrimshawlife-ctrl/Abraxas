from __future__ import annotations


def build_calibration_activation_decision(preview: dict, state: dict, readiness: dict) -> dict:
    base = {
        "schema_version": "CalibrationActivationDecision.v1",
        "status": "NOT_COMPUTABLE",
        "authority": "ACTIVATION_DECISION_GATE",
        "decision": "DO_NOT_ENABLE_RUNTIME_WIRING",
        "locked": True,
        "runtime_wiring_enabled": False,
        "reason": "GATE_FAILED",
        "next_eligible_trigger": "NEW_CALIBRATION_CYCLE_REQUIRED",
    }

    if readiness.get("status") != "READY":
        return base
    if preview.get("status") != "PREVIEW_ONLY":
        return base
    if state.get("runtime_wiring_enabled") is not False:
        return base

    improvement = bool(preview.get("delta", {}).get("improvement", False))
    if improvement:
        return {
            "schema_version": "CalibrationActivationDecision.v1",
            "status": "DECISION_RECORDED",
            "authority": "ACTIVATION_DECISION_GATE",
            "decision": "ELIGIBLE_FOR_ACTIVATION_REVIEW",
            "locked": False,
            "runtime_wiring_enabled": False,
            "reason": "PREVIEW_IMPROVEMENT_DETECTED",
            "next_eligible_trigger": "MANUAL_ACTIVATION_REVIEW_REQUIRED",
        }

    return {
        "schema_version": "CalibrationActivationDecision.v1",
        "status": "DECISION_RECORDED",
        "authority": "ACTIVATION_DECISION_GATE",
        "decision": "DO_NOT_ENABLE_RUNTIME_WIRING",
        "locked": True,
        "runtime_wiring_enabled": False,
        "reason": "NO_PREVIEW_IMPROVEMENT",
        "next_eligible_trigger": "NEW_CALIBRATION_CYCLE_REQUIRED",
    }
