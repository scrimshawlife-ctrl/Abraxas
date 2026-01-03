"""Execute bulk pull plans (cache-first, bulk-only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from abraxas.acquisition.perf_ledger import PerfLedger
from abraxas.acquisition.plan_schema import BulkPullPlan, PlanStep
from abraxas.acquisition.transport import acquire_bulk, acquire_cache_only
from abraxas.policy.utp import PortfolioTuningIR
from abraxas.runtime.concurrency import ConcurrencyConfig
from abraxas.runtime.deterministic_executor import commit_results, execute_parallel, WorkResult
from abraxas.runtime.work_units import WorkUnit
from abraxas.sources.packets import SourcePacket
from abraxas.storage.cas import CASStore


@dataclass(frozen=True)
class ExecutionResult:
    packets: List[SourcePacket]
    cache_refs: List[Dict[str, Any]]


def execute_plan(
    *,
    plan: BulkPullPlan,
    run_ctx: Dict[str, Any],
    budgets: PortfolioTuningIR,
    cas_store: CASStore | None = None,
    perf_ledger: PerfLedger | None = None,
    offline: bool = False,
) -> ExecutionResult:
    cas_store = cas_store or CASStore()
    perf_ledger = perf_ledger or PerfLedger()
    now_utc = run_ctx.get("now_utc") or "1970-01-01T00:00:00Z"

    config = ConcurrencyConfig.from_portfolio(budgets)
    work_units = _build_work_units(plan)
    results = execute_parallel(
        work_units,
        config=config,
        stage="FETCH",
        handler=lambda unit: _execute_unit(unit, plan, run_ctx, budgets, cas_store, offline),
    )
    committed = commit_results(results.results)

    packets: List[SourcePacket] = []
    cache_refs: List[Dict[str, Any]] = []
    for result in committed:
        output = result.output_refs
        if output.get("skipped"):
            continue
        cache_refs.append(output["cache_ref"])
        packet = SourcePacket(
            source_id=plan.source_id,
            observed_at_utc=now_utc,
            window_start_utc=plan.window_utc.get("start"),
            window_end_utc=plan.window_utc.get("end"),
            payload={
                "url": output["url"],
                "cache_ref": output["cache_ref"],
                "content_type": output.get("content_type"),
            },
            provenance={
                "plan_id": plan.plan_id,
                "step_id": output.get("step_id"),
                "acquisition_method": output.get("method"),
            },
        )
        packets.append(packet)
        perf_ledger.record(
            {
                "ts": now_utc,
                "event": "plan_step",
                "source_id": plan.source_id,
                "plan_id": plan.plan_id,
                "step_id": output.get("step_id"),
                "url": output.get("url"),
                "bytes": output["cache_ref"].get("bytes"),
                "method": output.get("method"),
            }
        )

    perf_ledger.record(
        {
            "ts": now_utc,
            "event": "parallel_stage",
            "stage": "FETCH",
            "workers_used": results.workers_used,
            "max_inflight_bytes": results.max_inflight_bytes,
            "wall_ms": results.wall_ms,
        }
    )

    return ExecutionResult(packets=packets, cache_refs=cache_refs)


def _execute_unit(
    unit: WorkUnit,
    plan: BulkPullPlan,
    run_ctx: Dict[str, Any],
    budgets: PortfolioTuningIR,
    cas_store: CASStore,
    offline: bool,
) -> WorkResult:
    step_id = unit.input_refs.get("step_id")
    url = unit.input_refs.get("url")
    if offline:
        cached = acquire_cache_only(url=url, cas_store=cas_store)
        if cached is None:
            return WorkResult(
                unit_id=unit.unit_id,
                key=unit.key,
                output_refs={"skipped": True, "step_id": step_id, "url": url},
                bytes_processed=0,
                stage=unit.stage,
            )
        return WorkResult(
            unit_id=unit.unit_id,
            key=unit.key,
            output_refs={
                "cache_ref": cached.raw_ref.to_dict(),
                "method": "cache_only",
                "content_type": cached.content_type,
                "step_id": step_id,
                "url": url,
            },
            bytes_processed=cached.raw_ref.bytes,
            stage=unit.stage,
        )

    result = acquire_bulk(
        url=url,
        source_id=plan.source_id,
        run_id=run_ctx.get("run_id", "bulk"),
        cas_store=cas_store,
        recorded_at_utc=run_ctx.get("now_utc"),
        budget={
            "max_requests": budgets.ubv.max_requests_per_run,
            "max_bytes": budgets.ubv.max_bytes_per_run,
            "timeout_s": 60,
        },
    )
    return WorkResult(
        unit_id=unit.unit_id,
        key=unit.key,
        output_refs={
            "cache_ref": result.raw_ref.to_dict(),
            "method": "bulk",
            "content_type": result.content_type,
            "step_id": step_id,
            "url": url,
        },
        bytes_processed=result.raw_ref.bytes,
        stage=unit.stage,
    )


def _build_work_units(plan: BulkPullPlan) -> List[WorkUnit]:
    units: List[WorkUnit] = []
    for step in plan.steps:
        if step.action == "SKIP":
            continue
        key = (plan.source_id, plan.window_utc.get("start"), step.url_or_key)
        unit = WorkUnit.build(
            stage="FETCH",
            source_id=plan.source_id,
            window_utc=plan.window_utc,
            key=key,
            input_refs={"step_id": step.step_id, "url": step.url_or_key},
            input_bytes=step.expected_bytes or 0,
        )
        units.append(unit)
    return sorted(units, key=lambda unit: unit.key)
