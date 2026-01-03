"""Lifecycle runner for storage summarize/plan/execute."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

from abraxas.storage.compaction import CompactionPlan, execute_compaction, plan_compaction
from abraxas.storage.eviction import EvictionPlan, plan_eviction
from abraxas.storage.index import StorageIndex, StorageIndexEntry
from abraxas.storage.lifecycle_schema import LifecycleIR
from abraxas.storage.perf_ledger import StoragePerfLedger
from abraxas.storage.tiering import assign_tier


@dataclass(frozen=True)
class LifecyclePlan:
    compaction: CompactionPlan
    eviction: EvictionPlan


@dataclass(frozen=True)
class LifecycleExecutionResult:
    compaction_events: List[Dict[str, Any]]
    eviction_events: List[Dict[str, Any]]
    bytes_freed: int
    bytes_saved: int
    bytes_written: int
    cpu_ms: int


def summarize_storage(index: StorageIndex, now_utc: str, lifecycle_ir: LifecycleIR) -> Dict[str, Any]:
    totals: Dict[str, int] = {}
    tiers: Dict[str, int] = {}
    entries = _with_assigned_tiers(index, lifecycle_ir, now_utc)
    for entry in entries:
        totals[entry.artifact_type] = totals.get(entry.artifact_type, 0) + entry.size_bytes
        tiers[entry.tier] = tiers.get(entry.tier, 0) + entry.size_bytes
    return {
        "total_bytes_by_type": totals,
        "total_bytes_by_tier": tiers,
        "entry_count": len(entries),
    }


def plan_lifecycle(
    index: StorageIndex,
    now_utc: str,
    lifecycle_ir: LifecycleIR,
    *,
    allow_raw_delete: bool = False,
) -> LifecyclePlan:
    assigned_index = StorageIndex(_with_assigned_tiers(index, lifecycle_ir, now_utc))
    compaction_plan = plan_compaction(assigned_index, lifecycle_ir, now_utc)
    eviction_plan = plan_eviction(assigned_index, lifecycle_ir, now_utc, allow_raw_delete=allow_raw_delete)
    return LifecyclePlan(compaction=compaction_plan, eviction=eviction_plan)


def execute_lifecycle(
    plan: LifecyclePlan,
    lifecycle_ir: LifecycleIR,
    *,
    perf_ledger: StoragePerfLedger | None = None,
    max_files: int | None = None,
    max_cpu_ms: int | None = None,
    max_bytes_written: int | None = None,
    allow_raw_delete: bool = False,
) -> LifecycleExecutionResult:
    perf_ledger = perf_ledger or StoragePerfLedger()
    max_files = max_files if max_files is not None else lifecycle_ir.compaction.max_files_per_run
    max_cpu_ms = max_cpu_ms if max_cpu_ms is not None else lifecycle_ir.compaction.max_cpu_ms_per_run
    max_bytes_written = (
        max_bytes_written if max_bytes_written is not None else lifecycle_ir.compaction.max_bytes_written_per_run
    )

    start = time.monotonic()
    compaction_index, compaction_events = execute_compaction(
        plan.compaction,
        lifecycle_ir,
        max_files=max_files,
        max_cpu_ms=max_cpu_ms,
        max_bytes_written=max_bytes_written,
    )

    bytes_written = sum(event.get("bytes_after", 0) for event in compaction_events)
    bytes_saved = sum(
        max(0, event.get("bytes_before", 0) - event.get("bytes_after", 0)) for event in compaction_events
    )
    eviction_events = _execute_eviction(plan.eviction, allow_raw_delete=allow_raw_delete)
    bytes_freed = sum(event.get("bytes_freed", 0) for event in eviction_events) + bytes_saved
    cpu_ms = int((time.monotonic() - start) * 1000)

    rent_ratio = (bytes_freed / cpu_ms) if cpu_ms > 0 else 0.0
    perf_ledger.record(
        {
            "event": "lifecycle_execute",
            "bytes_written": bytes_written,
            "bytes_freed": bytes_freed,
            "bytes_saved": bytes_saved,
            "cpu_ms": cpu_ms,
            "rent_ratio": round(rent_ratio, 6),
        }
    )

    return LifecycleExecutionResult(
        compaction_events=compaction_events,
        eviction_events=eviction_events,
        bytes_freed=bytes_freed,
        bytes_saved=bytes_saved,
        bytes_written=bytes_written,
        cpu_ms=cpu_ms,
    )


def _execute_eviction(eviction_plan: EvictionPlan, *, allow_raw_delete: bool) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for step in eviction_plan.steps:
        if step.action != "DELETE":
            continue
        path = Path(step.path)
        if not path.exists():
            continue
        bytes_before = path.stat().st_size
        path.unlink()
        events.append(
            {
                "event": "evict",
                "path": step.path,
                "bytes_freed": bytes_before,
                "reason": step.reason,
            }
        )
    return events


def _with_assigned_tiers(index: StorageIndex, lifecycle_ir: LifecycleIR, now_utc: str) -> List[StorageIndexEntry]:
    entries: List[StorageIndexEntry] = []
    for entry in index.entries:
        tier = assign_tier(entry, lifecycle_ir, now_utc)
        if tier == entry.tier:
            entries.append(entry)
        else:
            entries.append(
                StorageIndexEntry(
                    artifact_type=entry.artifact_type,
                    source_id=entry.source_id,
                    created_at_utc=entry.created_at_utc,
                    size_bytes=entry.size_bytes,
                    codec=entry.codec,
                    tier=tier,
                    path=entry.path,
                    content_hash=entry.content_hash,
                    last_accessed_at_utc=entry.last_accessed_at_utc,
                    superseded_by=entry.superseded_by,
                )
            )
    return entries
