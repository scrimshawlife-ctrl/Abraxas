from __future__ import annotations

import hashlib
import json
from pathlib import Path

from abraxas.pse.calibration_candidate_approval import canonical_hash


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply_candidate_proposal(
    proposal: dict,
    approval_gate: dict,
    readiness: dict,
    state_out: Path,
    rollback_out: Path,
) -> dict:
    state_out.parent.mkdir(parents=True, exist_ok=True)
    rollback_out.parent.mkdir(parents=True, exist_ok=True)

    proposal_hash = canonical_hash(proposal)
    checks = [
        readiness.get("status") == "READY",
        proposal.get("status") == "PROPOSAL_ONLY",
        approval_gate.get("status") == "APPROVED_FOR_APPLICATION",
        approval_gate.get("proposal_hash") == proposal_hash,
        approval_gate.get("runtime_wiring_enabled") is False,
    ]

    if not all(checks):
        return {
            "schema_version": "CalibrationCandidateApplicationReport.v1",
            "status": "NOT_COMPUTABLE",
            "new_state_hash": None,
            "previous_state_hash": None,
            "rollback_available": rollback_out.exists(),
            "runtime_behavior_changed": False,
        }

    previous_state_hash = None
    rollback_available = False
    if state_out.exists():
        previous = state_out.read_bytes()
        previous_state_hash = _sha256_bytes(previous)
        rollback_out.write_bytes(previous)
        rollback_available = True

    new_state = {
        "status": "ACTIVE_GENERATED_STATE",
        "calibration": {
            "global_confidence_multiplier": proposal.get("proposed_changes", {}).get("global_confidence_multiplier", 0.0)
        },
        "evidence": {
            "baseline": proposal.get("evidence", {}).get("baseline_mean_brier"),
            "candidate": proposal.get("evidence", {}).get("candidate_mean_brier"),
            "delta": proposal.get("evidence", {}).get("mean_brier_delta"),
        },
        "applied": True,
        "runtime_wiring_enabled": False,
    }
    serialized = json.dumps(new_state, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    state_out.write_bytes(serialized)

    return {
        "schema_version": "CalibrationCandidateApplicationReport.v1",
        "status": "APPLIED",
        "new_state_hash": _sha256_bytes(serialized),
        "previous_state_hash": previous_state_hash,
        "rollback_available": rollback_available,
        "runtime_behavior_changed": False,
    }
