from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abraxas.runes.gap_closure.common import GAP_CLOSURE_ARTIFACT_TYPES, stable_sha256_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Log deterministic gap-closure invariance rows.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--mode", default="sandbox")
    parser.add_argument("--workspace-scope", default="workspace_only")
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts_seal/runs"))
    parser.add_argument("--ledger-path", type=Path, default=Path("out/ledger/abx_invariance_tracker.jsonl"))
    parser.add_argument("--report-path", type=Path, default=None)
    return parser.parse_args()


def _load_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _load_previous_rows(report_path: Path) -> list[dict[str, Any]]:
    if not report_path.exists():
        return []
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    rows = payload.get("rows", [])
    return [dict(row) for row in rows]


def _transition(previous_state: str | None, hash_status: str) -> str:
    if hash_status == "NOT_RUN":
        return "UNCHECKED"
    if hash_status == "MISMATCH":
        if previous_state == "STABLE":
            return "REOPEN_REQUIRED"
        return "DRIFT_DETECTED"
    if previous_state == "UNCHECKED":
        return "PROVISIONAL"
    if previous_state in {"PROVISIONAL", "STABLE"}:
        return "STABLE"
    return "PROVISIONAL"


def _build_row(
    *,
    run_id: str,
    mode: str,
    workspace_scope: str,
    artifact_type: str,
    artifact_path: Path,
    previous: dict[str, Any] | None,
    validator_status: str,
) -> dict[str, Any]:
    if not artifact_path.exists():
        return {
            "Name": f"{run_id}:{artifact_type}",
            "Run ID": run_id,
            "Artifact Type": artifact_type,
            "Artifact Path": artifact_path.as_posix(),
            "Artifact Hash": "NOT_COMPUTABLE",
            "Execution Mode": mode,
            "Workspace Scope": workspace_scope,
            "Determinism Pair Status": "NOT_RUN",
            "Invariance State": "BLOCKED",
            "Drift Severity": "BLOCKED",
            "Repair Loop Reopened": False,
            "Validator Status": validator_status,
            "Promotion Recommendation": "BLOCK",
            "Notes": "missing artifact",
        }

    artifact_hash = stable_sha256_file(artifact_path)
    if previous is None:
        determinism_status = "NOT_RUN"
    elif previous.get("Artifact Hash") == artifact_hash:
        determinism_status = "MATCH"
    else:
        determinism_status = "MISMATCH"
    invariance_state = _transition(previous.get("Invariance State") if previous else None, determinism_status)
    drift_severity = "LOW" if determinism_status in {"NOT_RUN", "MATCH"} else "HIGH"
    return {
        "Name": f"{run_id}:{artifact_type}",
        "Run ID": run_id,
        "Artifact Type": artifact_type,
        "Artifact Path": artifact_path.as_posix(),
        "Artifact Hash": artifact_hash,
        "Execution Mode": mode,
        "Workspace Scope": workspace_scope,
        "Determinism Pair Status": determinism_status,
        "Invariance State": invariance_state,
        "Drift Severity": drift_severity,
        "Repair Loop Reopened": invariance_state == "REOPEN_REQUIRED",
        "Validator Status": validator_status,
        "Promotion Recommendation": "HOLD",
        "Notes": "artifact hash compared against local invariance ledger",
    }


def main() -> int:
    args = parse_args()
    run_dir = args.artifacts_dir / args.run_id
    report_path = args.report_path or Path("out/reports") / f"{args.run_id}.abx_invariance_tracker_rows.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    args.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    validator_path = Path("out/validators") / f"{args.run_id}.gap_closure.validator.json"
    validator_status = "NOT_COMPUTABLE"
    if validator_path.exists():
        validator_status = str(json.loads(validator_path.read_text(encoding="utf-8")).get("status", "NOT_COMPUTABLE"))

    history = _load_rows(args.ledger_path)
    if not history:
        history = _load_previous_rows(report_path)
    previous_by_type: dict[str, dict[str, Any]] = {}
    for row in history:
        if row.get("Run ID") == args.run_id and row.get("Artifact Type"):
            previous_by_type[str(row["Artifact Type"])] = row

    rows: list[dict[str, Any]] = []
    for artifact_type, artifact_name in GAP_CLOSURE_ARTIFACT_TYPES:
        row = _build_row(
            run_id=args.run_id,
            mode=args.mode,
            workspace_scope=args.workspace_scope,
            artifact_type=artifact_type,
            artifact_path=run_dir / artifact_name,
            previous=previous_by_type.get(artifact_type),
            validator_status=validator_status,
        )
        rows.append(row)

    with args.ledger_path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")

    report_payload = {
        "schema_version": "abx_invariance_tracker_rows.v0.1",
        "run_id": args.run_id,
        "rows": rows,
    }
    report_path.write_text(json.dumps(report_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
