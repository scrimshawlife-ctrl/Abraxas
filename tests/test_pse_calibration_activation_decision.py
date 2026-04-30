from __future__ import annotations

from abraxas.pse.calibration_decision import build_calibration_activation_decision


def _inputs() -> tuple[dict, dict, dict]:
    preview = {
        "status": "PREVIEW_ONLY",
        "delta": {"improvement": False},
    }
    state = {
        "status": "ACTIVE_GENERATED_STATE",
        "runtime_wiring_enabled": False,
        "applied": True,
    }
    readiness = {"status": "READY"}
    return preview, state, readiness


def test_deterministic_decision_and_reason() -> None:
    preview, state, readiness = _inputs()
    first = build_calibration_activation_decision(preview, state, readiness)
    second = build_calibration_activation_decision(preview, state, readiness)
    assert first == second
    assert first["status"] == "DECISION_RECORDED"
    assert first["decision"] == "DO_NOT_ENABLE_RUNTIME_WIRING"
    assert first["reason"] == "NO_PREVIEW_IMPROVEMENT"
    assert first["locked"] is True


def test_rejection_paths() -> None:
    preview, state, readiness = _inputs()
    assert build_calibration_activation_decision(preview, state, {"status": "NOT_READY"})["status"] == "NOT_COMPUTABLE"
    bad_preview = dict(preview)
    bad_preview["status"] = "NOT_COMPUTABLE"
    assert build_calibration_activation_decision(bad_preview, state, readiness)["status"] == "NOT_COMPUTABLE"
    bad_state = dict(state)
    bad_state["runtime_wiring_enabled"] = True
    assert build_calibration_activation_decision(preview, bad_state, readiness)["status"] == "NOT_COMPUTABLE"


def test_runtime_still_disabled() -> None:
    preview, state, readiness = _inputs()
    report = build_calibration_activation_decision(preview, state, readiness)
    assert report["runtime_wiring_enabled"] is False
