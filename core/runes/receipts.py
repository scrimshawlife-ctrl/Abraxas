from pydantic import BaseModel, Field, root_validator
from typing import List, Optional
from core.models.governance import Authority
from typing import List
from hashlib import sha256
import json

class RuneInvocationReceipt(BaseModel):
    schema_version: str = Field("RuneInvocationReceipt.v1", const=True)
    receipt_id: str
    execution_id: str
    rune_id: str
    pipeline_id: str
    step_id: str
    execution_state: str
    input_hash: str
    output_hash: str
    route_node: str
    prior_receipt_hash: Optional[str] = None
    authority: Authority
    status: str
    errors: List[str] = Field(default_factory=list)

    @root_validator
    def validate_receipt(cls, values):
        if not values["authority"].is_locked():
            raise ValueError("authority must be locked")
        if not values["route_node"]:
            raise ValueError("route_node is required")
        if not values["execution_state"] in ["started", "completed", "failed"]:
            raise ValueError("execution_state must be 'started', 'completed', or 'failed'")
        return values

    def receipt_hash(self) -> str:
        """
        Generate a deterministic hash for the receipt
        """
        canonical_data = json.dumps(
            {
                "receipt_id": self.receipt_id,
                "execution_id": self.execution_id,
                "rune_id": self.rune_id,
                "pipeline_id": self.pipeline_id,
                "step_id": self.step_id,
                "execution_state": self.execution_state,
                "input_hash": self.input_hash,
                "output_hash": self.output_hash,
                "route_node": self.route_node,
                "prior_receipt_hash": self.prior_receipt_hash,
                "status": self.status,
                "errors": self.errors
            },
            sort_keys=True
        ).encode("utf-8")
        return sha256(canonical_data).hexdigest()

def build_receipt_chain(receipts: List[RuneInvocationReceipt]) -> dict:
    """
    Builds a deterministic receipt chain and calculates the chain hash.

    Args:
        receipts (List[RuneInvocationReceipt]): List of invocation receipts.

    Returns:
        dict: Chain hash, receipt count, and receipts with updated prior receipt references.
    """
    if not receipts:
        raise ValueError("Receipts list cannot be empty.")

    # Ensure receipts are ordered deterministically
    sorted_receipts = sorted(receipts, key=lambda r: r.receipt_id)

    # Chain receipts deterministically
    prior_hash = None
    for receipt in sorted_receipts:
        receipt.prior_receipt_hash = prior_hash
        prior_hash = receipt.receipt_hash()

    # Calculate overall chain hash
    canonical_chain = json.dumps(
        [
            {
                "receipt_id": r.receipt_id,
                "execution_id": r.execution_id,
                "rune_id": r.rune_id,
                "input_hash": r.input_hash,
                "output_hash": r.output_hash,
                "prior_receipt_hash": r.prior_receipt_hash
            }
            for r in sorted_receipts
        ],
        sort_keys=True
    ).encode("utf-8")

    chain_hash = sha256(canonical_chain).hexdigest()

    return {
        "chain_hash": chain_hash,
        "receipt_count": len(sorted_receipts),
        "receipts": sorted_receipts
    }