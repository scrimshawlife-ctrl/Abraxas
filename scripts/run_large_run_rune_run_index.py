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


def build_rune_run_index(
    *,
    base_dir: Path,
    batch_id: str,
    timestamp: str,
) -> dict[str, Any]:
    validators_dir = base_dir / "out" / "validators"
    projections_dir = base_dir / "out" / "operator"

    projection_by_run: dict[str, dict[str, Any]] = {}
    for path in sorted(projections_dir.glob("operator-projection-*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        run_id = payload.get("run_id")
        if isinstance(run_id, str) and run_id:
            projection_by_run[run_id] = payload

    rune_to_rows: dict[str, list[dict[str, Any]]] = {}
    run_count = 0
    for path in sorted(validators_dir.glob("execution-validation-*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        run_id = str(payload.get("runId") or "")
        if not run_id:
            continue
        run_count += 1

        validator_status = str(payload.get("status", "MISSING"))
        rune_context = payload.get("runeContext") if isinstance(payload.get("runeContext"), dict) else {}
        rune_ids_raw = rune_context.get("runeIds") if isinstance(rune_context.get("runeIds"), list) else []
        phases_raw = rune_context.get("phases") if isinstance(rune_context.get("phases"), list) else []
        rune_ids = sorted({str(item) for item in rune_ids_raw if str(item)})
        phases = sorted({str(item) for item in phases_raw if str(item)})

        projection = projection_by_run.get(run_id, {})
        projection_status = str(projection.get("proof_closure_status", "MISSING"))
        projection_artifact_path = f"out/operator/operator-projection-{run_id}.json" if projection else "MISSING"

        for rune_id in rune_ids:
            rune_to_rows.setdefault(rune_id, []).append(
                {
                    "run_id": run_id,
                    "validator_status": validator_status,
                    "projection_status": projection_status,
                    "phases": phases,
                    "validator_artifact_path": f"out/validators/execution-validation-{run_id}.json",
                    "projection_artifact_path": projection_artifact_path,
                }
            )

    rune_entries: list[dict[str, Any]] = []
    for rune_id in sorted(rune_to_rows):
        run_rows = sorted(rune_to_rows[rune_id], key=lambda row: row["run_id"])
        rune_entries.append(
            {
                "rune_id": rune_id,
                "run_count": len(run_rows),
                "runs": run_rows,
            }
        )

    status = "SUCCESS" if rune_entries else "NOT_COMPUTABLE"
    if run_count == 0:
        status = "NOT_COMPUTABLE"

    artifact = {
        "schema": "RuneRunIndex.v1",
        "run_id": f"BATCH::{batch_id}",
        "rune_id": "RUNE.DIFF",
        "artifact_id": f"rune-run-index-{batch_id}",
        "timestamp": timestamp,
        "phase": "AUDIT",
        "status": status,
        "batch_id": batch_id,
        "inputs": {
            "validators_glob": "out/validators/execution-validation-*.json",
            "operator_projection_glob": "out/operator/operator-projection-*.json",
        },
        "outputs": {
            "validator_run_count": run_count,
            "rune_count": len(rune_entries),
            "runes": rune_entries,
        },
        "provenance": {
            "builder": "scripts.run_large_run_rune_run_index",
            "determinism": "sorted-rune-order + sorted-run-order",
        },
        "correlation_pointers": [
            f"out/validators/execution-validation-*.json#{batch_id}",
            f"out/operator/operator-projection-*.json#{batch_id}",
        ],
    }
    return assert_large_run_envelope(artifact)


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit deterministic rune/run index for large-run orchestration.")
    parser.add_argument("--base-dir", default=".", help="Repository base directory.")
    parser.add_argument("--batch-id", required=True, help="Deterministic batch id.")
    parser.add_argument("--timestamp", default=None, help="Optional fixed timestamp.")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    timestamp = args.timestamp or _utc_now_iso()
    artifact = build_rune_run_index(base_dir=base_dir, batch_id=args.batch_id, timestamp=timestamp)

    out_dir = base_dir / "out" / "operator"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "rune_run_index.json"
    out_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({"artifact_path": out_path.as_posix(), "status": artifact["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
