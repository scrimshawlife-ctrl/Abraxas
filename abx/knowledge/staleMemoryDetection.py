from __future__ import annotations

from abx.knowledge.memoryLifecycle import build_memory_lifecycle


def detect_stale_memory() -> list[str]:
    return sorted([row.memory_id for row in build_memory_lifecycle() if row.lifecycle_state in {"STALE", "EXPIRED"}])
