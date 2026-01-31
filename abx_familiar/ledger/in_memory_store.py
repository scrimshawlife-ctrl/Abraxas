from __future__ import annotations

from typing import Iterable, List

from abx_familiar.ir.continuity_ledger_v0 import ContinuityLedgerEntry


class InMemoryAppendOnlyStore:
    def __init__(self) -> None:
        self._entries: List[ContinuityLedgerEntry] = []

    def append(self, entry: ContinuityLedgerEntry) -> None:
        self._entries.append(entry)

    def read_all(self) -> Iterable[ContinuityLedgerEntry]:
        return list(self._entries)
