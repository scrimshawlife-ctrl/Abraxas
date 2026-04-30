from __future__ import annotations

import hashlib
import json


def canonical_hash(payload: dict) -> str:
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def run_calibration_approval_gate(proposal: dict, approval_packet: dict, readiness: dict) -> dict:
    proposal_hash = canonical_hash(proposal)
    base = {
        "schema_version": "CalibrationApprovalGateReport.v1",
        "status": "NOT_COMPUTABLE",
        "authority": "APPROVAL_GATE_ONLY",
        "proposal_hash": proposal_hash,
        "approval": {
            "approved": bool(approval_packet.get("approved", False)),
            "approved_by": approval_packet.get("approved_by", ""),
            "approved_at": approval_packet.get("approved_at", ""),
            "scope": approval_packet.get("scope", []),
        },
        "application_allowed": False,
        "application_next_step": "PATCH-013_REQUIRED",
    }

    conditions = [
        readiness.get("status") == "READY",
        proposal.get("status") == "PROPOSAL_ONLY",
        proposal.get("approval", {}).get("applied") is False,
        approval_packet.get("approved") is True,
        bool(approval_packet.get("approved_by")),
        bool(approval_packet.get("approved_at")),
        bool(approval_packet.get("scope")),
        approval_packet.get("proposal_hash") == proposal_hash,
    ]

    if all(conditions):
        base["status"] = "APPROVED_FOR_APPLICATION"

    return base
