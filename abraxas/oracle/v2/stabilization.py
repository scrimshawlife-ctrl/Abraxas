from __future__ import annotations

import os
from typing import Any, Dict

from abraxas.oracle.v2.ledger import append_stabilization_row


DEFAULT_LEDGER_PATH = os.environ.get(
    "ABX_V2_LEDGER_PATH",
    "var/ledger/oracle_v2_stabilization.jsonl",
)


def compute_next_day(existing_lines: int) -> int:
    # Deterministic: day = (existing lines) + 1
    return int(existing_lines) + 1


def count_lines(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return 0


def stabilization_tick(
    *,
    v2_block: Dict[str, Any],
    ledger_path: str | None = None,
    date_iso: str | None = None,
) -> Dict[str, Any]:
    """
    Appends one stabilization row and returns it.
    No side effects besides JSONL append.
    """
    lp = ledger_path or DEFAULT_LEDGER_PATH
    n = count_lines(lp)
    day = compute_next_day(n)
    return append_stabilization_row(path=lp, v2_block=v2_block, day=day, date_iso=date_iso)
