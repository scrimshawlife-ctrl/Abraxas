from __future__ import annotations

from copy import deepcopy

from abraxas.pse.calibration_candidate_approval import canonical_hash, run_candidate_approval_gate


def _inputs() -> tuple[dict, dict, dict]:
    proposal = {
        "status": "PROPOSAL_ONLY",
        "source": "CANDIDATE_CYCLE",
        "proposed_changes": {"global_confidence_multiplier": 0.9},
        "evidence": {
            "baseline_mean_brier": 0.1975,
            "candidate_mean_brier": 0.196975,
            "mean_brier_delta": -0.000525,
            "improvement": True,
        },
    }
    approval = {
        "proposal_hash": canonical_hash(proposal),
        "approved": True,
        "approved_by": "operator",
        "approved_at": "1970-01-01T00:00:00Z",
        "scope": ["global"],
    }
    readiness = {"status": "READY"}
    return proposal, approval, readiness


def test_deterministic_hash_and_approval_path() -> None:
    proposal, approval, readiness = _inputs()
    assert canonical_hash(proposal) == canonical_hash(proposal)
    first = run_candidate_approval_gate(proposal, approval, readiness)
    second = run_candidate_approval_gate(proposal, approval, readiness)
    assert first == second
    assert first["status"] == "APPROVED_FOR_APPLICATION"
    assert first["application_allowed"] is False


def test_hash_mismatch_and_missing_fields_rejection() -> None:
    proposal, approval, readiness = _inputs()
    bad_hash = deepcopy(approval)
    bad_hash["proposal_hash"] = "bad"
    assert run_candidate_approval_gate(proposal, bad_hash, readiness)["status"] == "NOT_COMPUTABLE"

    missing = deepcopy(approval)
    missing["approved_by"] = ""
    assert run_candidate_approval_gate(proposal, missing, readiness)["status"] == "NOT_COMPUTABLE"


def test_runtime_disabled_and_no_apply() -> None:
    proposal, approval, readiness = _inputs()
    report = run_candidate_approval_gate(proposal, approval, readiness)
    assert report["runtime_wiring_enabled"] is False
    assert report["application_allowed"] is False
