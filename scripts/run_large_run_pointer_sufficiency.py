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


def build_pointer_sufficiency_report(
    *,
    base_dir: Path,
    batch_id: str,
    timestamp: str,
    min_pointers: int,
) -> dict[str, Any]:
    validators_dir = base_dir / "out" / "validators"
    rows: list[dict[str, Any]] = []

    for path in sorted(validators_dir.glob("execution-validation-*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        run_id = str(payload.get("runId") or "")
        if not run_id:
            continue
        correlation = payload.get("correlation") if isinstance(payload.get("correlation"), dict) else {}
        raw_pointers = correlation.get("pointers") if isinstance(correlation.get("pointers"), list) else []
        pointers = [str(item) for item in raw_pointers if str(item)]
        pointer_count = len(pointers)
        sufficiency_state = "SUFFICIENT" if pointer_count >= min_pointers else "NOT_COMPUTABLE"
        reason_codes: list[str] = []
        if pointer_count < min_pointers:
            reason_codes.append(f"pointer-count-below-threshold:{pointer_count}<{min_pointers}")

        rows.append(
            {
                "run_id": run_id,
                "sufficiency_state": sufficiency_state,
                "pointer_count": pointer_count,
                "threshold": min_pointers,
                "reason_codes": reason_codes,
                "validator_artifact_id": str(payload.get("artifactId", "MISSING")),
            }
        )

    rows = sorted(rows, key=lambda item: item["run_id"])
    insufficient = [row for row in rows if row["sufficiency_state"] != "SUFFICIENT"]
    status = "SUCCESS" if rows and not insufficient else "NOT_COMPUTABLE"

    artifact = {
        "schema": "LargeRunPointerSufficiency.v1",
        "run_id": f"BATCH::{batch_id}",
        "rune_id": "RUNE.INGEST",
        "artifact_id": f"large-run-pointer-sufficiency-{batch_id}",
        "timestamp": timestamp,
        "phase": "AUDIT",
        "status": status,
        "batch_id": batch_id,
        "inputs": {
            "validators_glob": "out/validators/execution-validation-*.json",
            "min_pointers": min_pointers,
        },
        "outputs": {
            "run_count": len(rows),
            "sufficient_count": len(rows) - len(insufficient),
            "not_computable_count": len(insufficient),
            "runs": rows,
        },
        "provenance": {
            "builder": "scripts.run_large_run_pointer_sufficiency",
            "determinism": "sorted-run-order + static-threshold-policy",
        },
        "correlation_pointers": [f"out/validators/execution-validation-*.json#{batch_id}"],
    }
    return assert_large_run_envelope(artifact)


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit deterministic pointer sufficiency report for large-run validator artifacts.")
    parser.add_argument("--base-dir", default=".", help="Repository base directory.")
    parser.add_argument("--batch-id", required=True, help="Deterministic batch id.")
    parser.add_argument("--min-pointers", type=int, default=1, help="Minimum pointer count per run.")
    parser.add_argument("--timestamp", default=None, help="Optional fixed timestamp.")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    timestamp = args.timestamp or _utc_now_iso()
    report = build_pointer_sufficiency_report(
        base_dir=base_dir,
        batch_id=args.batch_id,
        timestamp=timestamp,
        min_pointers=max(args.min_pointers, 0),
    )

    reports_dir = base_dir / "out" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = reports_dir / f"large_run_pointer_sufficiency_{args.batch_id}.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({"artifact_path": out_path.as_posix(), "status": report["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
