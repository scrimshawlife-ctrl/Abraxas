"""Convenience wrappers for profile runes."""

from __future__ import annotations

from typing import Any, Dict

from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.invoke import invoke_capability


def profile_run(*, config: Dict[str, Any], run_ctx: Dict[str, Any], ctx: RuneInvocationContext | dict) -> Dict[str, Any]:
    return invoke_capability("rune:profile_run", {"config": config, "run_ctx": run_ctx}, ctx=ctx)


def profile_export(*, profile_pack: Dict[str, Any], out_path: str, ctx: RuneInvocationContext | dict) -> Dict[str, Any]:
    return invoke_capability(
        "rune:profile_export",
        {"profile_pack": profile_pack, "out_path": out_path},
        ctx=ctx,
    )


def profile_ingest(*, profile_pack: Dict[str, Any], ctx: RuneInvocationContext | dict) -> Dict[str, Any]:
    return invoke_capability("rune:profile_ingest", {"profile_pack": profile_pack}, ctx=ctx)
