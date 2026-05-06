from pydantic import BaseModel
from core.execution.context import RuneExecutionContext
from core.runes.receipts import RuneInvocationReceipt
import hashlib
import json


def _step_attr(step, key):
    """Get step attribute from either a dict or object."""
    if isinstance(step, dict):
        return step[key]
    return getattr(step, key)


def execute_rune(rune_id: str, payload: dict, context: RuneExecutionContext, step):
    """
    Deterministically execute a rune based on the provided context and payload.
    """
    canonical_payload = json.dumps(payload, sort_keys=True).encode("utf-8")
    payload_hash = hashlib.sha256(canonical_payload).hexdigest()

    output_payload = {"result": f"output from {rune_id}"}
    canonical_output = json.dumps(output_payload, sort_keys=True).encode("utf-8")
    output_hash = hashlib.sha256(canonical_output).hexdigest()

    step_id = _step_attr(step, "step_id")
    route_node = _step_attr(step, "route_node")

    receipt = RuneInvocationReceipt(
        receipt_id=hashlib.sha256(f"{rune_id}{context.execution_id}{step_id}".encode("utf-8")).hexdigest(),
        execution_id=context.execution_id,
        rune_id=rune_id,
        pipeline_id=context.pipeline_id,
        step_id=step_id,
        execution_state="completed",
        input_hash=payload_hash,
        output_hash=output_hash,
        route_node=route_node,
        prior_receipt_hash=None,
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