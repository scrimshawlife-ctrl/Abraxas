"""
Viz Resolver — Abraxas-side loader for event + resolved result.

AAL-Viz (or any UI) can call these functions to click an event
and instantly retrieve its resolved task result via meta.result_ref.

This stays inside Abraxas because it's about Abraxas artifact semantics.
AAL-Viz stays dumb and pretty; Abraxas stays the semantic authority.

Example:
    from abraxas.runtime.viz_resolve import resolve_trendpack_events

    rows = resolve_trendpack_events("./artifacts/viz/<run_id>/000000.trendpack.json")
    # rows[i] -> {"event": ..., "ref": ..., "result": ...}
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def _read_json(path: str) -> Dict[str, Any]:
    """Read and parse a JSON file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_trendpack(path: str) -> Dict[str, Any]:
    """
    Load and validate a TrendPack.v0 artifact.

    Args:
        path: Path to TrendPack JSON file

    Returns:
        Parsed TrendPack dict

    Raises:
        ValueError: If schema is not TrendPack.v0
    """
    tp = _read_json(path)
    # TrendPack uses "version" not "schema" in current implementation
    # Accept both for compatibility
    version = tp.get("version")
    schema = tp.get("schema")
    if version not in ("0.1", "TrendPack.v0") and schema != "TrendPack.v0":
        raise ValueError(f"Expected TrendPack.v0, got version={version} schema={schema}")
    return tp


def load_resultspack(path: str) -> Dict[str, Any]:
    """
    Load and validate a ResultsPack.v0 artifact.

    Args:
        path: Path to ResultsPack JSON file

    Returns:
        Parsed ResultsPack dict

    Raises:
        ValueError: If schema is not ResultsPack.v0
    """
    rp = _read_json(path)
    if rp.get("schema") != "ResultsPack.v0":
        raise ValueError(f"Expected ResultsPack.v0, got {rp.get('schema')}")
    return rp


def _index_resultspack(rp: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build dict task_name -> TaskResult dict (the asdict(TaskResult) payload).

    Deterministic: last duplicate wins (should not happen; tasks should be unique).

    Args:
        rp: Parsed ResultsPack dict

    Returns:
        Dict mapping task name to result dict
    """
    idx: Dict[str, Any] = {}
    for item in rp.get("items", []) or []:
        t = item.get("task")
        r = item.get("result")
        if isinstance(t, str):
            idx[t] = r
    return idx


# Cache for ResultsPack to avoid re-reading same file multiple times
_resultspack_cache: Dict[str, Dict[str, Any]] = {}


def _get_resultspack_index(path: str) -> Dict[str, Any]:
    """
    Get indexed ResultsPack, using cache to avoid repeated file reads.

    Args:
        path: Path to ResultsPack JSON file

    Returns:
        Dict mapping task name to result dict
    """
    if path not in _resultspack_cache:
        rp = load_resultspack(path)
        _resultspack_cache[path] = _index_resultspack(rp)
    return _resultspack_cache[path]


def clear_resultspack_cache() -> None:
    """Clear the ResultsPack cache. Useful for testing."""
    _resultspack_cache.clear()


def resolve_event_result(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Given a TrendPack event dict, resolve its ResultRef.v0 and return merged object.

    Args:
        event: A single event dict from TrendPack.timeline

    Returns:
        Dict with structure:
            {
                "event": <original event dict>,
                "result": <resolved TaskResult dict or None>,
                "ref": <ResultRef.v0 dict or None>
            }
    """
    meta = event.get("meta") or {}
    ref = meta.get("result_ref")

    # No ref or invalid ref schema
    if not isinstance(ref, dict) or ref.get("schema") != "ResultRef.v0":
        return {"event": event, "result": None, "ref": None}

    rp_path = ref.get("results_pack")
    task = ref.get("task")

    # Missing required fields in ref
    if not isinstance(rp_path, str) or not isinstance(task, str):
        return {"event": event, "result": None, "ref": ref}

    # Resolve via cached index
    try:
        idx = _get_resultspack_index(rp_path)
        return {"event": event, "result": idx.get(task), "ref": ref}
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        # ResultsPack not found or invalid - return event without result
        return {"event": event, "result": None, "ref": ref}


def resolve_trendpack_events(
    trendpack_path: str,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Load TrendPack and return list of resolved entries.

    Each entry contains the original event, its result_ref, and the resolved
    TaskResult (if available).

    Args:
        trendpack_path: Path to TrendPack JSON file
        limit: If provided, return first N events only (execution order)

    Returns:
        List of resolved event dicts:
            [{"event": ..., "ref": ..., "result": ...}, ...]
    """
    # Clear cache before batch resolution to ensure fresh reads
    clear_resultspack_cache()

    tp = load_trendpack(trendpack_path)

    # TrendPack uses "timeline" for events list
    events = tp.get("timeline", []) or []

    if limit is not None:
        events = events[: int(limit)]

    return [resolve_event_result(ev) for ev in events]


def get_event_result_by_task(
    trendpack_path: str,
    task_name: str,
) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get a single task's resolved result.

    Args:
        trendpack_path: Path to TrendPack JSON file
        task_name: Task name to find (e.g., "oracle:signal", "shadow:anagram")

    Returns:
        Resolved event dict if found, None otherwise
    """
    tp = load_trendpack(trendpack_path)
    events = tp.get("timeline", []) or []

    for ev in events:
        if ev.get("task") == task_name:
            return resolve_event_result(ev)

    return None


__all__ = [
    "load_trendpack",
    "load_resultspack",
    "resolve_event_result",
    "resolve_trendpack_events",
    "get_event_result_by_task",
    "clear_resultspack_cache",
]
