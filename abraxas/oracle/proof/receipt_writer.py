from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from abraxas.core.canonical import canonical_json


def write_receipt_artifacts(
    *,
    output: Mapping[str, object],
    invariance: Mapping[str, object],
    validator_summary: Mapping[str, object],
    out_dir: str,
) -> dict:
    run_id = str(output.get("run_id"))
    out_root = Path(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    runtime_path = out_root / f"oracle_signal_layer_output_{run_id}.json"
    invariance_path = out_root / f"oracle_invariance_{run_id}.json"
    validator_path = out_root / f"oracle_validator_summary_{run_id}.json"

    runtime_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    invariance_path.write_text(json.dumps(invariance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validator_path.write_text(json.dumps(validator_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    ledger_row = {
        "schema_id": "OracleSignalLayerLedgerRow.v2",
        "run_id": run_id,
        "runtime_artifact": str(runtime_path),
        "invariance_artifact": str(invariance_path),
        "validator_artifact": str(validator_path),
        "hashes": dict(validator_summary.get("hashes") or {}),
    }
    ledger = Path("out/ledger/oracle_signal_layer_v2_runs.jsonl")
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as f:
        f.write(canonical_json(ledger_row) + "\n")

    return {
        "runtime_artifact": str(runtime_path),
        "invariance_artifact": str(invariance_path),
        "validator_artifact": str(validator_path),
        "ledger_path": str(ledger),
    }
