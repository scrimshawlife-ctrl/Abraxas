"""Schema for deterministic Semantic Weather Atlas packs."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.schema.tvm import _round_floats

ATLAS_SCHEMA_VERSION = "atlas.v1.0"


class AtlasPack(BaseModel):
    atlas_version: str = Field(ATLAS_SCHEMA_VERSION, description="Atlas schema version")
    year: int = Field(..., description="Year represented")
    window_granularity: str = Field(..., description="Window granularity")
    frames_count: int = Field(..., description="Count of frames in source seedpack")
    pressure_cells: List[Dict[str, Any]] = Field(default_factory=list)
    jetstreams: List[Dict[str, Any]] = Field(default_factory=list)
    cyclones: List[Dict[str, Any]] = Field(default_factory=list)
    calm_zones: List[Dict[str, Any]] = Field(default_factory=list)
    synchronicity_clusters: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    def canonical_payload(self) -> Dict[str, Any]:
        payload = self.model_dump()
        provenance = dict(payload.get("provenance") or {})
        provenance.pop("atlas_hash", None)
        payload["provenance"] = provenance
        return _round_floats(payload)

    def atlas_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical_payload()))
