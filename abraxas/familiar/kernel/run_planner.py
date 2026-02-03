from __future__ import annotations

from typing import Any, Dict, List
import heapq


class PlanError(ValueError):
    pass


def _normalize_step(step: Dict[str, Any]) -> Dict[str, Any]:
    if "step_id" not in step:
        raise PlanError("step_id is required for each step")
    step_id = step["step_id"]
    if not isinstance(step_id, str) or not step_id:
        raise PlanError("step_id must be a non-empty string")
    depends_on = step.get("depends_on") or []
    if not isinstance(depends_on, list):
        raise PlanError("depends_on must be a list")
    for dep in depends_on:
        if not isinstance(dep, str) or not dep:
            raise PlanError("depends_on entries must be non-empty strings")
    normalized = {
        "step_id": step_id,
        "action": step.get("action") or "noop",
        "depends_on": sorted(set(depends_on)),
        "parameters": step.get("parameters"),
    }
    return normalized


def _topological_order(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    step_map: Dict[str, Dict[str, Any]] = {}
    for step in steps:
        step_id = step["step_id"]
        if step_id in step_map:
            raise PlanError(f"duplicate step_id: {step_id}")
        step_map[step_id] = step

    graph: Dict[str, List[str]] = {step_id: [] for step_id in step_map}
    indegree: Dict[str, int] = {step_id: 0 for step_id in step_map}

    for step_id, step in step_map.items():
        for dep in step.get("depends_on", []):
            if dep not in step_map:
                raise PlanError(f"missing dependency: {dep}")
            graph[dep].append(step_id)
            indegree[step_id] += 1

    for deps in graph.values():
        deps.sort()

    heap: List[str] = [sid for sid, deg in indegree.items() if deg == 0]
    heapq.heapify(heap)

    ordered: List[Dict[str, Any]] = []
    while heap:
        sid = heapq.heappop(heap)
        ordered.append(step_map[sid])
        for neighbor in graph[sid]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                heapq.heappush(heap, neighbor)

    if len(ordered) != len(step_map):
        raise PlanError("cycle detected in step graph")

    return ordered


def build_run_plan(run_request: Dict[str, Any]) -> Dict[str, Any]:
    steps_raw = run_request.get("steps", [])
    if not isinstance(steps_raw, list):
        raise PlanError("steps must be a list")

    normalized_steps = [_normalize_step(step) for step in steps_raw]
    ordered_steps = _topological_order(normalized_steps)

    return {
        "schema_version": "v0",
        "run_id": run_request.get("run_id"),
        "steps": ordered_steps,
        "ordered_step_ids": [step["step_id"] for step in ordered_steps],
    }
