from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def task_event(
    *,
    ledger: str,
    run_id: str,
    task_id: str,
    status: str,
    mode: str,
    claim_id: str,
    term: str,
    task_kind: str,
    detail: str,
    artifacts: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    art = artifacts or {}
    if "front_tags" in art:
        ft = art.get("front_tags")
        if isinstance(ft, list):
            art["front_tags"] = [
                str(x).strip().upper() for x in ft if str(x).strip()
            ]
        elif isinstance(ft, str) and ft.strip():
            art["front_tags"] = [ft.strip().upper()]
        else:
            art["front_tags"] = []

    obj = {
        "kind": "task_event",
        "ts": _utc_now_iso(),
        "run_id": run_id,
        "task_id": task_id,
        "status": status,
        "mode": mode,
        "claim_id": claim_id,
        "term": term,
        "task_kind": task_kind,
        "detail": detail,
        "artifacts": art,
    }
    _append_jsonl(ledger, obj)
    return obj


def task_status_change(
    *,
    ledger: str,
    run_id: str,
    task_id: str,
    from_status: str,
    to_status: str,
    reason: str,
    batch_id: str = "",
    artifacts: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    obj = {
        "kind": "task_status_changed",
        "ts": _utc_now_iso(),
        "run_id": run_id,
        "task_id": task_id,
        "from_status": from_status,
        "to_status": to_status,
        "reason": reason,
        "batch_id": batch_id,
        "artifacts": artifacts or {},
    }
    _append_jsonl(ledger, obj)
    return obj
