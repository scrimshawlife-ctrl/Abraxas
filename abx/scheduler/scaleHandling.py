from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from abx.ers_scheduler import ERSTask, run_scheduler
from abx.runtime.runIsolation import RunContext
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


@dataclass(frozen=True)
class SchedulerContext:
    run_id: str
    queue_id: str
    policy_id: str
    ordered_task_ids: list[str]
    scheduler_hash: str


def run_partitioned_scheduler(*, contexts: list[RunContext], task_factory: dict[str, list[ERSTask]], policy_id: str = "ERS.v1") -> dict[str, Any]:
    per_run: list[dict[str, Any]] = []
    scheduler_contexts: list[SchedulerContext] = []

    for ctx in sorted(contexts, key=lambda x: x.run_id):
        scoped_tasks = task_factory.get(ctx.run_id, [])
        patched_tasks = [
            ERSTask(
                task_id=f"{ctx.run_id}:{task.task_id}",
                phase=task.phase,
                priority=task.priority,
                metadata={"pressure": task.metadata.get("pressure", 0.0), "precedence": task.metadata.get("precedence", 0)},
                fn=task.fn,
            )
            for task in scoped_tasks
        ]
        result = run_scheduler(run_id=ctx.run_id, policy_id=policy_id, tasks=patched_tasks, require_metadata=True)
        per_run.append({"run_id": ctx.run_id, "scheduler": result})

        scheduler_hash = sha256_bytes(
            dumps_stable({"run_id": ctx.run_id, "ordered_task_ids": result["ordered_task_ids"], "policy_id": policy_id}).encode("utf-8")
        )
        scheduler_contexts.append(
            SchedulerContext(
                run_id=ctx.run_id,
                queue_id=f"queue-{ctx.run_id}",
                policy_id=policy_id,
                ordered_task_ids=list(result["ordered_task_ids"]),
                scheduler_hash=scheduler_hash,
            )
        )

    return {
        "artifactType": "ScaleSchedulerInspectionArtifact.v1",
        "artifactId": "scale-scheduler-inspection",
        "runs": per_run,
        "schedulerContexts": [x.__dict__ for x in scheduler_contexts],
    }
