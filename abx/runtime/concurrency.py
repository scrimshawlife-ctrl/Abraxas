from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from abx.operator_workflows import run_operator_workflow
from abx.runtime.runIsolation import RunContext, isolate_payload
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


@dataclass(frozen=True)
class WorkflowExecutionArtifact:
    artifact_type: str
    artifact_id: str
    run_id: str
    workflow_id: str
    ordering_key: str
    idempotency_key: str
    output_ref: str


def _idempotency_key(run_id: str, workflow_id: str, payload: dict[str, Any]) -> str:
    return sha256_bytes(dumps_stable({"run_id": run_id, "workflow_id": workflow_id, "payload": payload}).encode("utf-8"))


def execute_overlap_safe_workflows(ctx: RunContext, workflow_payloads: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    ordered = sorted(workflow_payloads, key=lambda item: item[0])
    seen: set[str] = set()
    artifacts: list[WorkflowExecutionArtifact] = []
    outputs: list[dict[str, Any]] = []

    for workflow_id, payload in ordered:
        scoped_payload = isolate_payload(payload, ctx)
        idem = _idempotency_key(ctx.run_id, workflow_id, scoped_payload)
        if idem in seen:
            continue
        seen.add(idem)
        output = run_operator_workflow(workflow_id, scoped_payload)
        output_ref = str(output.get("artifactId") or output.get("artifact_id") or f"output:{workflow_id}") if isinstance(output, dict) else f"output:{workflow_id}"
        artifact = WorkflowExecutionArtifact(
            artifact_type="WorkflowExecutionArtifact.v2",
            artifact_id=f"workflow-exec-{ctx.run_id}-{workflow_id}",
            run_id=ctx.run_id,
            workflow_id=workflow_id,
            ordering_key=f"{ctx.run_id}:{workflow_id}",
            idempotency_key=idem,
            output_ref=output_ref,
        )
        artifacts.append(artifact)
        outputs.append({"workflow_id": workflow_id, "output": output})

    summary_hash = sha256_bytes(
        dumps_stable(
            {
                "run_id": ctx.run_id,
                "ordered": [a.workflow_id for a in artifacts],
                "idempotency": [a.idempotency_key for a in artifacts],
            }
        ).encode("utf-8")
    )
    return {
        "run_id": ctx.run_id,
        "ordered_workflows": [a.workflow_id for a in artifacts],
        "artifacts": [a.__dict__ for a in artifacts],
        "outputs": outputs,
        "summary_hash": summary_hash,
    }
