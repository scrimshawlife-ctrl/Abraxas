from __future__ import annotations

import json
import re
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from abx.execution_validation_types import ExecutionValidationResult, ExecutionValidationStatus

DEFAULT_LEDGER_GLOBS = (
    "out/ledger/*.jsonl",
    "out/evolution_ledgers/*.jsonl",
    "out/forecast_ledger/*.jsonl",
    "out/value_ledgers/*.jsonl",
    ".aal/ledger/*.jsonl",
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

ID_KEYS = (
    "record_id",
    "event_id",
    "id",
    "sha256",
    "ledger_sha256",
    "step_hash",
    "ctx_hash",
    "bundle_hash",
)

ARTIFACT_ID_KEYS = (
    "artifact_id",
    "bundle_id",
    "manifest_id",
    "proof_id",
    "admission_id",
    "packet_id",
    "sha256",
    "snapshot_sha256",
)

PACKET_ID_KEYS = (
    "packet_id",
    "packetId",
)


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


def _run_aliases(run_id: str) -> set[str]:
    aliases = {run_id, run_id.lower()}
    m = re.match(r"^RUN-([A-Z0-9_]+)-\d+$", run_id, flags=re.IGNORECASE)
    if m:
        stem = m.group(1)
        # Bounded aliases only for observed real-data variants.
        # Current repository evidence maps RUN-SEAL-* operator IDs to run_id="seal".
        if stem.lower() == "seal":
            aliases.update({stem, stem.lower()})
    return {a for a in aliases if a}


def _extract_strings_for_keys(obj: Any, keys: Iterable[str], *, max_depth: int = 6) -> list[str]:
    wanted = {k for k in keys}
    out: list[str] = []

    def walk(node: Any, depth: int) -> None:
        if depth < 0:
            return
        if isinstance(node, dict):
            for k, v in node.items():
                if k in wanted and isinstance(v, (str, int, float)):
                    out.append(str(v))
                walk(v, depth - 1)
        elif isinstance(node, list):
            for item in node:
                walk(item, depth - 1)

    walk(obj, max_depth)
    return out


def _extract_run_values(obj: dict[str, Any]) -> set[str]:
    values = set(_extract_strings_for_keys(obj, ("run_id", "runId")))
    return {v for v in values if v}


def _matches_run(run_id: str, row: dict[str, Any]) -> bool:
    aliases = _run_aliases(run_id)
    for candidate in _extract_run_values(row):
        if candidate in aliases or candidate.lower() in aliases:
            return True
    return False


def _path_matches_alias(path: Path, aliases: set[str]) -> bool:
    path_str = path.as_posix().lower()
    name = path.name.lower()
    for alias in aliases:
        alias_l = alias.lower()
        if not alias_l:
            continue
        # full operator run ids are safe to use as direct substring matches
        # because they are high-specificity tokens (e.g., RUN-FOO-0001).
        if alias_l.startswith("run-") and (alias_l in path_str or alias_l in name):
            return True
        # segment match: /<alias>/
        if f"/{alias_l}/" in path_str:
            return True
        # filename prefix/suffix boundary match
        if name == alias_l:
            return True
        if name.startswith(f"{alias_l}.") or name.startswith(f"{alias_l}_") or name.endswith(f".{alias_l}.json"):
            return True
    return False


def to_canon_artifact(
    result: ExecutionValidationResult,
    *,
    validator_id: str = "abx.execution_validator",
    artifact_type: str = "ExecutionValidationArtifact.v1",
) -> dict[str, Any]:
    packet_ids = sorted(set((result.provenance or {}).get("packet_ids", [])))
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
            "packetIds": packet_ids,
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
    aliases = _run_aliases(run_id)
    ledger_record_ids: list[str] = []
    ledger_artifact_ids: list[str] = []
    packet_ids: list[str] = []
    correlation_pointers: list[str] = []
    errors: list[str] = []

    for pattern in ledger_globs:
        for ledger_path in sorted(base_dir.glob(pattern)):
            for line_no, row in _read_jsonl(ledger_path):
                if not _matches_run(run_id, row):
                    continue
                row_ids = _extract_strings_for_keys(row, ID_KEYS)
                rec_id = row_ids[0] if row_ids else f"{ledger_path.name}:{line_no}"
                ledger_record_ids.append(str(rec_id))

                ledger_artifact_ids.extend(_extract_strings_for_keys(row, ARTIFACT_ID_KEYS))
                packet_ids.extend(_extract_strings_for_keys(row, PACKET_ID_KEYS))
                correlation_pointers.append(f"{ledger_path.as_posix()}:{line_no}")

    for pattern in artifact_globs:
        for path in sorted(base_dir.glob(pattern)):
            if not path.is_file():
                continue
            path_str = path.as_posix()
            path_match = _path_matches_alias(path, aliases)

            row: dict[str, Any] = {}
            if path.suffix == ".json":
                try:
                    row = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    row = {}
            content_match = isinstance(row, dict) and _matches_run(run_id, row)

            if not (path_match or content_match):
                continue

            ledger_artifact_ids.append(path.name)
            if isinstance(row, dict):
                ledger_artifact_ids.extend(_extract_strings_for_keys(row, ARTIFACT_ID_KEYS))
                packet_ids.extend(_extract_strings_for_keys(row, PACKET_ID_KEYS))
            correlation_pointers.append(path_str)

    # Deduplicate deterministically.
    ledger_record_ids = sorted(set(ledger_record_ids))
    ledger_artifact_ids = sorted(set(ledger_artifact_ids))
    packet_ids = sorted(set(packet_ids))
    correlation_pointers = sorted(set(correlation_pointers))

    return {
        "ledger_record_ids": ledger_record_ids,
        "ledger_artifact_ids": ledger_artifact_ids,
        "packet_ids": packet_ids,
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
            "version": "mvp.v2",
            "base_dir": str(base_dir),
            "packet_ids": evidence["packet_ids"],
            "run_aliases": sorted(_run_aliases(run_id)),
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
