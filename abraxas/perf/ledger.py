"""Performance ledger - append-only JSONL for rent metrics.

Performance Drop v1.0 - Provenance-tracked performance metrics.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

from abraxas.perf.schema import PerfEvent


def get_perf_ledger_path() -> Path:
    """Get performance ledger path.

    Returns:
        Path to perf_ledger.jsonl
    """
    repo_root = Path(os.getenv("ABRAXAS_ROOT", Path.cwd()))
    return repo_root / "out" / "ledger" / "perf_ledger.jsonl"


def write_perf_event(event: PerfEvent) -> None:
    """Write performance event to ledger.

    Args:
        event: PerfEvent to write
    """
    ledger_path = get_perf_ledger_path()
    ledger_path.parent.mkdir(parents=True, exist_ok=True)

    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(event.model_dump_json(exclude_none=True) + "\n")


def read_perf_events(
    *,
    since_utc: str | None = None,
    op_name: str | None = None,
    source_id: str | None = None,
) -> list[PerfEvent]:
    """Read performance events from ledger with optional filters.

    Args:
        since_utc: Optional ISO8601 timestamp to filter events after
        op_name: Optional operation name filter
        source_id: Optional source ID filter

    Returns:
        List of PerfEvent objects
    """
    ledger_path = get_perf_ledger_path()
    if not ledger_path.exists():
        return []

    events: list[PerfEvent] = []
    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            event = PerfEvent(**json.loads(line))

            # Apply filters
            if since_utc and event.timestamp_utc < since_utc:
                continue
            if op_name and event.op_name != op_name:
                continue
            if source_id and event.source_id != source_id:
                continue

            events.append(event)

    return events


def summarize_perf(
    window_hours: int = 24,
    *,
    op_name: str | None = None,
    source_id: str | None = None,
) -> dict:
    """Summarize performance metrics for a time window.

    Args:
        window_hours: Time window in hours (default: 24)
        op_name: Optional operation name filter
        source_id: Optional source ID filter

    Returns:
        Summary dict with metrics
    """
    since_utc = (datetime.utcnow() - timedelta(hours=window_hours)).isoformat()
    events = read_perf_events(since_utc=since_utc, op_name=op_name, source_id=source_id)

    if not events:
        return {
            "window_hours": window_hours,
            "event_count": 0,
            "total_bytes_in": 0,
            "total_bytes_out": 0,
            "total_duration_ms": 0,
            "cache_hit_rate": 0.0,
            "avg_compression_ratio": 0.0,
            "decodo_call_count": 0,
        }

    total_bytes_in = sum(e.bytes_in for e in events)
    total_bytes_out = sum(e.bytes_out for e in events)
    total_duration_ms = sum(e.duration_ms for e in events)
    cache_hits = sum(1 for e in events if e.cache_hit)
    decodo_calls = sum(1 for e in events if e.decodo_used)

    compression_ratios = [e.compression_ratio for e in events if e.compression_ratio is not None]
    avg_compression_ratio = (
        sum(compression_ratios) / len(compression_ratios) if compression_ratios else 0.0
    )

    return {
        "window_hours": window_hours,
        "event_count": len(events),
        "total_bytes_in": total_bytes_in,
        "total_bytes_out": total_bytes_out,
        "total_duration_ms": total_duration_ms,
        "cache_hit_rate": cache_hits / len(events) if events else 0.0,
        "avg_compression_ratio": avg_compression_ratio,
        "decodo_call_count": decodo_calls,
        "bytes_saved": total_bytes_in - total_bytes_out,
    }
