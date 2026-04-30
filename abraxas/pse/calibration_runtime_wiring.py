from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def enable_runtime_wiring(
    candidate_state: dict,
    activation_review: dict,
    readiness: dict,
    wiring_out: Path,
    rollback_out: Path,
) -> dict:
    wiring_out.parent.mkdir(parents=True, exist_ok=True)
    rollback_out.parent.mkdir(parents=True, exist_ok=True)

    expected_multiplier = 0.9
    candidate_multiplier = candidate_state.get("calibration", {}).get("global_confidence_multiplier")
    review_multiplier = activation_review.get("review_summary", {}).get("multiplier")

    checks = [
        readiness.get("status") == "READY",
        candidate_state.get("status") == "ACTIVE_GENERATED_STATE",
        candidate_state.get("runtime_wiring_enabled") is False,
        activation_review.get("status") == "ACTIVATION_REVIEW_PASSED",
        activation_review.get("decision") == "ELIGIBLE_FOR_ACTIVATION",
        candidate_multiplier == expected_multiplier,
        review_multiplier == expected_multiplier,
        candidate_multiplier == review_multiplier,
    ]

    if not all(checks):
        return {
            "schema_version": "CalibrationRuntimeWiringReport.v1",
            "status": "NOT_COMPUTABLE",
            "new_state_hash": None,
            "previous_state_hash": None,
            "rollback_available": rollback_out.exists(),
            "post_validation_required": True,
        }

    previous_state_hash = None
    rollback_available = False
    if wiring_out.exists():
        previous = wiring_out.read_bytes()
        previous_state_hash = _sha256_bytes(previous)
        rollback_out.write_bytes(previous)
        rollback_available = True

    new_state = {
        "status": "RUNTIME_WIRING_ENABLED",
        "runtime_wiring_enabled": True,
        "calibration": {
            "global_confidence_multiplier": expected_multiplier,
        },
        "evidence": {
            "baseline": candidate_state.get("evidence", {}).get("baseline"),
            "candidate": candidate_state.get("evidence", {}).get("candidate"),
            "delta": candidate_state.get("evidence", {}).get("delta"),
        },
        "requires_post_validation": True,
        "source_logic_modified": False,
    }

    serialized = json.dumps(new_state, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    wiring_out.write_bytes(serialized)

    return {
        "schema_version": "CalibrationRuntimeWiringReport.v1",
        "status": "RUNTIME_WIRING_ENABLED",
        "new_state_hash": _sha256_bytes(serialized),
        "previous_state_hash": previous_state_hash,
        "rollback_available": rollback_available,
        "post_validation_required": True,
    }
