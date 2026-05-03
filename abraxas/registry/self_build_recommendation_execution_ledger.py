from __future__ import annotations

from pathlib import Path
from typing import Any
from datetime import datetime, timezone
import hashlib
import json

LEDGER_PATH = Path("out/registry/self_build_recommendation_execution_ledger.latest.json")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _load() -> dict[str, Any]:
    if not LEDGER_PATH.exists():
        return {"schema_version": "SelfBuildRecommendationExecutionLedger.v1", "entry_count": 0, "entries": []}
    loaded = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {"schema_version": "SelfBuildRecommendationExecutionLedger.v1", "entry_count": 0, "entries": []}


def build_execution_entry(execution_result: dict[str, Any]) -> dict[str, Any]:
    action_id = execution_result.get("action_id")
    action_type = execution_result.get("action_type")
    status = execution_result.get("status", "NOT_COMPUTABLE")
    reason = execution_result.get("reason")
    approval_write = execution_result.get("approval_write") if isinstance(execution_result.get("approval_write"), dict) else None
    approval_id = approval_write.get("approved_ids", [None])[0] if isinstance(approval_write, dict) and approval_write.get("approved_ids") else None
    basis = _canonical({"action_id": action_id, "action_type": action_type, "status": status, "reason": reason})
    execution_id = "exec-" + _sha256_text(basis)[:20]
    approval_write_hash = None if approval_write is None else _sha256_text(_canonical(approval_write))
    entry = {
        "execution_id": execution_id,
        "action_id": action_id,
        "action_type": action_type,
        "approval_id": approval_id,
        "status": "FAILED" if status == "NOT_COMPUTABLE" else ("NO_OP" if action_type == "HOLD" else "EXECUTED"),
        "reason": reason,
        "batch_cycle_hash": execution_result.get("batch_cycle_hash"),
        "approval_write_hash": approval_write_hash,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "authority": {"mutation": False, "execution": False, "analysis_only": True},
    }
    entry["canonical_hash"] = _sha256_text(_canonical(entry))
    return entry


def append_execution_entry(execution_result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(execution_result, dict) or execution_result.get("schema_version") != "SelfBuildRecommendationExecution.v1":
        return {
            "schema_version": "SelfBuildRecommendationExecutionLedger.v1",
            "status": "NOT_COMPUTABLE",
            "reason": "INVALID_EXECUTION_RESULT",
            "entry_count": 0,
            "entries": [],
        }
    ledger = _load()
    entries = ledger.get("entries", []) if isinstance(ledger.get("entries"), list) else []
    entries.append(build_execution_entry(execution_result))
    payload = {
        "schema_version": "SelfBuildRecommendationExecutionLedger.v1",
        "entry_count": len(entries),
        "entries": entries,
        "authority": {"mutation": False, "execution": False, "analysis_only": True},
    }
    payload["canonical_hash"] = _sha256_text(_canonical(payload))
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload
