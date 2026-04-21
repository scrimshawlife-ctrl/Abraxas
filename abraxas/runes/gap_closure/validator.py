from __future__ import annotations

from pathlib import Path
from typing import Any

from abraxas.core.canonical import canonical_json, sha256_hex

from .runtime import REQUIRED_ARTIFACTS, load_json


def validate_gap_closure_artifacts(
    *,
    run_id: str,
    run_dir: Path,
    artifact_index: list[dict[str, Any]],
) -> dict[str, Any]:
    run_path = run_dir / "gap_closure_run.json"
    if not run_path.exists():
        return {
            "schema_version": "closure_validation_report.v1",
            "run_id": run_id,
            "status": "FAIL",
            "promotion_decision": "HOLD",
            "reason": "missing artifact: gap_closure_run.json",
            "authority_boundary": "projection cannot alter canon status",
        }

    run_payload = load_json(run_path)
    if run_payload.get("status") == "NOT_COMPUTABLE":
        return {
            "schema_version": "closure_validation_report.v1",
            "run_id": run_id,
            "status": "NOT_COMPUTABLE",
            "promotion_decision": "HOLD",
            "reason": "missing required input",
            "authority_boundary": "projection cannot alter canon status",
        }

    missing = [name for name in REQUIRED_ARTIFACTS if not (run_dir / name).exists()]
    if missing:
        return {
            "schema_version": "closure_validation_report.v1",
            "run_id": run_id,
            "status": "FAIL",
            "promotion_decision": "HOLD",
            "reason": f"missing artifact: {missing[0]}",
            "authority_boundary": "projection cannot alter canon status",
        }

    index_hash = sha256_hex(canonical_json(artifact_index))
    return {
        "schema_version": "closure_validation_report.v1",
        "run_id": run_id,
        "status": "PASS",
        "promotion_decision": "HOLD",
        "reason": "artifacts_valid_promotion_held",
        "artifact_index_hash": index_hash,
        "authority_boundary": "projection cannot alter canon status",
    }
