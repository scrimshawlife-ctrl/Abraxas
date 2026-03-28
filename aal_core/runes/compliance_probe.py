"""ABX-Rune compliance probe: minimal rune execution to artifact output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Mapping, Sequence, Tuple

from .executor import NOT_COMPUTABLE, execute_rune

SCHEMA_PATH = Path("aal_core/schemas/rune_execution_artifact.v1.json")
OUTPUT_DIR = Path("artifacts_seal/runs/compliance_probe")
VALIDATOR_OUTPUT_DIR = Path("out/validators")
PROBE_LEDGER_PATH = Path("out/ledger/compliance_probe_linkage.jsonl")
DEFAULT_RUN_ID = "run.compliance_probe.v1"
DEFAULT_LINKAGE_MODE: Literal["absent", "present", "not_computable", "resolve"] = "absent"
RUNE_ID = "RUNE.INGEST"
PHASE = "INGEST"


LinkageMode = Literal["absent", "present", "not_computable", "resolve"]
LINKAGE_SEARCH_ROOTS: Sequence[Path] = (
    Path("artifacts_seal"),
    Path("out/ledger"),
)
LINKAGE_SEARCH_EXTENSIONS = {".json", ".jsonl"}
ValidatorSurfaceStatus = Literal[
    "SURFACED_TO_VALIDATOR_OUTPUT",
    "UNSURFACED_STRUCTURALLY_AVAILABLE",
    "NOT_COMPUTABLE",
]


def _deterministic_step(inputs: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = inputs.get("payload", {})
    return {
        "payload": {
            "ingested": True,
            "record_count": 1,
            "source": payload.get("source", "compliance_probe"),
        },
        "summary": "Compliance probe ingest completed.",
        "metrics": {"input_keys": len(payload) if isinstance(payload, Mapping) else 0},
        "errors": [],
    }


def _required_fields(schema_path: Path) -> Iterable[str]:
    with schema_path.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    return schema.get("required", [])


def _normalize_not_computable(
    artifact: Dict[str, Any], *, reason: str, required_keys: Iterable[str]
) -> Dict[str, Any]:
    normalized = dict(artifact)
    normalized["status"] = NOT_COMPUTABLE
    outputs = dict(normalized.get("outputs", {}))
    errors = list(outputs.get("errors", []))
    errors.append(reason)
    outputs["errors"] = errors
    outputs.setdefault("summary", "Compliance probe not computable.")
    normalized["outputs"] = outputs

    provenance = dict(normalized.get("provenance", {}))
    unresolved = list(provenance.get("unresolved_linkage", []))
    unresolved.append(reason)
    provenance["unresolved_linkage"] = unresolved
    provenance.setdefault("source_refs", [])
    normalized["provenance"] = provenance

    for key in required_keys:
        if key not in normalized:
            if key in {"ledger_record_ids", "ledger_artifact_ids", "correlation_pointers"}:
                normalized[key] = []
            elif key == "provenance":
                normalized[key] = {"source_refs": [], "unresolved_linkage": [reason]}
            elif key in {"inputs", "outputs"}:
                normalized[key] = {}
            elif key == "status":
                normalized[key] = NOT_COMPUTABLE
            else:
                normalized[key] = ""
    return normalized


def _linkage_fields_for_mode(
    mode: LinkageMode, run_id: str
) -> Tuple[List[str], List[str], List[Dict[str, str]], Dict[str, Any]]:
    if mode == "present":
        record_ids = [f"probe-record:{run_id}:v1"]
        artifact_ids = [f"probe-artifact:{run_id}:v1"]
        pointers = [
            {
                "type": "probe_local_correlation",
                "value": f"probe-correlation:{run_id}:v1",
                "status": "PRESENT",
                "reason": "LOCAL_DETERMINISTIC_TEST_LINKAGE",
            }
        ]
        provenance_patch = {
            "linkage_mode": "present",
            "linkage_provenance": "LOCAL_DETERMINISTIC_TEST_LINKAGE",
            "linkage_resolution": "NOT_EXTERNAL_VALIDATOR_OR_LEDGER",
        }
        return record_ids, artifact_ids, pointers, provenance_patch

    if mode == "not_computable":
        provenance_patch = {
            "linkage_mode": "not_computable",
            "linkage_provenance": "LOCAL_DETERMINISTIC_TEST_LINKAGE",
            "unresolved_linkage": ["LINKAGE_NOT_COMPUTABLE"],
        }
        return [], [], [], provenance_patch

    provenance_patch = {
        "linkage_mode": "absent",
        "linkage_provenance": "LOCAL_DETERMINISTIC_TEST_LINKAGE",
        "linkage_resolution": "EXPLICIT_EMPTY_LINKAGE",
    }
    return [], [], [], provenance_patch


def _json_records_from_path(path: Path) -> Iterable[Mapping[str, Any]]:
    if path.suffix == ".json":
        with path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if isinstance(loaded, Mapping):
            yield loaded
        return

    if path.suffix != ".jsonl":
        return

    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            loaded = json.loads(line)
            if isinstance(loaded, Mapping):
                yield loaded


def _extract_linkage_from_record(record: Mapping[str, Any]) -> Tuple[List[str], List[str], List[Dict[str, str]]]:
    record_ids = record.get("ledger_record_ids", [])
    artifact_ids = record.get("ledger_artifact_ids", [])
    pointers = record.get("correlation_pointers", [])

    normalized_record_ids = [value for value in record_ids if isinstance(value, str) and value]
    normalized_artifact_ids = [value for value in artifact_ids if isinstance(value, str) and value]
    normalized_pointers = []
    for pointer in pointers:
        if not isinstance(pointer, Mapping):
            continue
        pointer_type = pointer.get("type")
        pointer_value = pointer.get("value")
        if not isinstance(pointer_type, str) or not isinstance(pointer_value, str):
            continue
        entry: Dict[str, str] = {"type": pointer_type, "value": pointer_value}
        pointer_status = pointer.get("status")
        if isinstance(pointer_status, str):
            entry["status"] = pointer_status
        pointer_reason = pointer.get("reason")
        if isinstance(pointer_reason, str):
            entry["reason"] = pointer_reason
        normalized_pointers.append(entry)
    return normalized_record_ids, normalized_artifact_ids, normalized_pointers


def _resolve_linkage_from_repo(*, run_id: str, artifact_id: str) -> Tuple[List[str], List[str], List[Dict[str, str]], Dict[str, Any]]:
    found_record_ids: set[str] = set()
    found_artifact_ids: set[str] = set()
    found_pointer_keys: set[Tuple[str, str, str, str]] = set()
    found_pointers: List[Dict[str, str]] = []
    source_refs: List[str] = []
    scanned_files = 0

    for root in LINKAGE_SEARCH_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in LINKAGE_SEARCH_EXTENSIONS:
                continue
            scanned_files += 1
            try:
                records = list(_json_records_from_path(path))
            except (OSError, json.JSONDecodeError):
                continue

            matched = False
            for record in records:
                record_run_id = record.get("run_id")
                record_artifact_id = record.get("artifact_id")
                if record_run_id != run_id and record_artifact_id != artifact_id:
                    continue

                matched = True
                record_ids, artifact_ids, pointers = _extract_linkage_from_record(record)
                found_record_ids.update(record_ids)
                found_artifact_ids.update(artifact_ids)
                for pointer in pointers:
                    key = (
                        pointer.get("type", ""),
                        pointer.get("value", ""),
                        pointer.get("status", ""),
                        pointer.get("reason", ""),
                    )
                    if key not in found_pointer_keys:
                        found_pointer_keys.add(key)
                        found_pointers.append(pointer)

            if matched:
                source_refs.append(f"repo://{path.as_posix()}")

    sorted_record_ids = sorted(found_record_ids)
    sorted_artifact_ids = sorted(found_artifact_ids)
    sorted_pointers = sorted(
        found_pointers,
        key=lambda item: (
            item.get("type", ""),
            item.get("value", ""),
            item.get("status", ""),
            item.get("reason", ""),
        ),
    )
    linkage_resolved = bool(sorted_record_ids or sorted_artifact_ids or sorted_pointers)
    unresolved = [] if linkage_resolved else ["REPO_VISIBLE_LINKAGE_NOT_FOUND"]
    provenance_patch: Dict[str, Any] = {
        "linkage_mode": "resolve",
        "linkage_provenance": "REPO_VISIBLE_EVIDENCE_SCAN",
        "linkage_resolution": "RESOLVED" if linkage_resolved else "UNRESOLVED",
        "linkage_scan_roots": [root.as_posix() for root in LINKAGE_SEARCH_ROOTS],
        "linkage_scan_file_count": scanned_files,
        "source_refs": source_refs,
    }
    if unresolved:
        provenance_patch["unresolved_linkage"] = unresolved
    return sorted_record_ids, sorted_artifact_ids, sorted_pointers, provenance_patch


def run_probe(run_id: str, linkage_mode: LinkageMode = DEFAULT_LINKAGE_MODE) -> Path:
    inputs: Dict[str, Any] = {
        "payload": {
            "source": "compliance_probe",
            "signal": "deterministic",
            "linkage_mode": linkage_mode,
        },
        "content_hash": "sha256:compliance-probe-v1",
        "meta": {"probe_version": "v2-linkage"},
    }

    if linkage_mode == "resolve":
        pre_artifact = execute_rune(
            rune_id=RUNE_ID,
            run_id=run_id,
            phase=PHASE,
            step=_deterministic_step,
            inputs=inputs,
            provenance={
                "source_refs": ["probe://abx-rune-compliance"],
                "operator": "codex",
                "notes": "Pre-resolution artifact materialization for deterministic artifact_id.",
            },
            ledger_record_ids=[],
            ledger_artifact_ids=[],
            correlation_pointers=[],
        )
        artifact_id_for_lookup = str(pre_artifact.get("artifact_id", ""))
        (
            ledger_record_ids,
            ledger_artifact_ids,
            correlation_pointers,
            provenance_patch,
        ) = _resolve_linkage_from_repo(run_id=run_id, artifact_id=artifact_id_for_lookup)
    else:
        ledger_record_ids, ledger_artifact_ids, correlation_pointers, provenance_patch = (
            _linkage_fields_for_mode(linkage_mode, run_id)
        )

    provenance: Dict[str, Any] = {
        "source_refs": ["probe://abx-rune-compliance"],
        "operator": "codex",
        "notes": "Minimal deterministic compliance probe.",
        **provenance_patch,
    }

    artifact = execute_rune(
        rune_id=RUNE_ID,
        run_id=run_id,
        phase=PHASE,
        step=_deterministic_step,
        inputs=inputs,
        provenance=provenance,
        ledger_record_ids=ledger_record_ids,
        ledger_artifact_ids=ledger_artifact_ids,
        correlation_pointers=correlation_pointers,
    )

    if linkage_mode == "not_computable":
        artifact = _normalize_not_computable(
            artifact,
            reason="LINKAGE_NOT_COMPUTABLE",
            required_keys=_required_fields(SCHEMA_PATH),
        )

    required = list(_required_fields(SCHEMA_PATH))
    missing = [field for field in required if field not in artifact]
    if missing:
        artifact = _normalize_not_computable(
            artifact,
            reason=f"MISSING_REQUIRED_FIELDS:{','.join(sorted(missing))}",
            required_keys=required,
        )

    if linkage_mode == "resolve":
        probe_pointer = _probe_continuity_pointer(
            run_id=str(artifact.get("run_id", run_id)),
            artifact_id=str(artifact.get("artifact_id", "")),
        )
        pointers = list(artifact.get("correlation_pointers", []))
        pointer_key = (
            probe_pointer.get("type", ""),
            probe_pointer.get("value", ""),
            probe_pointer.get("status", ""),
            probe_pointer.get("reason", ""),
        )
        existing_keys = {
            (
                str(pointer.get("type", "")),
                str(pointer.get("value", "")),
                str(pointer.get("status", "")),
                str(pointer.get("reason", "")),
            )
            for pointer in pointers
            if isinstance(pointer, Mapping)
        }
        if pointer_key not in existing_keys:
            pointers.append(probe_pointer)
            artifact["correlation_pointers"] = sorted(
                pointers,
                key=lambda item: (
                    str(item.get("type", "")),
                    str(item.get("value", "")),
                    str(item.get("status", "")),
                    str(item.get("reason", "")),
                ),
            )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{run_id}.artifact.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(artifact, handle, sort_keys=True, indent=2)
        handle.write("\n")
    _write_probe_ledger_record(artifact=artifact, artifact_path=output_path)
    return output_path


def _write_probe_ledger_record(*, artifact: Mapping[str, Any], artifact_path: Path) -> None:
    PROBE_LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    run_id = str(artifact.get("run_id", ""))
    artifact_id = str(artifact.get("artifact_id", ""))
    if not run_id or not artifact_id:
        return

    ledger_row: Dict[str, Any] = {
        "run_id": run_id,
        "record_id": f"probe-ledger:{run_id}:{artifact_id}",
        "artifact_id": artifact_id,
        "refs": {"compliance_artifact": artifact_path.as_posix()},
        "source": "aal_core.runes.compliance_probe",
    }
    encoded_row = json.dumps(ledger_row, sort_keys=True, separators=(",", ":"))
    if PROBE_LEDGER_PATH.exists():
        with PROBE_LEDGER_PATH.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip() == encoded_row:
                    return

    with PROBE_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(encoded_row)
        handle.write("\n")


def _probe_continuity_pointer(*, run_id: str, artifact_id: str) -> Dict[str, str]:
    record_id = f"probe-ledger:{run_id}:{artifact_id}" if artifact_id else f"probe-ledger:{run_id}"
    return {
        "type": "probe_ledger_record",
        "value": f"{PROBE_LEDGER_PATH.as_posix()}#{record_id}",
        "status": "PRESENT",
        "reason": "DETERMINISTIC_PROBE_LEDGER_CONTINUITY",
    }


def _validator_surface_state(
    probe_artifact_path: Path, validation_payload: Mapping[str, Any]
) -> ValidatorSurfaceStatus:
    probe_name = probe_artifact_path.name
    validated = validation_payload.get("validatedArtifacts", [])
    pointers = (
        validation_payload.get("correlation", {}).get("pointers", [])
        if isinstance(validation_payload.get("correlation"), Mapping)
        else []
    )

    validated_values = [str(value) for value in validated if isinstance(value, str)]
    pointer_values = [str(value) for value in pointers if isinstance(value, str)]
    if probe_name in validated_values:
        return "SURFACED_TO_VALIDATOR_OUTPUT"
    if any(probe_name in value for value in pointer_values):
        return "SURFACED_TO_VALIDATOR_OUTPUT"
    return "UNSURFACED_STRUCTURALLY_AVAILABLE"


def run_validator_surfacing_probe(
    run_id: str,
    *,
    linkage_mode: LinkageMode,
    base_dir: Path = Path("."),
    validator_out_dir: Path = VALIDATOR_OUTPUT_DIR,
) -> Path:
    probe_artifact_path = run_probe(run_id, linkage_mode=linkage_mode)
    with probe_artifact_path.open("r", encoding="utf-8") as handle:
        probe_artifact = json.load(handle)

    surface_status: ValidatorSurfaceStatus = "NOT_COMPUTABLE"
    validator_output_path: str | None = None
    surface_reason = "VALIDATOR_INTEGRATION_NOT_COMPUTABLE"
    try:
        from abx.execution_validator import emit_validation_result, validate_run

        validation_result = validate_run(run_id, base_dir=base_dir)
        validator_path = emit_validation_result(validation_result, validator_out_dir)
        validator_output_path = validator_path.as_posix()
        with validator_path.open("r", encoding="utf-8") as handle:
            validation_payload = json.load(handle)
        surface_status = _validator_surface_state(probe_artifact_path, validation_payload)
        surface_reason = (
            "PROBE_ARTIFACT_VISIBLE_IN_VALIDATOR_OUTPUT"
            if surface_status == "SURFACED_TO_VALIDATOR_OUTPUT"
            else "PROBE_ARTIFACT_NOT_FOUND_IN_VALIDATOR_OUTPUT"
        )
    except Exception as exc:
        surface_status = "NOT_COMPUTABLE"
        surface_reason = f"VALIDATOR_INTEGRATION_EXCEPTION:{type(exc).__name__}"

    surface_artifact = {
        "schema_version": "aal.runes.validator_surface_probe.v1",
        "run_id": str(probe_artifact.get("run_id", run_id)),
        "artifact_id": str(probe_artifact.get("artifact_id", "")),
        "rune_id": str(probe_artifact.get("rune_id", RUNE_ID)),
        "status": str(probe_artifact.get("status", "")),
        "ledger_record_ids": list(probe_artifact.get("ledger_record_ids", [])),
        "ledger_artifact_ids": list(probe_artifact.get("ledger_artifact_ids", [])),
        "correlation_pointers": list(probe_artifact.get("correlation_pointers", [])),
        "validator_surface_status": surface_status,
        "validator_surface_reason": surface_reason,
        "validator_output_path": validator_output_path,
        "probe_artifact_path": probe_artifact_path.as_posix(),
    }
    out_path = OUTPUT_DIR / f"{run_id}.validator_surface_probe.json"
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(surface_artifact, handle, sort_keys=True, indent=2)
        handle.write("\n")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ABX-Rune compliance probe.")
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID, help="Run identifier")
    parser.add_argument(
        "--linkage-mode",
        default=DEFAULT_LINKAGE_MODE,
        choices=("absent", "present", "not_computable", "resolve"),
        help="Linkage emission mode",
    )
    parser.add_argument(
        "--validator-surface-probe",
        action="store_true",
        help="Emit a validator-surfacing probe artifact alongside the compliance artifact.",
    )
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Repository base path used for validator evidence lookup.",
    )
    parser.add_argument(
        "--validator-out-dir",
        default=str(VALIDATOR_OUTPUT_DIR),
        help="Validator output directory for emitted validator artifacts.",
    )
    args = parser.parse_args()
    path = (
        run_validator_surfacing_probe(
            args.run_id,
            linkage_mode=args.linkage_mode,
            base_dir=Path(args.base_dir),
            validator_out_dir=Path(args.validator_out_dir),
        )
        if args.validator_surface_probe
        else run_probe(args.run_id, linkage_mode=args.linkage_mode)
    )
    print(path)


if __name__ == "__main__":
    main()
