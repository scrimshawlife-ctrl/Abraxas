from __future__ import annotations

from pathlib import Path

from aatf.config import LEDGER_ROOT


def local_ledger_path(name: str) -> Path:
    return LEDGER_ROOT / f"{name}.jsonl"
