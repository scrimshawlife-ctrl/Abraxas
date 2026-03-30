from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.large_run_contracts import assert_large_run_envelope
from scripts.run_large_run_coverage_audit import build_large_run_coverage_artifact
from scripts.run_large_run_pointer_sufficiency import build_pointer_sufficiency_report
from scripts.run_large_run_promotion_barrier import build_large_run_promotion_barrier
from scripts.run_large_run_rune_run_index import build_rune_run_index


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_large_run_convergence_bundle(
    *,
    base_dir: Path,
    batch_id: str,
    timestamp: str,
    min_pointers: int,
) -> dict[str, Any]:
    coverage, ledger_rows = build_large_run_coverage_artifact(base_dir=base_dir, batch_id=batch_id, timestamp=timestamp)
    pointer = build_pointer_sufficiency_report(
        base_dir=base_dir,
        batch_id=batch_id,
        timestamp=timestamp,
        min_pointers=min_pointers,
    )
    rune_index = build_rune_run_index(base_dir=base_dir, batch_id=batch_id, timestamp=timestamp)
    barrier = build_large_run_promotion_barrier(base_dir=base_dir, batch_id=batch_id, timestamp=timestamp)

    component_statuses = {
        "coverage": str(coverage.get("status", "NOT_COMPUTABLE")),
        "pointer_sufficiency": str(pointer.get("status", "NOT_COMPUTABLE")),
        "rune_run_index": str(rune_index.get("status", "NOT_COMPUTABLE")),
        "promotion_barrier": str(barrier.get("status", "NOT_COMPUTABLE")),
    }
    overall_status = "SUCCESS" if all(value == "SUCCESS" for value in component_statuses.values()) else "NOT_COMPUTABLE"
    if component_statuses["promotion_barrier"] == "BLOCKED":
        overall_status = "BLOCKED"

    blocked_components = sorted(name for name, state in component_statuses.items() if state != "SUCCESS")
    artifact = {
        "schema": "LargeRunConvergenceBundle.v1",
        "run_id": f"BATCH::{batch_id}",
        "rune_id": "RUNE.DIFF",
        "artifact_id": f"large-run-convergence-{batch_id}",
        "timestamp": timestamp,
        "phase": "AUDIT",
        "status": overall_status,
        "batch_id": batch_id,
        "inputs": {"min_pointers": min_pointers},
        "outputs": {
            "component_statuses": component_statuses,
            "blocked_components": blocked_components,
            "coverage_run_count": int(coverage.get("outputs", {}).get("run_count", 0)),
            "pointer_run_count": int(pointer.get("outputs", {}).get("run_count", 0)),
            "rune_count": int(rune_index.get("outputs", {}).get("rune_count", 0)),
            "barrier_run_count": int(barrier.get("outputs", {}).get("run_count", 0)),
            "coverage_ledger_rows": len(ledger_rows),
        },
        "provenance": {
            "builder": "scripts.run_large_run_convergence",
            "determinism": "fixed timestamp + sorted downstream builders",
        },
        "correlation_pointers": [
            f"out/reports/large_run_coverage_{batch_id}.json",
            f"out/reports/large_run_pointer_sufficiency_{batch_id}.json",
            "out/operator/rune_run_index.json",
            f"out/policy/large_run_barrier_{batch_id}.json",
        ],
    }
    return assert_large_run_envelope(artifact)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic large-run convergence bundle.")
    parser.add_argument("--base-dir", default=".", help="Repository base directory.")
    parser.add_argument("--batch-id", required=True, help="Deterministic batch id.")
    parser.add_argument("--min-pointers", type=int, default=1, help="Pointer threshold.")
    parser.add_argument("--timestamp", default=None, help="Optional fixed timestamp.")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    timestamp = args.timestamp or _utc_now_iso()
    min_pointers = max(args.min_pointers, 0)

    coverage, ledger_rows = build_large_run_coverage_artifact(base_dir=base_dir, batch_id=args.batch_id, timestamp=timestamp)
    pointer = build_pointer_sufficiency_report(
        base_dir=base_dir,
        batch_id=args.batch_id,
        timestamp=timestamp,
        min_pointers=min_pointers,
    )
    rune_index = build_rune_run_index(base_dir=base_dir, batch_id=args.batch_id, timestamp=timestamp)
    barrier = build_large_run_promotion_barrier(base_dir=base_dir, batch_id=args.batch_id, timestamp=timestamp)
    bundle = build_large_run_convergence_bundle(
        base_dir=base_dir,
        batch_id=args.batch_id,
        timestamp=timestamp,
        min_pointers=min_pointers,
    )

    _write_json(base_dir / "out" / "reports" / f"large_run_coverage_{args.batch_id}.json", coverage)
    _write_json(base_dir / "out" / "reports" / f"large_run_pointer_sufficiency_{args.batch_id}.json", pointer)
    _write_json(base_dir / "out" / "operator" / "rune_run_index.json", rune_index)
    _write_json(base_dir / "out" / "policy" / f"large_run_barrier_{args.batch_id}.json", barrier)
    _write_json(base_dir / "out" / "reports" / f"large_run_convergence_{args.batch_id}.json", bundle)

    ledger_path = base_dir / "out" / "ledger" / "large_run_coverage.jsonl"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as handle:
        for row in ledger_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    print(json.dumps({"artifact_path": f"out/reports/large_run_convergence_{args.batch_id}.json", "status": bundle["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
