"""ABX-PARALLEL_STAGE_RUN rune operator."""

from __future__ import annotations

from typing import Any, Dict, List

from abraxas.runtime.concurrency import ConcurrencyConfig
from abraxas.runtime.deterministic_executor import execute_parallel, WorkResult
from abraxas.runtime.work_units import WorkUnit
from abraxas.runtime.perf_ledger import RuntimePerfLedger


def apply_parallel_stage_run(
    *,
    work_units: List[Dict[str, Any]],
    config: Dict[str, Any],
    stage: str,
    strict_execution: bool = True,
) -> Dict[str, Any]:
    concurrency = ConcurrencyConfig(**config)
    units = [_work_unit_from_dict(unit) for unit in work_units]

    results = execute_parallel(
        units,
        config=concurrency,
        stage=stage,
        handler=lambda unit: WorkResult(
            unit_id=unit.unit_id,
            key=unit.key,
            output_refs=unit.output_refs or {},
            bytes_processed=unit.input_bytes,
            stage=unit.stage,
        ),
    )
    ledger = RuntimePerfLedger()
    ledger.record(
        {
            "event": "parallel_stage_run",
            "stage": stage,
            "workers_used": results.workers_used,
            "max_inflight_bytes": results.max_inflight_bytes,
            "wall_ms": results.wall_ms,
        }
    )
    return {
        "results": [
            {
                "unit_id": result.unit_id,
                "key": result.key,
                "output_refs": result.output_refs,
                "stage": result.stage,
            }
            for result in results.results
        ]
    }


def _work_unit_from_dict(payload: Dict[str, Any]) -> WorkUnit:
    return WorkUnit(
        unit_id=payload["unit_id"],
        stage=payload["stage"],
        source_id=payload["source_id"],
        window_utc=payload.get("window_utc") or {},
        key=tuple(payload.get("key") or ()),
        input_refs=payload.get("input_refs") or {},
        output_refs=payload.get("output_refs"),
        input_bytes=int(payload.get("input_bytes") or 0),
    )
