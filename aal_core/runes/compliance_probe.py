"""ABX-Rune compliance probe: minimal rune execution to artifact output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Mapping, Tuple

from .executor import NOT_COMPUTABLE, execute_rune

SCHEMA_PATH = Path("aal_core/schemas/rune_execution_artifact.v1.json")
OUTPUT_DIR = Path("artifacts_seal/runs/compliance_probe")
DEFAULT_RUN_ID = "run.compliance_probe.v1"
DEFAULT_LINKAGE_MODE: Literal["absent", "present", "not_computable"] = "absent"
RUNE_ID = "RUNE.INGEST"
PHASE = "INGEST"


LinkageMode = Literal["absent", "present", "not_computable"]


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

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{run_id}.artifact.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(artifact, handle, sort_keys=True, indent=2)
        handle.write("\n")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ABX-Rune compliance probe.")
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID, help="Run identifier")
    parser.add_argument(
        "--linkage-mode",
        default=DEFAULT_LINKAGE_MODE,
        choices=("absent", "present", "not_computable"),
        help="Linkage emission mode",
    )
    args = parser.parse_args()
    path = run_probe(args.run_id, linkage_mode=args.linkage_mode)
    print(path)


if __name__ == "__main__":
    main()
