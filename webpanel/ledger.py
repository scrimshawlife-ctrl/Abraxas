from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from abraxas.util.canonical_hash import canonical_hash


def _hash_payload(payload: Dict[str, Any]) -> str:
    return canonical_hash(payload)


@dataclass
class LedgerEvent:
    event_id: str
    run_id: str
    event_type: str
    timestamp_utc: str
    data: Dict[str, Any]
    prev_event_hash: Optional[str]
    event_hash: str


class LedgerChain:
    def __init__(self) -> None:
        self._events_by_run: Dict[str, List[LedgerEvent]] = {}

    def append(
        self,
        run_id: str,
        event_id: str,
        event_type: str,
        timestamp_utc: str,
        data: Dict[str, Any],
    ) -> LedgerEvent:
        events = self._events_by_run.setdefault(run_id, [])
        prev_hash = events[-1].event_hash if events else None

        payload = {
            "event_id": event_id,
            "run_id": run_id,
            "event_type": event_type,
            "timestamp_utc": timestamp_utc,
            "data": data,
            "prev_event_hash": prev_hash,
        }
        ev_hash = _hash_payload(payload)
        ev = LedgerEvent(
            event_id=event_id,
            run_id=run_id,
            event_type=event_type,
            timestamp_utc=timestamp_utc,
            data=data,
            prev_event_hash=prev_hash,
            event_hash=ev_hash,
        )
        events.append(ev)
        return ev

    def list_events(self, run_id: str) -> List[LedgerEvent]:
        return list(self._events_by_run.get(run_id, []))

    def chain_valid(self, run_id: str) -> bool:
        events = self._events_by_run.get(run_id, [])
        prev = None
        for ev in events:
            if ev.prev_event_hash != prev:
                return False
            payload = {
                "event_id": ev.event_id,
                "run_id": ev.run_id,
                "event_type": ev.event_type,
                "timestamp_utc": ev.timestamp_utc,
                "data": ev.data,
                "prev_event_hash": ev.prev_event_hash,
            }
            if _hash_payload(payload) != ev.event_hash:
                return False
            prev = ev.event_hash
        return True
