from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from core.execution.context import RuneExecutionContext
from core.runes.runtime import RuneInvocationPlan, build_invocation_plan
from core.runes.receipts import RuneInvocationReceipt, build_receipt_chain
from core.runes.execution import execute_rune
from core.models.governance import Authority
import uuid
import json
from hashlib import sha256

VALID_STATUSES = {"completed", "partial", "failed", "not_computable"}


class ShadowExecutionRun(BaseModel):
    schema_version: str = "ShadowExecutionRun.v1"
    run_id: str
    pipeline_id: str
    execution_context_hash: str
    invocation_plan_hash: str
    receipt_chain_hash: str
    executed_steps: List[str]
    failed_steps: List[str]
    skipped_steps: List[str]
    status: str
    authority: Authority
    recommended_next_state: str

    def __init__(self, **data):
        super().__init__(**data)
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")


def run_shadow_execution(contract: Dict, route_graph: Dict, rune_catalog: Dict) -> ShadowExecutionRun:
    # Derive a deterministic execution_id from contract inputs
    execution_id = sha256(json.dumps({
        "pipeline_id": contract["pipeline_id"],
        "lane": contract.get("lane", "shadow"),
        "required_runes": sorted(contract["required_runes"]),
        "graph_hash": route_graph["graph_hash"],
    }, sort_keys=True).encode("utf-8")).hexdigest()

    # Build execution context
    execution_context = RuneExecutionContext(
        execution_id=execution_id,
        pipeline_id=contract["pipeline_id"],
        lane=contract.get("lane", "shadow"),
        execution_mode="shadow_only",
        invoked_runes=contract["required_runes"],
        route_graph_hash=route_graph["graph_hash"],
        authority=contract["authority"],
        metadata=contract.get("metadata", {}),
    )
    context_hash = execution_context.execution_context_hash()
    invocation_plan = build_invocation_plan(contract, route_graph, rune_catalog)
    plan_hash = invocation_plan.invocation_plan_hash()

    executed_steps = []
    failed_steps = []
    skipped_steps = []
    receipts = []

    for step in sorted(invocation_plan.steps, key=lambda s: s.deterministic_order):
        node = route_graph.get(step.rune_id, {}).get("node", "")
        if not node or node == "unknown":
            failed_steps.append(step.step_id)
            continue
        try:
            result = execute_rune(step.rune_id, {}, execution_context, step)
            if result["status"] == "completed":
                executed_steps.append(step.step_id)
            else:
                failed_steps.append(step.step_id)
            receipt = RuneInvocationReceipt(
                receipt_id=result["execution_hash"],
                execution_id=execution_context.execution_id,
                rune_id=step.rune_id,
                pipeline_id=contract["pipeline_id"],
                step_id=step.step_id,
                execution_state=result["status"],
                input_hash=result["payload_hash"],
                output_hash=result["payload_hash"],
                route_node=step.route_node,
                authority=contract["authority"],
                status="success" if result["status"] == "completed" else "failure",
                errors=[],
            )
            receipts.append(receipt)
        except Exception:
            failed_steps.append(step.step_id)

    if receipts:
        receipt_chain = build_receipt_chain(receipts)
        chain_hash = receipt_chain["chain_hash"]
    else:
        chain_hash = sha256(b"empty").hexdigest()

    if not failed_steps and executed_steps:
        status = "completed"
        recommended = "proceed"
    elif failed_steps and executed_steps:
        status = "partial"
        recommended = "review"
    elif failed_steps and not executed_steps:
        status = "failed"
        recommended = "rollback"
    else:
        status = "not_computable"
        recommended = "review"

    return ShadowExecutionRun(
        run_id=str(uuid.uuid4()),
        pipeline_id=contract["pipeline_id"],
        execution_context_hash=context_hash,
        invocation_plan_hash=plan_hash,
        receipt_chain_hash=chain_hash,
        executed_steps=executed_steps,
        failed_steps=failed_steps,
        skipped_steps=skipped_steps,
        status=status,
        authority=contract["authority"],
        recommended_next_state=recommended,
    )