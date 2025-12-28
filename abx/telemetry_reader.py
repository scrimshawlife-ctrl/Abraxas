"""Telemetry Reader (v0.1) — read-only utilities for runtime_events.log.

Provides safe, read-only access to the runtime event ledger for offline analysis.
Zero coupling back into runtime - pure interpretation infrastructure.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator


# Runtime events ledger path (from runtime_events.py)
ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "runtime_events.log"


def iter_events() -> Iterator[dict[str, Any]]:
    """Iterate over all runtime events in the ledger.

    Yields:
        Event dicts from the ledger, one per line

    Notes:
        - Returns empty iterator if ledger doesn't exist
        - Skips blank lines silently
        - Skips malformed JSON silently
        - Read-only, never modifies ledger
        - Safe to call from multiple processes
    """
    if not LEDGER.exists():
        return

    with LEDGER.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                # Skip malformed lines silently
                continue
