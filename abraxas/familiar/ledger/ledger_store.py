from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


class InMemoryLedgerStore:
    def __init__(self) -> None:
        self._events: List[Dict[str, Any]] = []

    def append(self, event: Dict[str, Any]) -> None:
        if self._events:
            expected_prev = self._events[-1].get("event_hash")
            if event.get("prev_hash") != expected_prev:
                raise ValueError("ledger append prev_hash mismatch")
        self._events.append(event)

    def read_all(self) -> Iterable[Dict[str, Any]]:
        return list(self._events)

    def last_hash(self) -> Optional[str]:
        if not self._events:
            return None
        return self._events[-1].get("event_hash")
