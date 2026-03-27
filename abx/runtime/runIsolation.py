from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


@dataclass(frozen=True)
class RunContext:
    run_id: str
    scenario_id: str
    continuity_mode: str
    previous_run_id: str | None
    context_id: str


@dataclass(frozen=True)
class ConcurrencyBoundary:
    boundary_id: str
    run_id: str
    runtime_state_scope: str
    artifact_scope: str
    scheduler_scope: str


def build_run_context(*, run_id: str, scenario_id: str, previous_run_id: str | None = None, inherit_continuity: bool = False) -> RunContext:
    run_id_norm = str(run_id).strip()
    if not run_id_norm:
        raise ValueError("run_id_required")
    continuity_mode = "INHERIT" if inherit_continuity and previous_run_id else "ISOLATE"
    payload = {
        "run_id": run_id_norm,
        "scenario_id": scenario_id,
        "previous_run_id": previous_run_id,
        "continuity_mode": continuity_mode,
    }
    context_id = f"run-context-{sha256_bytes(dumps_stable(payload).encode('utf-8'))[:16]}"
    return RunContext(
        run_id=run_id_norm,
        scenario_id=str(scenario_id),
        continuity_mode=continuity_mode,
        previous_run_id=str(previous_run_id) if previous_run_id else None,
        context_id=context_id,
    )


def build_concurrency_boundary(ctx: RunContext) -> ConcurrencyBoundary:
    return ConcurrencyBoundary(
        boundary_id=f"boundary-{ctx.run_id}",
        run_id=ctx.run_id,
        runtime_state_scope=f"runtime/{ctx.run_id}",
        artifact_scope=f"artifacts/{ctx.run_id}",
        scheduler_scope=f"scheduler/{ctx.run_id}",
    )


def isolate_payload(payload: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
    base = dict(payload)
    base["run_id"] = ctx.run_id
    base["scenario_id"] = ctx.scenario_id
    base["continuity_mode"] = ctx.continuity_mode
    if ctx.previous_run_id:
        base["previous_run_id"] = ctx.previous_run_id
    return base
