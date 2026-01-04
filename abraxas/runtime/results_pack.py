"""
ResultsPack — Per-tick task results artifact.

Contains all TaskResult objects for a tick in a deterministic format.
TrendPack events point here via result_ref instead of embedding bulky payloads.

Architecture:
- TrendPack: lightweight execution timeline (what ran, costs, status)
- ResultsPack: full task outputs (actual return values)
- RunIndex: stable pointers + hashes for both

AAL-Viz can:
- Render timelines from TrendPack (fast, small)
- Lazy-load results from ResultsPack when needed (on-demand)
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict

from abraxas.ers.types import TaskResult


def build_results_pack(
    *,
    run_id: str,
    tick: int,
    results: Dict[str, TaskResult],
    provenance: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build a ResultsPack.v0 artifact from task results.

    Args:
        run_id: Run identifier
        tick: Tick number
        results: Dict mapping task name to TaskResult
        provenance: Provenance metadata

    Returns:
        ResultsPack.v0 dict with deterministic ordering
    """
    # Deterministic ordering by task name
    items = []
    for name in sorted(results.keys()):
        tr = results[name]
        items.append({
            "task": name,
            "result": asdict(tr),
        })

    return {
        "schema": "ResultsPack.v0",
        "run_id": run_id,
        "tick": int(tick),
        "items": items,
        "provenance": {k: provenance[k] for k in sorted(provenance.keys())},
    }


def make_result_ref(*, results_pack_path: str, task_name: str) -> Dict[str, Any]:
    """
    Create a lightweight result reference pointer.

    AAL-Viz can follow this to load the actual result:
    1. Load ResultsPack JSON from path
    2. Find item where item["task"] == task_name
    3. Return item["result"]

    Args:
        results_pack_path: Path to ResultsPack JSON file
        task_name: Task name to reference

    Returns:
        ResultRef.v0 dict
    """
    return {
        "schema": "ResultRef.v0",
        "results_pack": results_pack_path,
        "task": task_name,
    }


__all__ = ["build_results_pack", "make_result_ref"]
