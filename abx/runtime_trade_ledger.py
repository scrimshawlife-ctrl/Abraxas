from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _ledger_path(base_dir: Path, run_id: str, scenario_id: str) -> Path:
    return base_dir / "out" / "ledger" / "runtime_trade_ledger" / run_id / f"{scenario_id}.jsonl"


def write_runtime_trade_ledger(
    *,
    base_dir: Path,
    run_id: str,
    scenario_id: str,
    artifacts: list[dict[str, Any]],
) -> Path:
    ledger_path = _ledger_path(base_dir, run_id, scenario_id)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for index, artifact in enumerate(artifacts):
        artifact_id = str(artifact.get("artifactId") or artifact.get("artifact_id") or f"artifact-{index}")
        record = {
            "kind": "runtime_trade_record",
            "run_id": run_id,
            "scenario_id": scenario_id,
            "artifact_id": artifact_id,
            "artifact_type": str(artifact.get("artifactType") or "unknown"),
            "ordinal": index,
            "lineage": {"run_id": run_id, "scenario_id": scenario_id},
        }
        record["record_id"] = sha256_bytes(dumps_stable(record).encode("utf-8"))
        rows.append(record)

    with ledger_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    return ledger_path


def load_runtime_trade_records(base_dir: Path, run_id: str, scenario_id: str) -> list[dict[str, Any]]:
    ledger_path = _ledger_path(base_dir, run_id, scenario_id)
    if not ledger_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if str(payload.get("run_id") or "") == run_id and str(payload.get("scenario_id") or "") == scenario_id:
            rows.append(payload)
    return rows
