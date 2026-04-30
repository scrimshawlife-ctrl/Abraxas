from __future__ import annotations

import json
from pathlib import Path

from abraxas.pse.calibration_cycle import build_calibration_candidate_cycle


def _inputs() -> tuple[list[dict], list[dict], dict, dict]:
    predictions = json.loads(Path("fixtures/pse/scoreable_predictions.v1.json").read_text())
    outcomes = json.loads(Path("fixtures/pse/scoreable_outcomes.v1.json").read_text())
    readiness = {"status": "READY"}
    decision = {"status": "DECISION_RECORDED", "runtime_wiring_enabled": False}
    return predictions, outcomes, readiness, decision


def test_deterministic_and_baseline_and_ranking() -> None:
    predictions, outcomes, readiness, decision = _inputs()
    first = build_calibration_candidate_cycle(predictions, outcomes, readiness, decision)
    second = build_calibration_candidate_cycle(predictions, outcomes, readiness, decision)
    assert first == second
    assert first["status"] == "CANDIDATE_CYCLE_COMPLETE"
    assert first["baseline"]["mean_brier"] == 0.1975
    assert any(c["multiplier"] == 1.0 and c["mean_brier"] == 0.1975 for c in first["candidates"])
    sorted_copy = sorted(first["candidates"], key=lambda x: (x["mean_brier"], x["multiplier"]))
    assert first["candidates"] == sorted_copy


def test_recommendation_and_runtime_disabled() -> None:
    predictions, outcomes, readiness, decision = _inputs()
    report = build_calibration_candidate_cycle(predictions, outcomes, readiness, decision)
    assert report["recommendation"] in {"NO_IMPROVING_CANDIDATE", "CREATE_NEW_PROPOSAL_CANDIDATE"}
    assert report["runtime_wiring_enabled"] is False


def test_rejection_paths() -> None:
    predictions, outcomes, readiness, decision = _inputs()
    assert build_calibration_candidate_cycle(predictions, outcomes, {"status": "NOT_READY"}, decision)["status"] == "NOT_COMPUTABLE"
    assert build_calibration_candidate_cycle(predictions, outcomes, readiness, {"status": "NOT_COMPUTABLE", "runtime_wiring_enabled": False})["status"] == "NOT_COMPUTABLE"
