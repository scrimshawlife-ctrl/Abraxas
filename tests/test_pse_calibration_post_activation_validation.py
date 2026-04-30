from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json

from abraxas.pse.calibration_post_activation_validation import run_post_activation_validation


def _inputs() -> tuple[list[dict], list[dict], dict, dict, dict]:
    predictions = json.loads(Path("fixtures/pse/scoreable_predictions.v1.json").read_text())
    outcomes = json.loads(Path("fixtures/pse/scoreable_outcomes.v1.json").read_text())
    wiring_state = {
        "status": "RUNTIME_WIRING_ENABLED",
        "runtime_wiring_enabled": True,
        "calibration": {"global_confidence_multiplier": 0.9},
        "evidence": {"baseline": 0.1975, "candidate": 0.196975, "delta": -0.000525},
        "requires_post_validation": True,
        "source_logic_modified": False,
    }
    wiring_report = {
        "status": "RUNTIME_WIRING_ENABLED",
        "post_validation_required": True,
    }
    readiness = {"status": "READY"}
    return predictions, outcomes, wiring_state, wiring_report, readiness


def test_deterministic_and_expected_values() -> None:
    predictions, outcomes, wiring_state, wiring_report, readiness = _inputs()
    first = run_post_activation_validation(predictions, outcomes, wiring_state, wiring_report, readiness)
    second = run_post_activation_validation(predictions, outcomes, wiring_state, wiring_report, readiness)
    assert first == second
    assert first["status"] == "POST_ACTIVATION_VALIDATED"
    assert first["baseline"] == 0.1975
    assert first["activated"] == 0.196975
    assert first["delta"] == -0.000525
    assert first["rollback_recommendation"] == "NONE"


def test_failure_path_no_rollback_execution() -> None:
    predictions, outcomes, wiring_state, wiring_report, readiness = _inputs()
    bad_state = deepcopy(wiring_state)
    bad_state["source_logic_modified"] = True
    report = run_post_activation_validation(predictions, outcomes, bad_state, wiring_report, readiness)
    assert report["status"] == "POST_ACTIVATION_FAILED"
    assert report["rollback_recommendation"] == "ROLLBACK_RECOMMENDED"
    assert report["runtime_wiring_status"] == "ENABLED_FAILED"


def test_scored_count_gate_enforced() -> None:
    predictions, outcomes, wiring_state, wiring_report, readiness = _inputs()
    report = run_post_activation_validation(predictions[:2], outcomes, wiring_state, wiring_report, readiness)
    assert report["status"] == "POST_ACTIVATION_FAILED"
