from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from abx.execution_validation_types import ExecutionValidationResult, ExecutionValidationStatus

DEFAULT_LEDGER_GLOBS = (
    "out/ledger/*.jsonl",
    "out/evolution_ledgers/*.jsonl",
    "out/forecast_ledger/*.jsonl",
    "out/value_ledgers/*.jsonl",
)

DEFAULT_ARTIFACT_GLOBS = (
    "out/proof_bundles/**/*",
    "out/reports/*",
    "artifacts_seal/**/*",
)

CANON_STATUS_BY_INTERNAL = {
    ExecutionValidationStatus.PASS: "VALID",
    ExecutionValidationStatus.FAIL: "INVALID",
    ExecutionValidationStatus.INCOMPLETE: "ERROR",
    ExecutionValidationStatus.NOT_COMPUTABLE: "ERROR",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_artifact_id(run_id: str) -> str:
    return f"execution-validation-{run_id}"


def _read_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                rows.append((line_no, obj))
    return rows


def _canonical_status(status: ExecutionValidationStatus) -> str:
    return CANON_STATUS_BY_INTERNAL.get(status, "ERROR")


def to_canon_artifact(
    result: ExecutionValidationResult,
    *,
    validator_id: str = "abx.execution_validator",
    artifact_type: str = "ExecutionValidationArtifact.v1",
) -> dict[str, Any]:
    return {
        "artifactType": artifact_type,
        "artifactId": result.artifact_id,
        "runId": result.run_id,
        "validatorId": validator_id,
        "timestamp": result.checked_at,
        "status": _canonical_status(result.status),
        "errors": list(result.errors),
        "warnings": list(result.warnings),
        "validatedArtifacts": list(result.ledger_artifact_ids),
        "correlation": {
            "ledgerIds": list(result.ledger_record_ids),
            "packetIds": [],
            "pointers": list(result.correlation_pointers),
        },
        "provenance": {
            **result.provenance,
            "internalStatus": result.status.value,
            "internalValid": result.valid,
        },
    }


def find_run_evidence(
    run_id: str,
    *,
    base_dir: Path = Path("."),
    ledger_globs: tuple[str, ...] = DEFAULT_LEDGER_GLOBS,
    artifact_globs: tuple[str, ...] = DEFAULT_ARTIFACT_GLOBS,
) -> dict[str, Any]:
    ledger_record_ids: list[str] = []
    ledger_artifact_ids: list[str] = []
    correlation_pointers: list[str] = []
    errors: list[str] = []

    for pattern in ledger_globs:
        for ledger_path in sorted(base_dir.glob(pattern)):
            for line_no, row in _read_jsonl(ledger_path):
                if str(row.get("run_id", "")) != run_id:
                    continue
                rec_id = (
                    row.get("record_id")
                    or row.get("event_id")
                    or row.get("id")
                    or row.get("sha256")
                    or f"{ledger_path.name}:{line_no}"
                )
                ledger_record_ids.append(str(rec_id))
                if row.get("artifact_id"):
                    ledger_artifact_ids.append(str(row["artifact_id"]))
                correlation_pointers.append(f"{ledger_path.as_posix()}:{line_no}")

    for pattern in artifact_globs:
        for path in sorted(base_dir.glob(pattern)):
            if not path.is_file():
                continue
            if run_id in path.name or run_id in path.as_posix():
                ledger_artifact_ids.append(path.name)
                correlation_pointers.append(path.as_posix())

    # Deduplicate deterministically.
    ledger_record_ids = sorted(set(ledger_record_ids))
    ledger_artifact_ids = sorted(set(ledger_artifact_ids))
    correlation_pointers = sorted(set(correlation_pointers))

    return {
        "ledger_record_ids": ledger_record_ids,
        "ledger_artifact_ids": ledger_artifact_ids,
        "correlation_pointers": correlation_pointers,
        "errors": errors,
    }


def validate_run(
    run_id: str,
    *,
    base_dir: Path = Path("."),
    checked_at: str | None = None,
    ledger_globs: tuple[str, ...] = DEFAULT_LEDGER_GLOBS,
    artifact_globs: tuple[str, ...] = DEFAULT_ARTIFACT_GLOBS,
) -> ExecutionValidationResult:
    evidence = find_run_evidence(
        run_id,
        base_dir=base_dir,
        ledger_globs=ledger_globs,
        artifact_globs=artifact_globs,
    )
    has_ledger = bool(evidence["ledger_record_ids"])
    has_artifacts = bool(evidence["ledger_artifact_ids"])

    status = ExecutionValidationStatus.NOT_COMPUTABLE
    errors: list[str] = list(evidence["errors"])
    warnings: list[str] = []

    if errors:
        status = ExecutionValidationStatus.FAIL
    elif has_ledger and has_artifacts:
        status = ExecutionValidationStatus.PASS
    elif has_ledger or has_artifacts:
        status = ExecutionValidationStatus.INCOMPLETE
        warnings.append("Partial evidence chain found for run_id; missing ledger or artifact linkage.")
    else:
        warnings.append("No run-linked evidence found in configured ledgers or artifact stores.")

    result = ExecutionValidationResult(
        run_id=run_id,
        artifact_id=build_artifact_id(run_id),
        status=status,
        valid=(status == ExecutionValidationStatus.PASS),
        errors=sorted(errors),
        warnings=sorted(warnings),
        ledger_record_ids=evidence["ledger_record_ids"],
        ledger_artifact_ids=evidence["ledger_artifact_ids"],
        correlation_pointers=evidence["correlation_pointers"],
        checked_at=checked_at or _utc_now_iso(),
        provenance={
            "validator": "abx.execution_validator",
            "version": "mvp.v1",
            "base_dir": str(base_dir),
        },
    )
    return replace(result)


def emit_validation_result(result: ExecutionValidationResult, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{result.artifact_id}.json"
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(to_canon_artifact(result), handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    return out_path
