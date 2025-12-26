from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from abraxas.core.provenance import hash_canonical_json


def append_chained_jsonl(path: str | Path, record: Dict[str, Any]) -> None:
    ledger_path = Path(path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    prev_hash = _get_last_hash(ledger_path)
    entry = dict(record)
    entry["prev_hash"] = prev_hash
    entry["step_hash"] = hash_canonical_json(entry)
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def append_epp_ledger(
    pack: Dict[str, Any],
    ledger_path: str | Path = "out/value_ledgers/epp_runs.jsonl",
) -> str:
    path = Path(ledger_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    prev_hash = _get_last_hash(path)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pack_id": pack.get("pack_id"),
        "run_id": pack.get("run_id"),
        "proposal_count": len(pack.get("proposals", [])),
        "proposals_hash": hash_canonical_json(pack.get("proposals", [])),
        "summary_hash": hash_canonical_json(pack.get("summary", {})),
        "prev_hash": prev_hash,
    }
    step_hash = hash_canonical_json(entry)
    entry["step_hash"] = step_hash
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
    return step_hash


def _get_last_hash(path: Path) -> str:
    if not path.exists():
        return "genesis"
    lines = path.read_text().splitlines()
    if not lines:
        return "genesis"
    last = json.loads(lines[-1])
    return last.get("step_hash", "genesis")
