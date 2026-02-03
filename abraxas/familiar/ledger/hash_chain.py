from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from abraxas.util.canonical_hash import canonical_hash


def build_ledger_event(
    *,
    run_id: str,
    event_type: str,
    payload: Dict[str, Any],
    prev_hash: Optional[str],
) -> Dict[str, Any]:
    event_id_source = {
        "run_id": run_id,
        "prev_hash": prev_hash,
        "payload_hash": canonical_hash(payload),
    }
    event_id = canonical_hash(event_id_source)
    base = {
        "schema_version": "v0",
        "event_id": event_id,
        "event_type": event_type,
        "run_id": run_id,
        "prev_hash": prev_hash,
        "payload": payload,
    }
    event_hash = canonical_hash(base)
    return {**base, "event_hash": event_hash}


def validate_chain(events: Iterable[Dict[str, Any]]) -> bool:
    prev_hash: Optional[str] = None
    for event in events:
        if event.get("prev_hash") != prev_hash:
            return False
        base = {k: v for k, v in event.items() if k != "event_hash"}
        if canonical_hash(base) != event.get("event_hash"):
            return False
        prev_hash = event.get("event_hash")
    return True
