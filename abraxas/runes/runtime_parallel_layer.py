"""Convenience wrappers for runtime parallelism runes."""

from __future__ import annotations

from typing import Any, Dict, List

from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.invoke import invoke_capability


def parallel_stage_run(
    *,
    work_units: List[Dict[str, Any]],
    config: Dict[str, Any],
    stage: str,
    ctx: RuneInvocationContext | dict,
) -> Dict[str, Any]:
    return invoke_capability(
        "rune:parallel_stage_run",
        {"work_units": work_units, "config": config, "stage": stage},
        ctx=ctx,
    )


def serial_commit(
    *,
    results: List[Dict[str, Any]],
    ctx: RuneInvocationContext | dict,
) -> Dict[str, Any]:
    return invoke_capability(
        "rune:serial_commit",
        {"results": results},
        ctx=ctx,
    )


def deterministic_commit_order(
    *,
    results: List[Dict[str, Any]],
    ctx: RuneInvocationContext | dict,
) -> Dict[str, Any]:
    return invoke_capability(
        "rune:deterministic_commit_order",
        {"results": results},
        ctx=ctx,
    )


def no_time_branching(
    *,
    payload: Dict[str, Any],
    ctx: RuneInvocationContext | dict,
) -> Dict[str, Any]:
    return invoke_capability(
        "rune:no_time_branching",
        {"payload": payload},
        ctx=ctx,
    )
