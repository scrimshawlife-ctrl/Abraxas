"""ABX-BULK_PLAN rune operator."""

from __future__ import annotations

from typing import Any, Dict

from abraxas.acquisition.bulk_planner import build_bulk_plan
from abraxas.acquisition.manifest_schema import ManifestArtifact
from abraxas.policy.utp import load_active_utp


def apply_bulk_plan(
    *,
    manifest_artifact: Dict[str, Any],
    window: Dict[str, Any] | None = None,
    run_ctx: Dict[str, Any],
    strict_execution: bool = True,
) -> Dict[str, Any]:
    budgets = load_active_utp()
    manifest = ManifestArtifact(**manifest_artifact)
    plan_result = build_bulk_plan(
        source_id=manifest.source_id,
        window_utc=window or {},
        manifest=manifest,
        budgets=budgets,
        created_at_utc=run_ctx.get("now_utc", "1970-01-01T00:00:00Z"),
    )
    return {
        "bulk_plan": plan_result.plan.model_dump(),
        "overflow_urls": plan_result.overflow_urls,
    }
