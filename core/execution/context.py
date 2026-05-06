from pydantic import BaseModel, Field, root_validator
from typing import List, Dict
from core.models.governance import Authority

class RuneExecutionContext(BaseModel):
    schema_version: str = Field("RuneExecutionContext.v1", const=True)
    execution_id: str
    pipeline_id: str
    lane: str
    execution_mode: str = Field("shadow_only", const=True)
    invoked_runes: List[str]
    route_graph_hash: str
    authority: Authority
    metadata: Dict = Field(default_factory=dict)

    @root_validator
    def validate_context(cls, values):
        if values.get("execution_mode") != "shadow_only":
            raise ValueError("execution_mode must be 'shadow_only'")
        if not values["invoked_runes"]:
            raise ValueError("invoked_runes cannot be empty")
        if not values["route_graph_hash"]:
            raise ValueError("route_graph_hash is required")
        if not values["pipeline_id"]:
            raise ValueError("pipeline_id is required")
        if not values["authority"].is_locked():
            raise ValueError("authority must be locked")
        return values

    def execution_context_hash(self) -> str:
        # Calculate a deterministic hash for the execution context
        import hashlib
        import json
        canonical_data = json.dumps(
            {
                "execution_id": self.execution_id,
                "pipeline_id": self.pipeline_id,
                "lane": self.lane,
                "execution_mode": self.execution_mode,
                "invoked_runes": sorted(self.invoked_runes),
                "route_graph_hash": self.route_graph_hash,
                "metadata": self.metadata,
            },
            sort_keys=True
        ).encode("utf-8")
        return hashlib.sha256(canonical_data).hexdigest()

# Note: Authority class is assumed to be part of core.models.governance and must include an is_locked() method.