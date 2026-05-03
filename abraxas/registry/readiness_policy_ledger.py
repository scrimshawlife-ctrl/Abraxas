from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _hash(obj: Any) -> str:
    return hashlib.sha256(_canonical(obj).encode()).hexdigest()


def _fail(reason: str) -> dict[str, Any]:
    payload = {
        "schema_version": "ReadinessPolicyLedger.v1",
        "status": "NOT_COMPUTABLE",
        "reason": reason,
        "entries": [],
        "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True},
    }
    payload["canonical_hash"] = _hash(payload)
    return payload


def append_readiness_policy_ledger() -> dict[str, Any]:
    readiness_path = Path("out/registry/self_build_readiness_gate.latest.json")
    if not readiness_path.exists():
        return _fail("MISSING_READINESS_OUTPUT")

    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    if not isinstance(readiness, dict) or readiness.get("schema_version") != "SelfBuildReadinessGate.v1":
        return _fail("INVALID_READINESS_OUTPUT")

    ledger_path = Path("out/registry/readiness_policy_ledger.latest.json")
    entries: list[dict[str, Any]] = []
    if ledger_path.exists():
        current = json.loads(ledger_path.read_text(encoding="utf-8"))
        if isinstance(current, dict) and isinstance(current.get("entries"), list):
            entries = [e for e in current["entries"] if isinstance(e, dict)]

    entry = {
        "policy_hash": readiness.get("policy_hash"),
        "policy_schema_version": readiness.get("policy_schema_version"),
        "policy_path": readiness.get("policy_path"),
        "policy_fields_used": readiness.get("policy_fields_used", []),
        "readiness_status": readiness.get("status"),
        "readiness_hash": readiness.get("canonical_hash"),
        "blockers": readiness.get("blockers", []),
    }
    entry["canonical_hash"] = _hash(entry)
    entries.append(entry)

    payload = {
        "schema_version": "ReadinessPolicyLedger.v1",
        "status": "LEDGER_READY",
        "entries": entries,
        "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True},
    }
    payload["canonical_hash"] = _hash(payload)
    return payload
