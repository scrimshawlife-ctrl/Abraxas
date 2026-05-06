from pydantic import BaseModel, Field, root_validator
from typing import List, Optional, Dict
from core.execution.context import RuneExecutionContext
from core.runes.runtime import RuneInvocationPlan
from core.runes.receipts import RuneInvocationReceipt, build_receipt_chain
from core.runes.execution import execute_rune
from core.models.governance import Authority

class ShadowExecutionRun(BaseModel):
    schema_version: str = Field("ShadowExecutionRun.v1", const=True)
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

    @root_validator
    def validate_run(cls, values):
        if not values["authority"].is_locked():
            raise ValueError("authority must be locked")
        return values

def run_shadow_execution(contract: Dict, route_graph: Dict, rune_catalog: Dict) -> ShadowExecutionRun:
    """
    Executes the provided contract deterministically in shadow mode.

    Args:
        contract (Dict): The execution contract.
        route_graph (Dict): Route graph for validation.
        rune_catalog (Dict): Available rune definitions.

    Returns:
        ShadowExecutionRun: The execution run result.
    """
    import uuid

    # Step 1: Build Execution Context
    execution_context = RuneExecutionContext(
        execution_id=str(uuid.uuid4()),
        pipeline_id=contract["pipeline_id"],
        lane=contract["lane"],
        execution_mode="shadow_only",
        invoked_runes=contract["required_runes"],
        route_graph_hash=route_graph["graph_hash"],
        authority=contract["authority"],
        metadata=contract.get("metadata", {})
    )
    
    context_hash = execution_context.execution_context_hash()

    # Step 2: Build Invocation Plan
    invocation_plan = RuneInvocationPlan(
        plan_id=str(uuid.uuid4()),
        pipeline_id=contract["pipeline_id"],
        steps=[],
        authority=contract["authority"]
    )
    plan_hash = invocation_plan.invocation_plan_hash()

    # Step 3: Execute Steps
    executed_steps = []
    failed_steps = []
    skipped_steps = []
    receipts = []

    for step in invocation_plan.steps:
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
                input_hash="input_hash_placeholder",  # Placeholder
                output_hash=result["payload_hash"],
                route_node=step.route_node,
                prior_receipt_hash=None,  # Added during chaining
                authority=contract["authority"],
                status="success" if result["status"] == "completed" else "failure",
                errors=[]
            )
            receipts.append(receipt)
        except Exception as e:
            failed_steps.append(step.step_id)

    # Step 4: Chain Receipts
    receipt_chain = build_receipt_chain(receipts)
    chain_hash = receipt_chain["chain_hash"]

    # Step 5: Return Execution Run
    return ShadowExecutionRun(
        run_id=str(uuid.uuid4()),
        pipeline_id=contract["pipeline_id"],
        execution_context_hash=context_hash,
        invocation_plan_hash=plan_hash,
        receipt_chain_hash=chain_hash,
        executed_steps=executed_steps,
        failed_steps=failed_steps,
        skipped_steps=skipped_steps,
        status="completed" if not failed_steps else "partial",
        authority=contract["authority"],
        recommended_next_state="review" if failed_steps else "proceed"
    )