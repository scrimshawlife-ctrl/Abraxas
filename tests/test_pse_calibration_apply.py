from __future__ import annotations

import json
from pathlib import Path

from abraxas.pse.calibration_apply import apply_calibration_proposal
from abraxas.pse.calibration_approval import canonical_hash


def _inputs() -> tuple[dict, dict, dict]:
    proposal = {
        "status": "PROPOSAL_ONLY",
        "proposed_changes": {
            "global_confidence_multiplier": 0.8025,
            "domain_weights": {},
            "source_weights": {},
        },
    }
    approval = {
        "status": "APPROVED_FOR_APPLICATION",
        "proposal_hash": canonical_hash(proposal),
    }
    readiness = {"status": "READY"}
    return proposal, approval, readiness


def test_valid_apply_and_deterministic(tmp_path: Path) -> None:
    proposal, approval, readiness = _inputs()
    state_out = tmp_path / "state.json"
    rollback_out = tmp_path / "rollback.json"

    first = apply_calibration_proposal(readiness, proposal, approval, state_out, rollback_out, "1970-01-01T00:00:00Z")
    second = apply_calibration_proposal(readiness, proposal, approval, state_out, rollback_out, "1970-01-01T00:00:00Z")

    assert first["status"] == "APPLIED"
    assert second["status"] == "APPLIED"
    assert second["rollback_available"] is True

    state = json.loads(state_out.read_text())
    assert state["calibration"]["global_confidence_multiplier"] == 0.8025
    assert state["runtime_wiring_enabled"] is False


def test_rejection_paths(tmp_path: Path) -> None:
    proposal, approval, readiness = _inputs()
    state_out = tmp_path / "state.json"
    rollback_out = tmp_path / "rollback.json"

    report = apply_calibration_proposal({"status": "NOT_READY"}, proposal, approval, state_out, rollback_out, "1970-01-01T00:00:00Z")
    assert report["status"] == "NOT_COMPUTABLE"

    bad_approval = dict(approval)
    bad_approval["proposal_hash"] = "bad"
    report = apply_calibration_proposal(readiness, proposal, bad_approval, state_out, rollback_out, "1970-01-01T00:00:00Z")
    assert report["status"] == "NOT_COMPUTABLE"


def test_runtime_behavior_never_changes(tmp_path: Path) -> None:
    proposal, approval, readiness = _inputs()
    state_out = tmp_path / "state.json"
    rollback_out = tmp_path / "rollback.json"
    report = apply_calibration_proposal(readiness, proposal, approval, state_out, rollback_out, "1970-01-01T00:00:00Z")
    assert report["runtime_behavior_changed"] is False
