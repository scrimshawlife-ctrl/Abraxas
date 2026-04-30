from __future__ import annotations

import hashlib
import json


def canonical_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def run_candidate_approval_gate(proposal: dict, approval: dict, readiness: dict) -> dict:
    proposal_hash = canonical_hash(proposal)
    base = {
        "schema_version": "CalibrationCandidateApprovalGateReport.v1",
        "status": "NOT_COMPUTABLE",
        "authority": "APPROVAL_GATE_ONLY",
        "proposal_hash": proposal_hash,
        "candidate_summary": {
            "global_confidence_multiplier": proposal.get("proposed_changes", {}).get("global_confidence_multiplier", 0.0),
            "baseline_mean_brier": proposal.get("evidence", {}).get("baseline_mean_brier"),
            "candidate_mean_brier": proposal.get("evidence", {}).get("candidate_mean_brier"),
            "mean_brier_delta": proposal.get("evidence", {}).get("mean_brier_delta"),
            "improvement": proposal.get("evidence", {}).get("improvement", False),
        },
        "application_allowed": False,
        "application_next_step": "PATCH-019_REQUIRED",
        "runtime_wiring_enabled": False,
    }

    checks = [
        readiness.get("status") == "READY",
        proposal.get("status") == "PROPOSAL_ONLY",
        proposal.get("source") == "CANDIDATE_CYCLE",
        approval.get("approved") is True,
        bool(approval.get("approved_by")),
        bool(approval.get("approved_at")),
        bool(approval.get("scope")),
        approval.get("proposal_hash") == proposal_hash,
    ]

    if all(checks):
        base["status"] = "APPROVED_FOR_APPLICATION"
    return base
