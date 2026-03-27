from __future__ import annotations

from abx.knowledge.types import MemoryLifecycleRecord


def build_memory_lifecycle() -> list[MemoryLifecycleRecord]:
    rows = [
        MemoryLifecycleRecord("memory.baseline.current", "ACTIVE", "runtime+governance"),
        MemoryLifecycleRecord("memory.continuity.index", "GOVERNED_DERIVED", "governance+operator"),
        MemoryLifecycleRecord("memory.incident.ledger", "HISTORICAL", "operator"),
        MemoryLifecycleRecord("memory.scorecard.backlog", "ARCHIVAL", "audit-only"),
        MemoryLifecycleRecord("memory.operator.notes", "STALE", "none"),
    ]
    return sorted(rows, key=lambda x: x.memory_id)
