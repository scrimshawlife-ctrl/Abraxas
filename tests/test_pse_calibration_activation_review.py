from __future__ import annotations

from copy import deepcopy

from abraxas.pse.calibration_activation_review import run_activation_review


def _inputs() -> tuple[dict, dict, dict]:
    readiness = {"status": "READY"}
    preview = {
        "status": "PREVIEW_ONLY",
        "recommendation": "ELIGIBLE_FOR_ACTIVATION_REVIEW",
        "baseline": {"mean_brier": 0.1975},
        "candidate_preview": {"mean_brier": 0.196975, "multiplier": 0.9},
        "delta": {"mean_brier_delta": -0.000525, "improvement": True},
    }
    state = {
        "status": "ACTIVE_GENERATED_STATE",
        "calibration": {"global_confidence_multiplier": 0.9},
        "applied": True,
        "runtime_wiring_enabled": False,
    }
    return readiness, preview, state


def test_deterministic_and_passed_decision() -> None:
    readiness, preview, state = _inputs()
    first = run_activation_review(readiness, preview, state)
    second = run_activation_review(readiness, preview, state)
    assert first == second
    assert first["status"] == "ACTIVATION_REVIEW_PASSED"
    assert first["decision"] == "ELIGIBLE_FOR_ACTIVATION"
    assert first["runtime_activation_allowed"] is False
    assert first["locked"] is True


def test_rejection_paths() -> None:
    readiness, preview, state = _inputs()
    assert run_activation_review({"status": "NOT_READY"}, preview, state)["status"] == "NOT_COMPUTABLE"

    bad_preview = deepcopy(preview)
    bad_preview["delta"]["mean_brier_delta"] = 0.0
    assert run_activation_review(readiness, bad_preview, state)["status"] == "NOT_COMPUTABLE"

    bad_state = deepcopy(state)
    bad_state["runtime_wiring_enabled"] = True
    assert run_activation_review(readiness, preview, bad_state)["status"] == "NOT_COMPUTABLE"
