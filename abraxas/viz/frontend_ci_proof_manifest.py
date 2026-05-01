from __future__ import annotations

from typing import Any, Dict

from abraxas.core.canonical import canonical_json, sha256_hex

ARTIFACT = "AAL-VIZ-FRONTEND-CI-PROOF-001"
SCHEMA_VERSION = "AALVizFrontendCIProof.v1"


def build_ci_proof_manifest(ci_status: str, reason: str | None = None) -> Dict[str, Any]:
    if ci_status == "passed":
        execution = "verified"
    elif ci_status in {"failed_environment", "not_computable_environment"}:
        execution = "not_computable_environment"
    else:
        execution = "blocked"
    payload: Dict[str, Any] = {
        "artifact": ARTIFACT,
        "schema_version": SCHEMA_VERSION,
        "ci_status": ci_status,
        "reason": reason,
        "frontend_execution": execution,
        "authority": {
            "ci_proof_recording": True,
            "interaction_runtime": False,
            "execution": False,
            "scheduler": False,
        },
    }
    payload["proof_id"] = sha256_hex(canonical_json(payload))
    wrapped = dict(payload)
    wrapped["proof_hash"] = sha256_hex(canonical_json(wrapped))
    return wrapped
