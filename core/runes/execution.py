from pydantic import BaseModel
from core.execution.context import RuneExecutionContext
from core.runes.receipts import RuneInvocationReceipt
import hashlib
import json

def execute_rune(rune_id: str, payload: dict, context: RuneExecutionContext, step: dict):
    """
    Deterministically execute a rune based on the provided context and payload.

    Args:
        rune_id (str): The ID of the rune to execute.
        payload (dict): The input payload for the rune execution.
        context (RuneExecutionContext): The execution context.
        step (dict): The invocation step details.

    Returns:
        RuneInvocationReceipt: A receipt detailing the execution outcome.
    """
    # Canonicalize payload
    canonical_payload = json.dumps(payload, sort_keys=True).encode("utf-8")

    # Hash payload deterministically
    payload_hash = hashlib.sha256(canonical_payload).hexdigest()

    # Generate deterministic output (stub execution)
    output_payload = {"result": f"output from {rune_id}"}
    canonical_output = json.dumps(output_payload, sort_keys=True).encode("utf-8")
    output_hash = hashlib.sha256(canonical_output).hexdigest()

    # Generate a receipt
    receipt = RuneInvocationReceipt(
        receipt_id=hashlib.sha256(f"{rune_id}{context.execution_id}{step['step_id']}".encode("utf-8")).hexdigest(),
        execution_id=context.execution_id,
        rune_id=rune_id,
        pipeline_id=context.pipeline_id,
        step_id=step['step_id'],
        execution_state="completed",
        input_hash=payload_hash,
        output_hash=output_hash,
        route_node=step['route_node'],
        prior_receipt_hash=None,  # Determined later when linking receipts
        authority=context.authority,
        status="success",
        errors=[]
    )

    return {
        "rune_id": rune_id,
        "payload_hash": payload_hash,
        "execution_hash": receipt.receipt_hash(),
        "status": receipt.execution_state
    }