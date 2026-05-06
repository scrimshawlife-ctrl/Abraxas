from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from core.models.governance import Authority
import hashlib
import json


class RuneExecutionContext(BaseModel):
    schema_version: str = "RuneExecutionContext.v1"
    execution_id: str
    pipeline_id: str
    lane: str
    execution_mode: str = "shadow_only"
    invoked_runes: List[str]
    route_graph_hash: str
    authority: Authority
    metadata: Dict = {}

    def __init__(self, **data):
        super().__init__(**data)
        if self.execution_mode != "shadow_only":
            raise ValueError("execution_mode must be 'shadow_only'")
        if not self.invoked_runes:
            raise ValueError("invoked_runes cannot be empty")
        if not self.route_graph_hash:
            raise ValueError("route_graph_hash is required")
        if not self.pipeline_id:
            raise ValueError("pipeline_id is required")
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")

    def execution_context_hash(self) -> str:
        canonical_data = json.dumps({
            "execution_id": self.execution_id,
            "pipeline_id": self.pipeline_id,
            "lane": self.lane,
            "execution_mode": self.execution_mode,
            "invoked_runes": sorted(self.invoked_runes),
            "route_graph_hash": self.route_graph_hash,
            "metadata": self.metadata,
        }, sort_keys=True).encode("utf-8")
        return hashlib.sha256(canonical_data).hexdigest()