from pydantic import BaseModel, Field, root_validator
from typing import List, Optional
from core.models.governance import Authority

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
        import hashlib
        import json
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
        return hashlib.sha256(canonical_data).hexdigest()