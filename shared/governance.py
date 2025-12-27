# Governance ledger (v0.1) — append-only receipts for state-changing actions

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

DEFAULT_LEDGER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "governance.jsonl"
)


def _stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def record_receipt(
    *,
    action_rune_id: str,
    action_payload: Dict[str, Any],
    evidence_bundle: Dict[str, Any],
    decision: str,
    decided_by: str,
    reason: Optional[str] = None,
    provenance_bundle: Optional[Dict[str, Any]] = None,
    ledger_path: Optional[str] = None,
) -> Dict[str, Any]:
    lp = ledger_path or DEFAULT_LEDGER_PATH
    os.makedirs(os.path.dirname(lp), exist_ok=True)

    ts = datetime.now(timezone.utc).isoformat()

    core = {
        "timestamp_utc": ts,
        "action_rune_id": action_rune_id,
        "action_payload_sha256": _sha256(_stable_json(action_payload)),
        "evidence_sha256": _sha256(_stable_json(evidence_bundle)),
        "decision": decision,
        "decided_by": decided_by,
    }
    receipt_id = _sha256(_stable_json(core))

    receipt = {
        "governance_receipt_id": receipt_id,
        "timestamp_utc": ts,
        "action_rune_id": action_rune_id,
        "action_payload": action_payload,
        "evidence_bundle": evidence_bundle,
        "decision": decision,
        "decided_by": decided_by,
        "reason": reason,
        "provenance_bundle": provenance_bundle or {},
    }

    with open(lp, "a", encoding="utf-8") as file:
        file.write(_stable_json(receipt) + "\n")

    return receipt


def find_receipt(
    receipt_id: str, ledger_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    lp = ledger_path or DEFAULT_LEDGER_PATH
    if not os.path.exists(lp):
        return None
    with open(lp, "r", encoding="utf-8") as file:
        for line in file:
            try:
                receipt = json.loads(line)
            except Exception:
                continue
            if receipt.get("governance_receipt_id") == receipt_id:
                return receipt
    return None
