"""Convenience wrappers for source-layer ABX-Runes."""

from __future__ import annotations

from typing import Any, Dict, List

from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.invoke import invoke_capability


def source_resolve(source_ids: List[str], *, ctx: RuneInvocationContext | dict) -> Dict[str, Any]:
    return invoke_capability("rune:source_resolve", {"source_ids": source_ids}, ctx=ctx)


def temporal_normalize(
    *,
    timestamp: str,
    timezone: str,
    window: Dict[str, str] | None,
    calendars: List[str] | None,
    ctx: RuneInvocationContext | dict,
) -> Dict[str, Any]:
    return invoke_capability(
        "rune:temporal_normalize",
        {
            "timestamp": timestamp,
            "timezone": timezone,
            "window": window or {},
            "calendars": calendars or [],
        },
        ctx=ctx,
    )


def source_redundancy_check(sources: List[Dict[str, Any]], *, ctx: RuneInvocationContext | dict) -> Dict[str, Any]:
    return invoke_capability("rune:source_redundancy_check", {"sources": sources}, ctx=ctx)


def source_discover(
    *,
    residuals: List[Dict[str, Any]] | None,
    anomalies: List[Dict[str, Any]] | None,
    convergence: List[Dict[str, Any]] | None,
    silence: List[Dict[str, Any]] | None,
    ctx: RuneInvocationContext | dict,
) -> Dict[str, Any]:
    return invoke_capability(
        "rune:source_discover",
        {
            "residuals": residuals or [],
            "anomalies": anomalies or [],
            "convergence": convergence or [],
            "silence": silence or [],
        },
        ctx=ctx,
    )


def provenance_seal(payload: Dict[str, Any], *, ctx: RuneInvocationContext | dict) -> Dict[str, Any]:
    return invoke_capability("rune:provenance_seal", {"payload": payload}, ctx=ctx)
