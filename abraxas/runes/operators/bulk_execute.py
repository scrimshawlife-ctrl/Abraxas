"""ABX-BULK_EXECUTE rune operator."""

from __future__ import annotations

from typing import Any, Dict

from abraxas.acquisition.execute_plan import execute_plan
from abraxas.acquisition.plan_schema import BulkPullPlan
from abraxas.policy.utp import load_active_utp
from abraxas.storage.cas import CASStore


def apply_bulk_execute(
    *,
    bulk_plan: Dict[str, Any],
    offline: bool = False,
    run_ctx: Dict[str, Any],
    strict_execution: bool = True,
) -> Dict[str, Any]:
    budgets = load_active_utp()
    cas_store = CASStore()
    plan = BulkPullPlan(**bulk_plan)
    result = execute_plan(
        plan=plan,
        run_ctx=run_ctx,
        budgets=budgets,
        cas_store=cas_store,
        offline=offline,
    )
    return {
        "packet_refs": [packet.packet_hash() for packet in result.packets],
        "packets": [packet.model_dump() for packet in result.packets],
        "cache_refs": result.cache_refs,
    }
