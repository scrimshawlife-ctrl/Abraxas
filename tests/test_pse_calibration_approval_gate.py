from __future__ import annotations

from copy import deepcopy

from abraxas.pse.calibration_approval import canonical_hash, run_calibration_approval_gate


def _valid_inputs() -> tuple[dict, dict, dict]:
    proposal = {
        "schema_version": "CalibrationApplicationProposal.v1",
        "status": "PROPOSAL_ONLY",
        "authority": "PROPOSAL_ONLY",
        "proposed_changes": {"global_confidence_multiplier": 0.8025, "domain_weights": {}, "source_weights": {}},
        "approval": {"requires_approval": True, "approved": False, "applied": False},
    }
    readiness = {"status": "READY"}
    approval = {
        "approved": True,
        "approved_by": "ops",
        "approved_at": "1970-01-01T00:00:00Z",
        "scope": ["global"],
        "proposal_hash": canonical_hash(proposal),
    }
    return proposal, approval, readiness


def test_deterministic_hash_and_output() -> None:
    proposal, approval, readiness = _valid_inputs()
    assert canonical_hash(proposal) == canonical_hash(proposal)
    first = run_calibration_approval_gate(proposal, approval, readiness)
    second = run_calibration_approval_gate(proposal, approval, readiness)
    assert first == second


def test_rejection_paths() -> None:
    proposal, approval, readiness = _valid_inputs()
    assert run_calibration_approval_gate(proposal, approval, {"status": "NOT_READY"})["status"] == "NOT_COMPUTABLE"

    bad_proposal = deepcopy(proposal)
    bad_proposal["status"] = "NOT_COMPUTABLE"
    assert run_calibration_approval_gate(bad_proposal, approval, readiness)["status"] == "NOT_COMPUTABLE"

    bad_approval = deepcopy(approval)
    bad_approval["approved"] = False
    assert run_calibration_approval_gate(proposal, bad_approval, readiness)["status"] == "NOT_COMPUTABLE"

    bad_hash = deepcopy(approval)
    bad_hash["proposal_hash"] = "bad"
    assert run_calibration_approval_gate(proposal, bad_hash, readiness)["status"] == "NOT_COMPUTABLE"


def test_valid_approval_and_application_lock() -> None:
    proposal, approval, readiness = _valid_inputs()
    report = run_calibration_approval_gate(proposal, approval, readiness)
    assert report["status"] == "APPROVED_FOR_APPLICATION"
    assert report["application_allowed"] is False
    assert report["application_next_step"] == "PATCH-013_REQUIRED"
