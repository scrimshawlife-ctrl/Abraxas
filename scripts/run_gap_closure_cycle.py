from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from abraxas.runes.gap_closure.runtime import (
    build_artifact_index,
    build_gap_closure_cycle,
    write_canonical_json,
)
from abraxas.runes.gap_closure.validator import validate_gap_closure_artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic gap-closure cycle.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--mode", default="sandbox")
    parser.add_argument("--workspace-only", action="store_true")
    parser.add_argument("--required-input", type=Path, default=None)
    return parser.parse_args()


def _load_required_input(path: Path | None) -> dict[str, object] | None:
    if path is None:
        return {"input_state": "present", "source": "default"}
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_ledger_row(ledger_path: Path, row: dict[str, str]) -> None:
    existing_rows: list[dict[str, str]] = []
    if ledger_path.exists():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            existing_rows.append(json.loads(line))
    retained = [item for item in existing_rows if item.get("run_id") != row["run_id"]]
    retained.append(row)
    ordered = sorted(retained, key=lambda item: str(item.get("run_id", "")))
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("w", encoding="utf-8") as handle:
        for item in ordered:
            handle.write(json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n")


def main() -> int:
    args = parse_args()
    required_input = _load_required_input(args.required_input)
    run_dir = Path("artifacts_seal/runs") / args.run_id
    out_ledger = Path("out/ledger/gap_closure_runs.jsonl")
    out_ledger.parent.mkdir(parents=True, exist_ok=True)

    cycle = build_gap_closure_cycle(
        run_id=args.run_id,
        mode=args.mode,
        workspace_only=args.workspace_only,
        required_input=required_input,
    )
    run_path = run_dir / "gap_closure_run.json"
    projection_path = run_dir / "live_run_projection.json"
    run_hash = write_canonical_json(run_path, cycle["run_record"])
    projection_hash = write_canonical_json(projection_path, cycle["projection"])

    provisional_report = {
        "schema_version": "closure_validation_report.v1",
        "run_id": args.run_id,
        "status": "PARTIAL",
        "promotion_decision": "HOLD",
        "reason": "validation_pending_artifact_index",
        "authority_boundary": "projection cannot alter canon status",
    }
    report_path = run_dir / "closure_validation_report.json"
    report_hash = write_canonical_json(report_path, provisional_report)

    artifact_index = build_artifact_index(
        run_id=args.run_id,
        provenance=cycle["run_record"]["provenance"],
        input_hash=cycle["input_hash"],
        run_artifact=(run_path.as_posix(), run_hash),
        projection_artifact=(projection_path.as_posix(), projection_hash),
        validation_artifact=(report_path.as_posix(), report_hash),
    )
    index_payload = {
        "schema_version": "gap_closure_artifact_index.v1",
        "run_id": args.run_id,
        "bridge": cycle["bridge"],
        "artifacts": artifact_index,
    }
    write_canonical_json(run_dir / "artifact_index.json", index_payload)

    validation_report = validate_gap_closure_artifacts(
        run_id=args.run_id,
        run_dir=run_dir,
        artifact_index=artifact_index,
    )
    final_report_hash = write_canonical_json(report_path, validation_report)

    validator_payload = {
        "schema_version": "gap_closure.validator.v1",
        "run_id": args.run_id,
        "report_path": report_path.as_posix(),
        "report_hash": final_report_hash,
        "status": validation_report["status"],
        "promotion_decision": validation_report["promotion_decision"],
    }
    write_canonical_json(Path("out/validators") / f"{args.run_id}.gap_closure.validator.json", validator_payload)

    ledger_row = {
        "schema_version": "gap_closure_ledger_row.v1",
        "run_id": args.run_id,
        "input_hash": cycle["input_hash"],
        "status": cycle["status"],
        "validation_status": validation_report["status"],
        "promotion_decision": validation_report["promotion_decision"],
    }
    _write_ledger_row(out_ledger, ledger_row)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
