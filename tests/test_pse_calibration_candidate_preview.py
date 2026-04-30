from __future__ import annotations

import json
from pathlib import Path

from abraxas.pse.calibration_candidate_preview import build_candidate_preview


def _inputs() -> tuple[list[dict], list[dict], dict, dict]:
    predictions = json.loads(Path("fixtures/pse/scoreable_predictions.v1.json").read_text())
    outcomes = json.loads(Path("fixtures/pse/scoreable_outcomes.v1.json").read_text())
    state = {
        "status": "ACTIVE_GENERATED_STATE",
        "calibration": {"global_confidence_multiplier": 0.9},
        "applied": True,
        "runtime_wiring_enabled": False,
    }
    readiness = {"status": "READY"}
    return predictions, outcomes, state, readiness


def test_deterministic_and_expected_values() -> None:
    predictions, outcomes, state, readiness = _inputs()
    first = build_candidate_preview(predictions, outcomes, state, readiness)
    second = build_candidate_preview(predictions, outcomes, state, readiness)
    assert first == second
    assert first["status"] == "PREVIEW_ONLY"
    assert first["baseline"]["mean_brier"] == 0.1975
    assert first["candidate_preview"]["mean_brier"] == 0.196975
    assert first["delta"]["mean_brier_delta"] == -0.000525
    assert first["delta"]["improvement"] is True
    assert first["recommendation"] == "ELIGIBLE_FOR_ACTIVATION_REVIEW"
    assert first["runtime_behavior_changed"] is False


def test_rejection_paths() -> None:
    predictions, outcomes, state, readiness = _inputs()
    assert build_candidate_preview(predictions, outcomes, state, {"status": "NOT_READY"})["status"] == "NOT_COMPUTABLE"
    bad_state = dict(state)
    bad_state["runtime_wiring_enabled"] = True
    assert build_candidate_preview(predictions, outcomes, bad_state, readiness)["status"] == "NOT_COMPUTABLE"
