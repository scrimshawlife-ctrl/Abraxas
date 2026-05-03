from __future__ import annotations

import hashlib
import json
import os
from typing import Any

LEDGER_PATH = "out/registry/self_build_rollback_ledger.latest.json"


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _load_existing() -> dict[str, Any]:
    if not os.path.exists(LEDGER_PATH):
        return {
            "schema_version": "SelfBuildRollbackLedger.v1",
            "entry_count": 0,
            "entries": [],
            "canonical_hash": None,
        }
    with open(LEDGER_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def append_rollback_entry(entry: dict[str, Any]) -> dict[str, Any]:
    ledger = _load_existing()
    base = (
        entry["mutation_id"]
        + entry["target_path"]
        + entry["pre_rollback_hash"]
        + entry.get("restored_hash", "")
        + entry["status"]
    )
    entry["rollback_id"] = _sha256(base)[:24]
    ledger["entries"].append(entry)
    ledger["entry_count"] = len(ledger["entries"])
    ledger["canonical_hash"] = _sha256(_canonical(ledger))
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    with open(LEDGER_PATH, "w", encoding="utf-8") as handle:
        handle.write(_canonical(ledger))
    return ledger
