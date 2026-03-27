from __future__ import annotations

from abx.knowledge.types import MemoryRetentionRecord


def build_retention_policy() -> list[MemoryRetentionRecord]:
    rows = [
        MemoryRetentionRecord("memory.baseline.current", "retain_latest", "never"),
        MemoryRetentionRecord("memory.continuity.index", "rolling_window", "90d"),
        MemoryRetentionRecord("memory.incident.ledger", "historical_retention", "365d"),
        MemoryRetentionRecord("memory.scorecard.backlog", "archive_only", "730d"),
        MemoryRetentionRecord("memory.operator.notes", "stale_cleanup", "30d"),
    ]
    return sorted(rows, key=lambda x: x.memory_id)
