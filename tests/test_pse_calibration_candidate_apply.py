from __future__ import annotations

import json
from pathlib import Path

from abraxas.pse.calibration_candidate_apply import apply_candidate_proposal
from abraxas.pse.calibration_candidate_approval import canonical_hash


def _inputs() -> tuple[dict, dict, dict]:
    proposal = {
        "status": "PROPOSAL_ONLY",
        "proposed_changes": {"global_confidence_multiplier": 0.9},
        "evidence": {
            "baseline_mean_brier": 0.1975,
            "candidate_mean_brier": 0.196975,
            "mean_brier_delta": -0.000525,
        },
    }
    approval = {
        "status": "APPROVED_FOR_APPLICATION",
        "proposal_hash": canonical_hash(proposal),
        "runtime_wiring_enabled": False,
    }
    readiness = {"status": "READY"}
    return proposal, approval, readiness


def test_apply_writes_state_and_multiplier(tmp_path: Path) -> None:
    proposal, approval, readiness = _inputs()
    state_out = tmp_path / "state.json"
    rollback_out = tmp_path / "rollback.json"

    report = apply_candidate_proposal(proposal, approval, readiness, state_out, rollback_out)
    assert report["status"] == "APPLIED"
    state = json.loads(state_out.read_text())
    assert state["calibration"]["global_confidence_multiplier"] == 0.9
    assert state["runtime_wiring_enabled"] is False


def test_rollback_and_deterministic(tmp_path: Path) -> None:
    proposal, approval, readiness = _inputs()
    state_out = tmp_path / "state.json"
    rollback_out = tmp_path / "rollback.json"
    first = apply_candidate_proposal(proposal, approval, readiness, state_out, rollback_out)
    second = apply_candidate_proposal(proposal, approval, readiness, state_out, rollback_out)
    assert first["status"] == "APPLIED"
    assert second["rollback_available"] is True


def test_rejection_paths_and_runtime_unchanged(tmp_path: Path) -> None:
    proposal, approval, readiness = _inputs()
    state_out = tmp_path / "state.json"
    rollback_out = tmp_path / "rollback.json"

    bad_approval = dict(approval)
    bad_approval["proposal_hash"] = "bad"
    report = apply_candidate_proposal(proposal, bad_approval, readiness, state_out, rollback_out)
    assert report["status"] == "NOT_COMPUTABLE"
    assert report["runtime_behavior_changed"] is False
