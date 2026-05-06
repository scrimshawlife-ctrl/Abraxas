from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional
from core.models.governance import Authority


class RuneReplayPacket(BaseModel):
    schema_version: str = "RuneReplayPacket.v1"
    replay_id: str
    source_execution_hash: str
    replay_execution_hash: str
    identical_output: bool
    deterministic_match: bool
    mismatched_receipts: List[str]
    authority: Authority
    status: str

    def __init__(self, **data):
        super().__init__(**data)
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")
        if self.mismatched_receipts:
            object.__setattr__(self, 'deterministic_match', False)
            object.__setattr__(self, 'identical_output', False)
