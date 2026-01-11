"""ABX-LIFECYCLE_PLAN rune operator."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from abraxas.storage.index import StorageIndex
from abraxas.storage.lifecycle_ir import load_lifecycle_ir
from abraxas.storage.lifecycle_run import plan_lifecycle


def apply_lifecycle_plan(
    *,
    index_path: str,
    now_utc: str,
    allow_raw_delete: bool = False,
    strict_execution: bool = True,
) -> Dict[str, Any]:
    index = StorageIndex.from_jsonl(Path(index_path))
    lifecycle_ir = load_lifecycle_ir(now_utc)
    plan = plan_lifecycle(index, now_utc, lifecycle_ir, allow_raw_delete=allow_raw_delete)
    return {
        "plan": {
            "compaction": [step.__dict__ for step in plan.compaction.steps],
            "eviction": [step.__dict__ for step in plan.eviction.steps],
            "now_utc": now_utc,
        },
        "ir_hash": lifecycle_ir.ir_hash(),
    }
