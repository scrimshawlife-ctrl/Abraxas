from __future__ import annotations

from typing import Any

from abx.operator_workflows import run_operator_workflow
from abx.runtime.runIsolation import RunContext, isolate_payload


def execute_workflow_with_context(ctx: RunContext, workflow: str, payload: dict[str, Any]) -> dict[str, Any]:
    scoped_payload = isolate_payload(payload, ctx)
    output = run_operator_workflow(workflow, scoped_payload)
    return {
        "artifactType": "OperatorWorkflowContextArtifact.v1",
        "artifactId": f"operator-context-{ctx.run_id}-{workflow}",
        "runId": ctx.run_id,
        "workflow": workflow,
        "activeRun": ctx.context_id,
        "output": output,
    }
