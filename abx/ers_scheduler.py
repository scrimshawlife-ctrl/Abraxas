from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class ERSSchedulerContextArtifact:
    artifact_type: str
    artifact_id: str
    run_id: str
    policy_id: str
    pressure: float
    precedence: int
    phase: str


@dataclass(frozen=True)
class ERSTask:
    task_id: str
    phase: str
    priority: int
    fn: Callable[[], Any]
    metadata: dict[str, Any] = field(default_factory=dict)


def order_tasks(tasks: list[ERSTask]) -> list[ERSTask]:
    return sorted(tasks, key=lambda t: (-int(t.priority), str(t.phase), str(t.task_id)))


def run_scheduler(
    *,
    run_id: str,
    policy_id: str,
    tasks: list[ERSTask],
    require_metadata: bool = True,
) -> dict[str, Any]:
    ordered = order_tasks(tasks)
    results: list[dict[str, Any]] = []
    contexts: list[ERSSchedulerContextArtifact] = []

    for idx, task in enumerate(ordered):
        if require_metadata and ("pressure" not in task.metadata or "precedence" not in task.metadata):
            raise ValueError(f"missing_scheduler_metadata:{task.task_id}")

        ctx = ERSSchedulerContextArtifact(
            artifact_type="SchedulerContextArtifact.v1",
            artifact_id=f"scheduler-context-{run_id}-{task.task_id}",
            run_id=run_id,
            policy_id=policy_id,
            pressure=float(task.metadata.get("pressure") or 0.0),
            precedence=int(task.metadata.get("precedence") or idx),
            phase=task.phase,
        )
        contexts.append(ctx)

        output = task.fn()
        results.append(
            {
                "task_id": task.task_id,
                "phase": task.phase,
                "priority": task.priority,
                "output": output,
                "scheduler_context_id": ctx.artifact_id,
            }
        )

    return {
        "ordered_task_ids": [t.task_id for t in ordered],
        "results": results,
        "scheduler_contexts": [c.__dict__ for c in contexts],
    }
