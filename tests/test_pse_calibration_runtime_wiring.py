from __future__ import annotations

import json
from pathlib import Path

from abraxas.pse.calibration_runtime_wiring import enable_runtime_wiring


def _inputs() -> tuple[dict, dict, dict]:
    candidate_state = {
        "status": "ACTIVE_GENERATED_STATE",
        "runtime_wiring_enabled": False,
        "calibration": {"global_confidence_multiplier": 0.9},
        "evidence": {"baseline": 0.1975, "candidate": 0.196975, "delta": -0.000525},
    }
    activation_review = {
        "status": "ACTIVATION_REVIEW_PASSED",
        "decision": "ELIGIBLE_FOR_ACTIVATION",
        "review_summary": {"multiplier": 0.9},
    }
    readiness = {"status": "READY"}
    return candidate_state, activation_review, readiness


def test_runtime_wiring_enabled_and_multiplier_preserved(tmp_path: Path) -> None:
    candidate_state, activation_review, readiness = _inputs()
    wiring_out = tmp_path / "wiring.json"
    rollback_out = tmp_path / "rollback.json"
    report = enable_runtime_wiring(candidate_state, activation_review, readiness, wiring_out, rollback_out)
    assert report["status"] == "RUNTIME_WIRING_ENABLED"
    state = json.loads(wiring_out.read_text())
    assert state["runtime_wiring_enabled"] is True
    assert state["calibration"]["global_confidence_multiplier"] == 0.9
    assert state["source_logic_modified"] is False


def test_rollback_and_deterministic_output(tmp_path: Path) -> None:
    candidate_state, activation_review, readiness = _inputs()
    wiring_out = tmp_path / "wiring.json"
    rollback_out = tmp_path / "rollback.json"
    first = enable_runtime_wiring(candidate_state, activation_review, readiness, wiring_out, rollback_out)
    second = enable_runtime_wiring(candidate_state, activation_review, readiness, wiring_out, rollback_out)
    assert first["status"] == "RUNTIME_WIRING_ENABLED"
    assert second["rollback_available"] is True


def test_rejection_paths_enforced(tmp_path: Path) -> None:
    candidate_state, activation_review, readiness = _inputs()
    wiring_out = tmp_path / "wiring.json"
    rollback_out = tmp_path / "rollback.json"

    bad_readiness = {"status": "NOT_READY"}
    report = enable_runtime_wiring(candidate_state, activation_review, bad_readiness, wiring_out, rollback_out)
    assert report["status"] == "NOT_COMPUTABLE"

    bad_state = dict(candidate_state)
    bad_state["runtime_wiring_enabled"] = True
    report2 = enable_runtime_wiring(bad_state, activation_review, readiness, wiring_out, rollback_out)
    assert report2["status"] == "NOT_COMPUTABLE"
