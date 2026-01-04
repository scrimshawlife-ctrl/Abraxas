"""
ViewPack — One-file "overview" artifact for UIs.

This is the "UI doesn't have to chase refs" layer.
Abraxas emits a compact view artifact per tick that contains:
- TrendPack aggregates (counts/costs)
- The event list (same as TrendPack timeline)
- Optionally a capped set of resolved results (first N events, or only errors/skips)

It's not a replacement for ResultPack—just an ergonomic overlay.

A UI can load one file:
    view/<run_id>/<tick>.viewpack.json

...and show:
- Timeline summary
- Counts & costs
- The list of events
- Only the important resolved results (errors/budget skips)

Without chasing ResultPack unless the user expands.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from abraxas.runtime.viz_resolve import load_trendpack, resolve_trendpack_events


def _strip_result_refs_paths(resolved: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Strip absolute paths from resolved entries to ensure determinism.

    The result refs contain absolute paths which vary between runs.
    We strip these since:
    1. ViewPack already embeds the resolved result (no need to chase refs)
    2. If needed, paths can be reconstructed from run_id/tick pattern
    """
    stripped = []
    for r in resolved:
        entry = dict(r)
        # Keep event and result, but clear path-dependent ref info
        if entry.get("ref"):
            ref = dict(entry["ref"])
            # Keep schema and task, strip the absolute path
            ref.pop("results_pack", None)
            entry["ref"] = ref if ref else None
        stripped.append(entry)
    return stripped


def build_view_pack(
    *,
    trendpack_path: str,
    run_id: str,
    tick: int,
    mode: str,
    # Cap resolved payload size
    resolve_limit: int = 50,
    # If provided, include resolved results only for events with status in this set
    # None means resolve all (up to limit)
    resolve_only_status: Optional[List[str]] = None,
    # Invariance summary for UI badge (trendpack_sha256, runheader_sha256, passed)
    invariance: Optional[Dict[str, Any]] = None,
    # Stability summary for run-level PASS/FAIL badge (if stability record exists)
    stability_summary: Optional[Dict[str, Any]] = None,
    provenance: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a ViewPack.v0 artifact.

    A single-file overview for UIs:
    - Includes TrendPack aggregates + events
    - Includes a capped resolved event+result list (optional filtering)

    Args:
        trendpack_path: Path to TrendPack JSON file
        run_id: Run identifier
        tick: Tick number
        mode: Execution mode
        resolve_limit: Maximum number of events to resolve (default 50)
        resolve_only_status: If provided, only resolve events with these statuses
            (e.g., ["error", "skipped_budget"] for compact high-signal output)
        invariance: Optional invariance summary for UI badge display.
            Expected shape: {"schema": "InvarianceSummary.v0",
                           "trendpack_sha256": str, "runheader_sha256": str, "passed": bool}
        stability_summary: Optional stability summary for run-level PASS/FAIL badge.
            Expected shape: {"schema": "StabilitySummary.v0",
                           "ok": bool, "first_mismatch_run": int|None, "divergence_kind": str|None}
        provenance: Optional provenance metadata

    Returns:
        ViewPack.v0 dict
    """
    provenance = provenance or {}
    provenance = {k: provenance[k] for k in sorted(provenance.keys())}

    tp = load_trendpack(trendpack_path)

    # TrendPack uses "timeline" for events
    events = tp.get("timeline", []) or []

    # Strip result_ref from events to avoid path-dependent content
    # (ViewPack is self-contained; refs are not needed)
    events_clean = []
    for ev in events:
        ev_copy = dict(ev)
        if ev_copy.get("meta"):
            meta = dict(ev_copy["meta"])
            meta.pop("result_ref", None)
            ev_copy["meta"] = meta
        events_clean.append(ev_copy)

    # Resolve events (with limit)
    resolved = resolve_trendpack_events(trendpack_path, limit=resolve_limit)

    # Filter by status if requested
    if resolve_only_status is not None:
        allow = set(resolve_only_status)
        resolved = [
            r for r in resolved
            if (r.get("event") or {}).get("status") in allow
        ]

    # Strip absolute paths from resolved entries for determinism
    resolved_clean = _strip_result_refs_paths(resolved)

    # Build aggregates from TrendPack stats/budget
    aggregates = {
        "stats": tp.get("stats", {}),
        "budget": tp.get("budget", {}),
        "error_count": len(tp.get("errors", [])),
        "skipped_count": len(tp.get("skipped", [])),
    }

    # Embed invariance summary if provided (for UI stable/unstable badge)
    if invariance is not None:
        aggregates["invariance"] = invariance

    # Embed stability summary if provided (for run-level PASS/FAIL badge)
    if stability_summary is not None:
        aggregates["stability_summary"] = stability_summary

    # Store relative ref pattern instead of absolute path
    # Consumer can reconstruct: {artifacts_dir}/viz/{run_id}/{tick:06d}.trendpack.json
    trendpack_ref = {
        "pattern": "viz/{run_id}/{tick:06d}.trendpack.json",
        "run_id": run_id,
        "tick": tick,
    }

    return {
        "schema": "ViewPack.v0",
        "run_id": run_id,
        "tick": int(tick),
        "mode": mode,
        "trendpack_ref": trendpack_ref,
        "aggregates": aggregates,
        "events": events_clean,
        "resolved": resolved_clean,
        "resolved_filter": {
            "limit": resolve_limit,
            "status_filter": resolve_only_status,
            "actual_count": len(resolved_clean),
        },
        "provenance": provenance,
    }


__all__ = ["build_view_pack"]
