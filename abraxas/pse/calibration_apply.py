from __future__ import annotations

import hashlib
import json
from pathlib import Path

from abraxas.pse.calibration_approval import canonical_hash


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply_calibration_proposal(
    readiness: dict,
    proposal: dict,
    approval_gate: dict,
    state_out: Path,
    rollback_out: Path,
    timestamp: str,
) -> dict:
    state_out.parent.mkdir(parents=True, exist_ok=True)
    rollback_out.parent.mkdir(parents=True, exist_ok=True)

    proposal_hash = canonical_hash(proposal)
    allowed = all(
        [
            readiness.get("status") == "READY",
            proposal.get("status") == "PROPOSAL_ONLY",
            approval_gate.get("status") == "APPROVED_FOR_APPLICATION",
            approval_gate.get("proposal_hash") == proposal_hash,
        ]
    )

    if not allowed:
        return {
            "schema_version": "CalibrationApplicationReport.v1",
            "status": "NOT_COMPUTABLE",
            "previous_state_hash": None,
            "new_state_hash": None,
            "rollback_available": rollback_out.exists(),
            "runtime_behavior_changed": False,
            "applied_at": timestamp,
        }

    previous_state_hash = None
    rollback_available = False
    if state_out.exists():
        previous_bytes = state_out.read_bytes()
        previous_state_hash = _hash_bytes(previous_bytes)
        rollback_out.write_bytes(previous_bytes)
        rollback_available = True

    new_state = {
        "status": "ACTIVE_GENERATED_STATE",
        "calibration": {
            "global_confidence_multiplier": proposal["proposed_changes"]["global_confidence_multiplier"],
            "domain_weights": proposal["proposed_changes"].get("domain_weights", {}),
            "source_weights": proposal["proposed_changes"].get("source_weights", {}),
        },
        "applied": True,
        "runtime_wiring_enabled": False,
        "generated_at": timestamp,
    }
    serialized = json.dumps(new_state, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    state_out.write_bytes(serialized)

    return {
        "schema_version": "CalibrationApplicationReport.v1",
        "status": "APPLIED",
        "previous_state_hash": previous_state_hash,
        "new_state_hash": _hash_bytes(serialized),
        "rollback_available": rollback_available,
        "runtime_behavior_changed": False,
        "applied_at": timestamp,
    }
