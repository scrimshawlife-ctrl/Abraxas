from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional
from core.models.governance import Authority


class ExecutionRollbackPacket(BaseModel):
    schema_version: str = "ExecutionRollbackPacket.v1"
    rollback_id: str
    source_execution_id: str
    reverted_receipts: List[str]
    rollback_possible: bool
    rollback_reason: str
    authority: Authority

    def __init__(self, **data):
        super().__init__(**data)
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")
        if not self.reverted_receipts:
            object.__setattr__(self, 'rollback_possible', False)


def generate_rollback_packet(
    source_execution_id: str,
    reverted_receipts: List[str],
    reason: str,
    authority: Authority,
) -> ExecutionRollbackPacket:
    import hashlib
    rollback_id = hashlib.sha256(
        f"{source_execution_id}:{reason}".encode("utf-8")
    ).hexdigest()
    return ExecutionRollbackPacket(
        rollback_id=rollback_id,
        source_execution_id=source_execution_id,
        reverted_receipts=reverted_receipts,
        rollback_possible=bool(reverted_receipts),
        rollback_reason=reason,
        authority=authority,
    )
