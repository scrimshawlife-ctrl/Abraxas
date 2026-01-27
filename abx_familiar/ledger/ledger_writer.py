from __future__ import annotations

from typing import Iterable, Protocol

from abx_familiar.ir.continuity_ledger_v0 import ContinuityLedgerEntry


class LedgerWriter(Protocol):
    def append(self, entry: ContinuityLedgerEntry) -> None:
        ...

    def read_all(self) -> Iterable[ContinuityLedgerEntry]:
        ...
