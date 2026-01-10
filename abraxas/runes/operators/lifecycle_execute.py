"""ABX-LIFECYCLE_EXECUTE rune operator."""

from __future__ import annotations

from typing import Any, Dict

from abraxas.storage.compaction import CompactionPlan, CompactionStep
from abraxas.storage.eviction import EvictionPlan, EvictionStep
from abraxas.storage.lifecycle_ir import load_lifecycle_ir
from abraxas.storage.lifecycle_run import execute_lifecycle, LifecyclePlan
from abraxas.runes.operators.raw_no_delete import apply_raw_no_delete


def apply_lifecycle_execute(
    *,
    plan: Dict[str, Any],
    allow_raw_delete: bool = False,
    strict_execution: bool = True,
) -> Dict[str, Any]:
    lifecycle_ir = load_lifecycle_ir(plan.get("now_utc", "1970-01-01T00:00:00Z"))
    compaction_steps = [CompactionStep(**step) for step in (plan.get("compaction") or [])]
    eviction_steps = [EvictionStep(**step) for step in (plan.get("eviction") or [])]
    apply_raw_no_delete(
        steps=[step.__dict__ for step in eviction_steps],
        allow_raw_delete=allow_raw_delete,
    )
    lifecycle_plan = LifecyclePlan(
        compaction=CompactionPlan(steps=compaction_steps),
        eviction=EvictionPlan(steps=eviction_steps),
    )
    result = execute_lifecycle(
        lifecycle_plan,
        lifecycle_ir,
        allow_raw_delete=allow_raw_delete,
        max_files=plan.get("max_files"),
        max_cpu_ms=plan.get("max_cpu_ms"),
        max_bytes_written=plan.get("max_bytes_written"),
    )
    return {
        "result": {
            "bytes_freed": result.bytes_freed,
            "bytes_saved": result.bytes_saved,
            "bytes_written": result.bytes_written,
            "cpu_ms": result.cpu_ms,
            "compaction_events": result.compaction_events,
            "eviction_events": result.eviction_events,
        }
    }
