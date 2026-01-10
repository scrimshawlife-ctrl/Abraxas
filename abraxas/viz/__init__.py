"""
Abraxas Viz Adapter — Pure Transformers (No Rendering)

Converts Abraxas runtime artifacts to visualization-friendly formats.
This module is Abraxas-owned, not external viz code.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from abraxas.ers.types import TraceEvent


def ers_trace_to_trendpack(
    *,
    trace: List[TraceEvent],
    run_id: str,
    tick: int,
    provenance: Optional[Dict[str, Any]] = None,
    result_ref_by_task: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Convert ERS trace to TrendPack format for visualization ingestion.

    TrendPack is a queryable, denormalized format optimized for:
    - Lane timelines (forecast vs shadow)
    - Budget heat maps (skipped_budget events)
    - Error cluster detection
    - Task cost burn-down per tick

    This is a pure data transformation with no rendering logic.

    Args:
        trace: List of TraceEvent from ERS scheduler
        run_id: Run identifier
        tick: Tick number
        provenance: Optional provenance metadata
        result_ref_by_task: Optional mapping of task name to ResultRef.v0 dict.
            If provided, each event's meta will include result_ref pointing to
            the ResultsPack location for that task's full output.
    """
    result_ref_by_task = result_ref_by_task or {}

    # Timeline: ordered events with full context
    timeline = []
    for event in trace:
        # Build meta with optional result_ref injection
        meta = dict(event.meta) if event.meta else {}
        result_ref = result_ref_by_task.get(event.task)
        if result_ref is not None:
            meta["result_ref"] = result_ref

        timeline.append({
            "task": event.task,
            "lane": event.lane,
            "status": event.status,
            "cost_ops": event.cost_ops,
            "cost_entropy": event.cost_entropy,
            "meta": meta,
        })

    # Budget analysis: aggregate costs by lane
    forecast_spent_ops = sum(e.cost_ops for e in trace if e.lane == "forecast" and e.status != "skipped_budget")
    forecast_spent_entropy = sum(e.cost_entropy for e in trace if e.lane == "forecast" and e.status != "skipped_budget")
    shadow_spent_ops = sum(e.cost_ops for e in trace if e.lane == "shadow" and e.status != "skipped_budget")
    shadow_spent_entropy = sum(e.cost_entropy for e in trace if e.lane == "shadow" and e.status != "skipped_budget")

    budget = {
        "forecast": {
            "spent_ops": forecast_spent_ops,
            "spent_entropy": forecast_spent_entropy,
        },
        "shadow": {
            "spent_ops": shadow_spent_ops,
            "spent_entropy": shadow_spent_entropy,
        },
    }

    # Error extraction: isolate error events with context
    errors = []
    for event in trace:
        if event.status == "error":
            errors.append({
                "task": event.task,
                "lane": event.lane,
                "cost_ops": event.cost_ops,
                "meta": event.meta,
            })

    # Skipped events: budget exhaustion tracking
    skipped = []
    for event in trace:
        if event.status == "skipped_budget":
            skipped.append({
                "task": event.task,
                "lane": event.lane,
                "cost_ops": event.cost_ops,
                "cost_entropy": event.cost_entropy,
            })

    # Stats: quick summary metrics
    stats = {
        "total_events": len(trace),
        "forecast_events": sum(1 for e in trace if e.lane == "forecast"),
        "shadow_events": sum(1 for e in trace if e.lane == "shadow"),
        "errors": len(errors),
        "skipped": len(skipped),
        "ok_events": sum(1 for e in trace if e.status == "ok"),
    }

    return {
        "version": "0.1",
        "run_id": run_id,
        "tick": tick,
        "provenance": provenance or {},
        "timeline": timeline,
        "budget": budget,
        "errors": errors,
        "skipped": skipped,
        "stats": stats,
    }


__all__ = ["ers_trace_to_trendpack"]
