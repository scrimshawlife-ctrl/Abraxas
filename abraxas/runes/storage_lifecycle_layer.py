"""Convenience wrappers for storage lifecycle runes."""

from __future__ import annotations

from typing import Any, Dict

from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.invoke import invoke_capability


def storage_summarize(*, index_path: str, now_utc: str, ctx: RuneInvocationContext | dict) -> Dict[str, Any]:
    return invoke_capability(
        "RUNE.STORAGE_SUMMARIZE",
        {"index_path": index_path, "now_utc": now_utc},
        ctx=ctx,
    )


def lifecycle_plan(
    *,
    index_path: str,
    now_utc: str,
    allow_raw_delete: bool,
    ctx: RuneInvocationContext | dict,
) -> Dict[str, Any]:
    return invoke_capability(
        "RUNE.LIFECYCLE_PLAN",
        {"index_path": index_path, "now_utc": now_utc, "allow_raw_delete": allow_raw_delete},
        ctx=ctx,
    )


def lifecycle_execute(
    *,
    plan: Dict[str, Any],
    allow_raw_delete: bool,
    ctx: RuneInvocationContext | dict,
) -> Dict[str, Any]:
    return invoke_capability(
        "RUNE.LIFECYCLE_EXECUTE",
        {"plan": plan, "allow_raw_delete": allow_raw_delete},
        ctx=ctx,
    )


def lifecycle_revert(*, pointer_path: str, ctx: RuneInvocationContext | dict) -> Dict[str, Any]:
    return invoke_capability(
        "RUNE.LIFECYCLE_REVERT",
        {"pointer_path": pointer_path},
        ctx=ctx,
    )
