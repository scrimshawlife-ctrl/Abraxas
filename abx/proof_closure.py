from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aal_core.runes.executor import execute_rune
from abx.execution_validator import emit_validation_result, validate_run


@dataclass(frozen=True)
class ProofClosureResult:
    run_id: str
    status: str
    rune_artifact_path: str
    validator_artifact_path: str
    operator_summary_path: str
    attestation_path: str


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def run_canonical_proof_closure(*, run_id: str, base_dir: Path = Path(".")) -> ProofClosureResult:
    """Execute canonical proof-bearing runtime spine for one run_id.

    Spine: emit rune artifact -> ledger pointer -> validator artifact -> operator projection -> attestation.
    """

    timestamp = _utc_now_iso()
    rune_artifact_dir = base_dir / "out" / "runtime_spine"
    ledger_path = base_dir / "out" / "ledger" / "canonical_runtime_spine.jsonl"

    rune_artifact = execute_rune(
        rune_id="RUNE.INGEST",
        run_id=run_id,
        phase="INGEST",
        step=lambda payload: {
            "payload": {
                "normalized": payload["payload"],
                "proof_closure": "canonical-runtime-spine",
            },
            "summary": "Canonical ingest artifact emitted for proof closure.",
            "metrics": {"input_count": 1, "deterministic": True},
        },
        inputs={"payload": {"message": "canonical-proof-closure"}, "content_hash": "sha256:static"},
        provenance={
            "source_refs": ["abx.proof_closure"],
            "operator": "abx.cli proof-run",
            "notes": "Canonical runtime spine emission",
        },
        correlation_pointers=[
            {"type": "ledger_path", "value": ledger_path.as_posix(), "status": "PRESENT"},
            {"type": "operator_surface", "value": "webpanel:/operator", "status": "PRESENT"},
        ],
        ledger_record_ids=[f"ledger:{run_id}:emit"],
        ledger_artifact_ids=[f"runtime-spine-{run_id}"],
    )

    rune_artifact_path = rune_artifact_dir / f"rune_execution_{run_id}.json"
    _write_json(rune_artifact_path, rune_artifact)

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_event = {
        "run_id": run_id,
        "event_id": f"canonical-runtime-{run_id}",
        "artifact_id": rune_artifact["artifact_id"],
        "timestamp": timestamp,
        "phase": "INGEST",
        "status": rune_artifact["status"],
        "refs": {
            "rune_artifact": rune_artifact_path.as_posix(),
        },
        "provenance": {
            "run_id": run_id,
            "source": "abx.proof_closure",
        },
    }
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(ledger_event, ensure_ascii=False, sort_keys=True) + "\n")

    validation_result = validate_run(run_id, base_dir=base_dir)
    validator_artifact_path = emit_validation_result(validation_result, base_dir / "out" / "validators")

    operator_summary = {
        "artifactType": "OperatorProofProjection.v1",
        "run_id": run_id,
        "timestamp": _utc_now_iso(),
        "status": "READY" if validation_result.valid else "REVIEW_REQUIRED",
        "proof_spine": {
            "emit": rune_artifact_path.as_posix(),
            "ledger": ledger_path.as_posix(),
            "validate": validator_artifact_path.as_posix(),
        },
        "validator": {
            "status": validation_result.status.value,
            "valid": validation_result.valid,
            "ledger_record_ids": validation_result.ledger_record_ids,
            "ledger_artifact_ids": validation_result.ledger_artifact_ids,
            "correlation_pointers": validation_result.correlation_pointers,
        },
    }
    operator_summary_path = _write_json(
        base_dir / "out" / "operator" / f"proof_projection_{run_id}.json",
        operator_summary,
    )

    attestation = {
        "schema": "CanonicalProofAttestation.v1",
        "run_id": run_id,
        "timestamp": _utc_now_iso(),
        "overall_status": "PASS" if validation_result.valid else "NOT_COMPUTABLE",
        "status_reason": "validator_valid" if validation_result.valid else "validator_not_valid",
        "artifacts": {
            "rune_execution": rune_artifact_path.as_posix(),
            "validation": validator_artifact_path.as_posix(),
            "operator_projection": operator_summary_path.as_posix(),
        },
        "provenance": {
            "runner": "abx.proof_closure.run_canonical_proof_closure",
            "source_refs": ["aal_core.runes.executor", "abx.execution_validator"],
        },
        "correlation_pointers": validation_result.correlation_pointers,
    }
    attestation_path = _write_json(base_dir / "out" / "attestation" / f"canonical_proof_{run_id}.json", attestation)

    return ProofClosureResult(
        run_id=run_id,
        status=attestation["overall_status"],
        rune_artifact_path=rune_artifact_path.as_posix(),
        validator_artifact_path=validator_artifact_path.as_posix(),
        operator_summary_path=operator_summary_path.as_posix(),
        attestation_path=attestation_path.as_posix(),
    )
