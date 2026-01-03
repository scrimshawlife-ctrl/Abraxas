"""CLI for storage lifecycle management."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from abraxas.core.canonical import canonical_json
from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.storage_lifecycle_layer import (
    lifecycle_execute,
    lifecycle_plan,
    lifecycle_revert,
    storage_summarize,
)


@dataclass(frozen=True)
class StorageRunContext:
    run_id: str
    now_utc: str
    git_hash: str = "unknown"
    subsystem_id: str = "storage"

    def rune_ctx(self) -> RuneInvocationContext:
        return RuneInvocationContext(run_id=self.run_id, subsystem_id=self.subsystem_id, git_hash=self.git_hash)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_storage_summarize(index_path: str, now: Optional[str]) -> int:
    run_ctx = StorageRunContext(run_id="storage_summarize", now_utc=now or _utc_now())
    outputs = storage_summarize(index_path=index_path, now_utc=run_ctx.now_utc, ctx=run_ctx.rune_ctx())
    print(canonical_json(outputs))
    return 0


def run_storage_plan(index_path: str, out_path: str, now: Optional[str], allow_raw_delete: bool) -> int:
    run_ctx = StorageRunContext(run_id="storage_plan", now_utc=now or _utc_now())
    outputs = lifecycle_plan(
        index_path=index_path,
        now_utc=run_ctx.now_utc,
        allow_raw_delete=allow_raw_delete,
        ctx=run_ctx.rune_ctx(),
    )
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(canonical_json(outputs), encoding="utf-8")
    return 0


def run_storage_execute(plan_path: str, allow_raw_delete: bool) -> int:
    run_ctx = StorageRunContext(run_id="storage_execute", now_utc=_utc_now())
    plan_payload = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    outputs = lifecycle_execute(plan=plan_payload.get("plan", plan_payload), allow_raw_delete=allow_raw_delete, ctx=run_ctx.rune_ctx())
    print(canonical_json(outputs))
    return 0


def run_storage_compact(plan_path: str, max_files: int, max_cpu_ms: int) -> int:
    plan_payload = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    plan = plan_payload.get("plan", plan_payload)
    plan["compaction"] = (plan.get("compaction") or [])[: max(0, int(max_files))]
    plan["eviction"] = []
    plan["max_files"] = int(max_files)
    plan["max_cpu_ms"] = int(max_cpu_ms)
    outputs = lifecycle_execute(plan=plan, allow_raw_delete=False, ctx=RuneInvocationContext(run_id="storage_compact", subsystem_id="storage", git_hash="unknown"))
    print(canonical_json(outputs))
    return 0


def run_storage_revert(pointer_path: str) -> int:
    run_ctx = StorageRunContext(run_id="storage_revert", now_utc=_utc_now())
    outputs = lifecycle_revert(pointer_path=pointer_path, ctx=run_ctx.rune_ctx())
    print(canonical_json(outputs))
    return 0
