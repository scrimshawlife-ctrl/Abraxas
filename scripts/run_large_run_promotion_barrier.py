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


def _extract_run_id(path: Path, payload: dict[str, Any]) -> str:
    run_id = payload.get("run_id")
    if isinstance(run_id, str) and run_id:
        return run_id
    run_id = payload.get("runId")
    if isinstance(run_id, str) and run_id:
        return run_id
    name = path.name
    prefix = "promotion-policy-"
    suffix = ".json"
    if name.startswith(prefix) and name.endswith(suffix):
        return name[len(prefix) : -len(suffix)]
    return ""


def build_large_run_promotion_barrier(
    *,
    base_dir: Path,
    batch_id: str,
    timestamp: str,
) -> dict[str, Any]:
    policy_dir = base_dir / "out" / "policy"
    run_rows: list[dict[str, Any]] = []

    for path in sorted(policy_dir.glob("promotion-policy-*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        run_id = _extract_run_id(path, payload)
        if not run_id:
            continue
        decision_state = str(payload.get("decision_state") or payload.get("decisionState") or "NOT_COMPUTABLE")
        reason_codes = payload.get("reason_codes") if isinstance(payload.get("reason_codes"), list) else []
        reason_codes = [str(code) for code in reason_codes]

        row_status = "ALLOWED" if decision_state == "ALLOWED" else "BLOCKED"
        if decision_state == "NOT_COMPUTABLE":
            row_status = "NOT_COMPUTABLE"

        run_rows.append(
            {
                "run_id": run_id,
                "decision_state": decision_state,
                "barrier_status": row_status,
                "reason_codes": reason_codes,
                "policy_artifact_path": path.as_posix(),
            }
        )

    run_rows = sorted(run_rows, key=lambda row: row["run_id"])
    allowed = [row for row in run_rows if row["barrier_status"] == "ALLOWED"]
    blocked = [row for row in run_rows if row["barrier_status"] == "BLOCKED"]
    not_computable = [row for row in run_rows if row["barrier_status"] == "NOT_COMPUTABLE"]

    aggregate_state = "NOT_COMPUTABLE"
    if run_rows and not blocked and not not_computable:
        aggregate_state = "SUCCESS"
    elif blocked:
        aggregate_state = "BLOCKED"

    artifact = {
        "schema": "LargeRunPromotionBarrier.v1",
        "run_id": f"BATCH::{batch_id}",
        "rune_id": "RUNE.DIFF",
        "artifact_id": f"large-run-barrier-{batch_id}",
        "timestamp": timestamp,
        "phase": "AUDIT",
        "status": aggregate_state,
        "batch_id": batch_id,
        "inputs": {"policy_glob": "out/policy/promotion-policy-*.json"},
        "outputs": {
            "run_count": len(run_rows),
            "allowed_count": len(allowed),
            "blocked_count": len(blocked),
            "not_computable_count": len(not_computable),
            "runs": run_rows,
        },
        "provenance": {
            "builder": "scripts.run_large_run_promotion_barrier",
            "determinism": "sorted-run-order + fail-closed aggregate state",
        },
        "correlation_pointers": [f"out/policy/promotion-policy-*.json#{batch_id}"],
    }
    return assert_large_run_envelope(artifact)


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit deterministic large-run promotion barrier artifact.")
    parser.add_argument("--base-dir", default=".", help="Repository base directory.")
    parser.add_argument("--batch-id", required=True, help="Deterministic batch id.")
    parser.add_argument("--timestamp", default=None, help="Optional fixed timestamp.")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    timestamp = args.timestamp or _utc_now_iso()
    artifact = build_large_run_promotion_barrier(base_dir=base_dir, batch_id=args.batch_id, timestamp=timestamp)

    out_dir = base_dir / "out" / "policy"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"large_run_barrier_{args.batch_id}.json"
    out_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({"artifact_path": out_path.as_posix(), "status": artifact["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
