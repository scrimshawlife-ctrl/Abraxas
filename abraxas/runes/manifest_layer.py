"""Convenience wrappers for manifest-first acquisition runes."""

from __future__ import annotations

from typing import Any, Dict, List

from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.invoke import invoke_capability


def manifest_discover(
    source_id: str,
    *,
    seeds: List[str] | None,
    window: Dict[str, Any] | None,
    run_ctx: Dict[str, Any],
    ctx: RuneInvocationContext | dict,
) -> Dict[str, Any]:
    return invoke_capability(
        "RUNE.MANIFEST_DISCOVER",
        {
            "source_id": source_id,
            "seeds": seeds or [],
            "window": window or {},
            "run_ctx": run_ctx,
        },
        ctx=ctx,
    )


def bulk_plan(
    *,
    manifest_artifact: Dict[str, Any],
    window: Dict[str, Any] | None,
    run_ctx: Dict[str, Any],
    ctx: RuneInvocationContext | dict,
) -> Dict[str, Any]:
    return invoke_capability(
        "RUNE.BULK_PLAN",
        {
            "manifest_artifact": manifest_artifact,
            "window": window or {},
            "run_ctx": run_ctx,
        },
        ctx=ctx,
    )


def bulk_execute(
    *,
    bulk_plan: Dict[str, Any],
    offline: bool,
    run_ctx: Dict[str, Any],
    ctx: RuneInvocationContext | dict,
) -> Dict[str, Any]:
    return invoke_capability(
        "RUNE.BULK_EXECUTE",
        {
            "bulk_plan": bulk_plan,
            "offline": offline,
            "run_ctx": run_ctx,
        },
        ctx=ctx,
    )


def manifest_only_enforce(
    *,
    stage: str,
    decodo_used: bool,
    ctx: RuneInvocationContext | dict,
) -> Dict[str, Any]:
    return invoke_capability(
        "RUNE.MANIFEST_ONLY_ENFORCE",
        {"stage": stage, "decodo_used": decodo_used},
        ctx=ctx,
    )


def plan_finite_enforce(
    *,
    steps: List[Dict[str, Any]],
    ctx: RuneInvocationContext | dict,
) -> Dict[str, Any]:
    return invoke_capability(
        "RUNE.PLAN_FINITE_ENFORCE",
        {"steps": steps},
        ctx=ctx,
    )
