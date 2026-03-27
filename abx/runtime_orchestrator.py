from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from abx.ers_scheduler import ERSTask, run_scheduler
from abx.operator_console import dispatch_operator_command
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable

RUNTIME_PHASES = [
    "ingest",
    "forecast_decision",
    "simulation",
    "validation_proof",
    "closure_summary",
]


@dataclass(frozen=True)
class RunPlanArtifact:
    artifact_type: str
    artifact_id: str
    run_id: str
    scenario_id: str
    phases: list[str]
    scheduler_policy: str


@dataclass(frozen=True)
class WorkflowExecutionArtifact:
    artifact_type: str
    artifact_id: str
    run_id: str
    scenario_id: str
    status: str
    dispatch_trace: list[dict[str, Any]]
    emitted_artifact_ids: list[str]
    summary_hash: str


def build_run_plan(*, run_id: str, scenario_id: str, scheduler_policy: str = "ERS.v1") -> RunPlanArtifact:
    return RunPlanArtifact(
        artifact_type="RunPlanArtifact.v1",
        artifact_id=f"run-plan-{run_id}-{scenario_id}",
        run_id=run_id,
        scenario_id=scenario_id,
        phases=list(RUNTIME_PHASES),
        scheduler_policy=scheduler_policy,
    )


def execute_run_plan(payload: dict[str, Any]) -> dict[str, Any]:
    run_id = str(payload.get("run_id") or "RUN-ORCH")
    scenario_id = str(payload.get("scenario_id") or "SCN-ORCH")
    plan = build_run_plan(run_id=run_id, scenario_id=scenario_id)

    tasks = [
        ERSTask(
            task_id="phase.simulation",
            phase="simulation",
            priority=100,
            metadata={"pressure": 0.5, "precedence": 1},
            fn=lambda: dispatch_operator_command("run-simulation", payload),
        ),
        ERSTask(
            task_id="phase.proof",
            phase="validation_proof",
            priority=90,
            metadata={"pressure": 0.4, "precedence": 2},
            fn=lambda: dispatch_operator_command("inspect-proof-chain", payload),
        ),
        ERSTask(
            task_id="phase.closure",
            phase="closure_summary",
            priority=80,
            metadata={"pressure": 0.3, "precedence": 3},
            fn=lambda: dispatch_operator_command("inspect-validation", payload),
        ),
    ]

    sched = run_scheduler(run_id=run_id, policy_id=plan.scheduler_policy, tasks=tasks, require_metadata=True)

    dispatch_trace = [
        {
            "phase": row["phase"],
            "task_id": row["task_id"],
            "scheduler_context_id": row["scheduler_context_id"],
        }
        for row in sched["results"]
    ]

    emitted_ids: list[str] = [plan.artifact_id]
    for row in sched["results"]:
        out = row["output"]
        if isinstance(out, dict):
            for key in ("simulation", "validation", "proof_summary", "proof_chain"):
                item = out.get(key) if isinstance(out.get(key), dict) else None
                if item and item.get("artifactId"):
                    emitted_ids.append(str(item["artifactId"]))
            if out.get("artifactId"):
                emitted_ids.append(str(out["artifactId"]))

    payload_hash = sha256_bytes(dumps_stable({"trace": dispatch_trace, "emitted": sorted(set(emitted_ids))}).encode("utf-8"))
    workflow = WorkflowExecutionArtifact(
        artifact_type="WorkflowExecutionArtifact.v1",
        artifact_id=f"workflow-{run_id}-{scenario_id}",
        run_id=run_id,
        scenario_id=scenario_id,
        status="VALID",
        dispatch_trace=dispatch_trace,
        emitted_artifact_ids=sorted(set(emitted_ids)),
        summary_hash=payload_hash,
    )

    return {
        "run_plan": plan.__dict__,
        "scheduler": sched,
        "workflow": workflow.__dict__,
    }
