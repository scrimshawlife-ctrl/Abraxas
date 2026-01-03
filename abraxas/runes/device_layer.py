"""Convenience wrappers for device selection runes."""

from __future__ import annotations

from typing import Any, Dict

from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.invoke import invoke_capability


def device_fingerprint(*, run_ctx: Dict[str, Any], ctx: RuneInvocationContext | dict) -> Dict[str, Any]:
    return invoke_capability("rune:device_fingerprint", {"run_ctx": run_ctx}, ctx=ctx)


def device_profile_resolve(
    *,
    fingerprint: Dict[str, Any],
    ctx: RuneInvocationContext | dict,
) -> Dict[str, Any]:
    return invoke_capability(
        "rune:device_profile_resolve",
        {"fingerprint": fingerprint},
        ctx=ctx,
    )


def portfolio_select(
    *,
    run_ctx: Dict[str, Any],
    dry_run: bool,
    ctx: RuneInvocationContext | dict,
) -> Dict[str, Any]:
    return invoke_capability(
        "rune:portfolio_select",
        {"run_ctx": run_ctx, "dry_run": dry_run},
        ctx=ctx,
    )
