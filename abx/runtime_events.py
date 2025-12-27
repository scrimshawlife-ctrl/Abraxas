"""Runtime Event Ledger (v0.1) — append-only, deterministic telemetry.

Pure signal capture for rune invocations. Zero coupling, write-only.
Enables drift detection, confidence calibration, and memetic weather analysis.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


# Ledger path (append-only JSONL)
ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "data" / "runtime_events.log"


def _now_ns() -> int:
    """Return current time in nanoseconds (high precision)."""
    return time.time_ns()


def _stable(obj: dict[str, Any]) -> str:
    """Stable JSON serialization (matches governance/provenance patterns)."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def emit(event: dict[str, Any]) -> None:
    """Append a single runtime event to the ledger.

    Args:
        event: Event dict to record (will be serialized as single JSON line)

    Notes:
        - Never raises exceptions (telemetry must never break execution)
        - Never mutates state
        - Append-only (immutable audit trail)
        - Thread-safe via OS-level append semantics
    """
    try:
        LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LEDGER_PATH, "a", encoding="utf-8") as f:
            f.write(_stable(event) + "\n")
    except Exception:
        # Telemetry failures are silent - execution continues
        pass
