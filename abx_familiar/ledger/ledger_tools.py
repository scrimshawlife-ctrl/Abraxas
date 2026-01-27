"""
Ledger tools (v0.1).

Deterministic helpers for reading last entry and computing continuity metadata.
No IO. No mutation.
"""

from __future__ import annotations

from typing import Optional, Iterable

from abx_familiar.ir.continuity_ledger_v0 import ContinuityLedgerEntry


def get_last_entry(entries: Iterable[ContinuityLedgerEntry]) -> Optional[ContinuityLedgerEntry]:
    """
    Return the last entry in insertion order, or None if empty.
    Deterministic given deterministic iteration order.
    """
    last: Optional[ContinuityLedgerEntry] = None
    for e in entries:
        last = e
    return last
