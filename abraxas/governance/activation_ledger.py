from __future__ import annotations

import hashlib
import json
from pathlib import Path

REQUIRED_ARTIFACTS = [
    "out/reports/abx_readiness_gate.latest.json",
    "out/reports/pse_calibration_candidate_cycle.latest.json",
    "out/reports/pse_calibration_candidate_proposal.latest.json",
    "out/reports/pse_calibration_candidate_approval_gate.latest.json",
    "out/reports/pse_calibration_candidate_application.latest.json",
    "out/state/pse_calibration_candidate_state.latest.json",
    "out/reports/pse_calibration_candidate_preview.latest.json",
    "out/reports/pse_calibration_activation_review.latest.json",
    "out/reports/pse_calibration_runtime_wiring.latest.json",
    "out/state/pse_calibration_runtime_wiring.latest.json",
    "out/reports/pse_calibration_post_activation_validation.latest.json",
]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_activation_ledger_receipt(repo_root: Path) -> dict:
    hashes: dict[str, str] = {}
    artifacts: dict[str, dict] = {}
    missing: list[str] = []

    for relative_path in REQUIRED_ARTIFACTS:
        path = repo_root / relative_path
        if not path.exists():
            missing.append(relative_path)
            continue
        payload = path.read_bytes()
        hashes[relative_path] = _sha256_bytes(payload)
        artifacts[relative_path] = json.loads(payload.decode("utf-8"))

    base = {
        "schema_version": "ActivationLedgerReceipt.v1",
        "status": "RECEIPT_BLOCKED",
        "cycle_id": "pse_calibration_activation_cycle_001",
        "artifacts": {"required": REQUIRED_ARTIFACTS, "hashes": hashes, "missing": missing},
        "metrics": {
            "baseline": None,
            "activated": None,
            "delta": None,
            "multiplier": None,
        },
        "validation": {
            "status": "NOT_COMPUTABLE",
            "runtime": "NOT_COMPUTABLE",
            "rollback": "NOT_COMPUTABLE",
        },
        "promotion": {
            "eligible": False,
            "promoted": False,
            "authority": "NOT_GRANTED",
        },
    }

    if missing:
        return base

    readiness = artifacts["out/reports/abx_readiness_gate.latest.json"]
    candidate_state = artifacts["out/state/pse_calibration_candidate_state.latest.json"]
    activation_review = artifacts["out/reports/pse_calibration_activation_review.latest.json"]
    runtime_wiring_report = artifacts["out/reports/pse_calibration_runtime_wiring.latest.json"]
    runtime_wiring_state = artifacts["out/state/pse_calibration_runtime_wiring.latest.json"]
    post_validation = artifacts["out/reports/pse_calibration_post_activation_validation.latest.json"]

    baseline = float(post_validation.get("baseline", 0.0))
    activated = float(post_validation.get("activated", 0.0))
    delta = float(post_validation.get("delta", 0.0))
    multiplier = float(runtime_wiring_state.get("calibration", {}).get("global_confidence_multiplier", 0.0))

    metrics = {
        "baseline": round(baseline, 6),
        "activated": round(activated, 6),
        "delta": round(delta, 6),
        "multiplier": round(multiplier, 6),
    }

    checks = [
        readiness.get("status") == "READY",
        candidate_state.get("status") == "ACTIVE_GENERATED_STATE",
        activation_review.get("status") == "ACTIVATION_REVIEW_PASSED",
        runtime_wiring_report.get("status") == "RUNTIME_WIRING_ENABLED",
        runtime_wiring_state.get("status") == "RUNTIME_WIRING_ENABLED",
        post_validation.get("status") == "POST_ACTIVATION_VALIDATED",
        post_validation.get("runtime_wiring_status") == "ENABLED_VALIDATED",
        post_validation.get("rollback_recommendation") == "NONE",
        post_validation.get("source_logic_modified") is False,
        metrics["baseline"] == 0.1975,
        metrics["activated"] == 0.196975,
        metrics["delta"] == -0.000525,
        metrics["multiplier"] == 0.9,
    ]

    if not all(checks):
        base["metrics"] = metrics
        base["validation"] = {
            "status": post_validation.get("status", "NOT_COMPUTABLE"),
            "runtime": post_validation.get("runtime_wiring_status", "NOT_COMPUTABLE"),
            "rollback": post_validation.get("rollback_recommendation", "NOT_COMPUTABLE"),
        }
        return base

    return {
        "schema_version": "ActivationLedgerReceipt.v1",
        "status": "RECEIPT_SEALED",
        "cycle_id": "pse_calibration_activation_cycle_001",
        "artifacts": {"required": REQUIRED_ARTIFACTS, "hashes": hashes, "missing": []},
        "metrics": metrics,
        "validation": {
            "status": "POST_ACTIVATION_VALIDATED",
            "runtime": "ENABLED_VALIDATED",
            "rollback": "NONE",
        },
        "promotion": {
            "eligible": True,
            "promoted": False,
            "authority": "NOT_GRANTED",
        },
    }
