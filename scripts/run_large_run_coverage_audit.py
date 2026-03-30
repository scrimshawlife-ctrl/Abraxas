from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.large_run_contracts import assert_large_run_envelope


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _extract_run_id_from_validator(path: Path, payload: dict[str, Any]) -> str:
    run_id = payload.get("runId")
    if isinstance(run_id, str) and run_id:
        return run_id
    name = path.name
    prefix = "execution-validation-"
    suffix = ".json"
    if name.startswith(prefix) and name.endswith(suffix):
        return name[len(prefix) : -len(suffix)]
    return ""


def build_large_run_coverage_artifact(
    *,
    base_dir: Path,
    batch_id: str,
    timestamp: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    validators_dir = base_dir / "out" / "validators"
    projection_dir = base_dir / "out" / "operator"
    ledger_path = base_dir / "out" / "ledger" / "large_run_coverage.jsonl"

    validator_payloads: dict[str, dict[str, Any]] = {}
    for path in sorted(validators_dir.glob("execution-validation-*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        run_id = _extract_run_id_from_validator(path, payload)
        if run_id:
            validator_payloads[run_id] = payload

    projection_payloads: dict[str, dict[str, Any]] = {}
    for path in sorted(projection_dir.glob("operator-projection-*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        run_id = payload.get("run_id")
        if isinstance(run_id, str) and run_id:
            projection_payloads[run_id] = payload

    run_ids = sorted(set(validator_payloads) | set(projection_payloads))
    runs: list[dict[str, Any]] = []
    ledger_rows: list[dict[str, Any]] = []

    for run_id in run_ids:
        validator = validator_payloads.get(run_id, {})
        projection = projection_payloads.get(run_id, {})
        validator_status = str(validator.get("status", "MISSING"))
        projection_status = str(projection.get("proof_closure_status", "MISSING"))
        coverage_state = "COVERED" if (validator and projection) else "NOT_COMPUTABLE"
        reasons: list[str] = []
        if not validator:
            reasons.append("missing-validator-artifact")
        if not projection:
            reasons.append("missing-operator-projection")

        row = {
            "run_id": run_id,
            "coverage_state": coverage_state,
            "reason_codes": reasons,
            "validator_status": validator_status,
            "projection_status": projection_status,
            "validator_artifact_id": str(validator.get("artifactId", "MISSING")),
            "projection_schema": str(projection.get("schema", "MISSING")),
        }
        runs.append(row)
        ledger_rows.append(
            {
                "event_id": f"large-run-coverage:{batch_id}:{run_id}",
                "run_id": run_id,
                "batch_id": batch_id,
                "rune_id": "RUNE.DIFF",
                "status": coverage_state,
                "timestamp": timestamp,
                "artifact_id": f"large-run-coverage-{batch_id}",
                "refs": {"coverage_artifact": f"out/reports/large_run_coverage_{batch_id}.json"},
            }
        )

    overall_status = "SUCCESS" if all(r["coverage_state"] == "COVERED" for r in runs) else "NOT_COMPUTABLE"
    artifact = {
        "schema": "LargeRunCoverageAudit.v1",
        "run_id": f"BATCH::{batch_id}",
        "rune_id": "RUNE.DIFF",
        "artifact_id": f"large-run-coverage-{batch_id}",
        "timestamp": timestamp,
        "phase": "AUDIT",
        "status": overall_status,
        "batch_id": batch_id,
        "inputs": {
            "validators_glob": "out/validators/execution-validation-*.json",
            "projection_glob": "out/operator/operator-projection-*.json",
        },
        "outputs": {
            "run_count": len(runs),
            "covered_count": sum(1 for r in runs if r["coverage_state"] == "COVERED"),
            "not_computable_count": sum(1 for r in runs if r["coverage_state"] == "NOT_COMPUTABLE"),
            "runs": runs,
        },
        "provenance": {
            "builder": "scripts.run_large_run_coverage_audit",
            "ledger_path": ledger_path.as_posix(),
        },
        "correlation_pointers": [ledger_path.as_posix()],
    }
    return assert_large_run_envelope(artifact), ledger_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit deterministic large-run coverage audit artifact.")
    parser.add_argument("--base-dir", default=".", help="Repository base directory.")
    parser.add_argument("--batch-id", required=True, help="Deterministic batch id for audit scope.")
    parser.add_argument("--timestamp", default=None, help="Optional fixed timestamp for deterministic tests.")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    timestamp = args.timestamp or _utc_now_iso()
    artifact, ledger_rows = build_large_run_coverage_artifact(base_dir=base_dir, batch_id=args.batch_id, timestamp=timestamp)

    reports_dir = base_dir / "out" / "reports"
    ledger_dir = base_dir / "out" / "ledger"
    reports_dir.mkdir(parents=True, exist_ok=True)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    artifact_path = reports_dir / f"large_run_coverage_{args.batch_id}.json"
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    ledger_path = ledger_dir / "large_run_coverage.jsonl"
    with ledger_path.open("a", encoding="utf-8") as handle:
        for row in ledger_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    print(json.dumps({"artifact_path": artifact_path.as_posix(), "status": artifact["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
