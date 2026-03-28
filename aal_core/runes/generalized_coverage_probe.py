"""Deterministic non-probe coverage path for closure generalization evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Mapping

from .executor import execute_rune

OUTPUT_DIR = Path("artifacts_seal/runs/generalized_coverage")
VALIDATOR_OUTPUT_DIR = Path("out/validators")
LEDGER_PATH = Path("out/ledger/generalized_coverage_linkage.jsonl")
RUNE_ID = "RUNE.SCAN"
PHASE = "SCAN"
DEFAULT_RUN_ID = "run.generalized_coverage.v1"


def _deterministic_step(inputs: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = inputs.get("payload", {})
    source = payload.get("source", "generalized_coverage") if isinstance(payload, Mapping) else "generalized_coverage"
    return {
        "payload": {
            "scanned": True,
            "record_count": 1,
            "source": source,
        },
        "summary": "Generalized non-probe coverage scan completed.",
        "metrics": {"input_keys": len(payload) if isinstance(payload, Mapping) else 0},
        "errors": [],
    }


def _emit_artifact(*, run_id: str) -> Path:
    inputs: Dict[str, Any] = {
        "payload": {
            "source": "generalized_coverage",
            "signal": "deterministic",
            "mode": "non_probe_coverage",
        },
        "content_hash": "sha256:generalized-coverage-v1",
        "meta": {"coverage_version": "v1"},
    }

    seed_artifact = execute_rune(
        rune_id=RUNE_ID,
        run_id=run_id,
        phase=PHASE,
        step=_deterministic_step,
        inputs=inputs,
        provenance={
            "source_refs": ["coverage://aal-core/non-probe"],
            "operator": "codex",
            "notes": "Deterministic minimal non-probe closure coverage path.",
        },
        ledger_record_ids=[],
        ledger_artifact_ids=[],
        correlation_pointers=[],
    )

    artifact_id = str(seed_artifact.get("artifact_id", ""))
    ledger_record_id = f"generalized-ledger:{run_id}:{artifact_id}" if artifact_id else f"generalized-ledger:{run_id}"
    pointer = f"{LEDGER_PATH.as_posix()}#{ledger_record_id}"

    artifact = execute_rune(
        rune_id=RUNE_ID,
        run_id=run_id,
        phase=PHASE,
        step=_deterministic_step,
        inputs=inputs,
        provenance={
            "source_refs": ["coverage://aal-core/non-probe"],
            "operator": "codex",
            "notes": "Deterministic minimal non-probe closure coverage path.",
            "coverage_path": "generalized_non_probe_minimal",
        },
        ledger_record_ids=[ledger_record_id],
        ledger_artifact_ids=[artifact_id] if artifact_id else [],
        correlation_pointers=[
            {
                "type": "generalized_ledger_record",
                "value": pointer,
                "status": "PRESENT",
                "reason": "DETERMINISTIC_GENERALIZED_COVERAGE",
            }
        ],
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = OUTPUT_DIR / f"{run_id}.artifact.json"
    artifact_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    ledger_row = {
        "run_id": run_id,
        "record_id": ledger_record_id,
        "artifact_id": artifact_id,
        "refs": {"coverage_artifact": artifact_path.as_posix()},
        "source": "aal_core.runes.generalized_coverage_probe",
        "ledger_record_ids": [ledger_record_id],
        "ledger_artifact_ids": [artifact_id] if artifact_id else [],
        "correlation_pointers": [
            {
                "type": "generalized_ledger_record",
                "value": pointer,
                "status": "PRESENT",
                "reason": "DETERMINISTIC_GENERALIZED_COVERAGE",
            }
        ],
    }

    serialized_row = json.dumps(ledger_row, sort_keys=True, separators=(",", ":"))
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    if LEDGER_PATH.exists():
        for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip() == serialized_row:
                break
        else:
            with LEDGER_PATH.open("a", encoding="utf-8") as handle:
                handle.write(serialized_row + "\n")
    else:
        with LEDGER_PATH.open("w", encoding="utf-8") as handle:
            handle.write(serialized_row + "\n")

    return artifact_path


def run_generalized_coverage(*, run_id: str, base_dir: Path = Path("."), out_dir: Path = VALIDATOR_OUTPUT_DIR) -> Path:
    artifact_path = _emit_artifact(run_id=run_id)

    from abx.execution_validator import emit_validation_result, validate_run

    result = validate_run(run_id, base_dir=base_dir)
    validator_output = emit_validation_result(result, out_dir)

    surface = {
        "schema_version": "aal.runes.generalized_coverage_surface.v1",
        "run_id": run_id,
        "artifact_path": artifact_path.as_posix(),
        "validator_output_path": validator_output.as_posix(),
        "validator_status": result.status.value,
        "validator_valid": result.valid,
        "ledger_record_ids": list(result.ledger_record_ids),
        "ledger_artifact_ids": list(result.ledger_artifact_ids),
        "correlation_pointers": list(result.correlation_pointers),
        "validator_surface_status": "SURFACED_TO_VALIDATOR_OUTPUT" if result.ledger_artifact_ids else "UNSURFACED_STRUCTURALLY_AVAILABLE",
    }
    surface_path = OUTPUT_DIR / f"{run_id}.validator_surface.json"
    surface_path.write_text(json.dumps(surface, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return surface_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic non-probe generalized coverage path.")
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID, help="Non-probe run identifier")
    parser.add_argument("--base-dir", default=".", help="Repository base path")
    parser.add_argument("--validator-out-dir", default=str(VALIDATOR_OUTPUT_DIR), help="Directory for validator artifacts")
    args = parser.parse_args()

    output = run_generalized_coverage(run_id=args.run_id, base_dir=Path(args.base_dir), out_dir=Path(args.validator_out_dir))
    print(output.as_posix())


if __name__ == "__main__":
    main()
