"""Schema for deterministic delta atlas packs."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.schema.tvm import _round_floats

DELTA_SCHEMA_VERSION = "atlas.delta.v1.0"


class DeltaAtlasPack(BaseModel):
    delta_version: str = Field(DELTA_SCHEMA_VERSION, description="Delta atlas schema version")
    base_atlas_hash: str = Field(..., description="Base atlas hash")
    compare_atlas_hash: str = Field(..., description="Compare atlas hash")
    comparison_label: str = Field(..., description="Comparison label")
    window_granularity: str = Field(..., description="Window granularity")
    frames_count: int = Field(..., description="Frames count considered")
    delta_pressures: List[Dict[str, Any]] = Field(default_factory=list)
    delta_jetstreams: List[Dict[str, Any]] = Field(default_factory=list)
    delta_cyclones: List[Dict[str, Any]] = Field(default_factory=list)
    delta_calm_zones: List[Dict[str, Any]] = Field(default_factory=list)
    delta_synchronicity_clusters: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    def canonical_payload(self) -> Dict[str, Any]:
        payload = self.model_dump()
        provenance = dict(payload.get("provenance") or {})
        provenance.pop("delta_hash", None)
        payload["provenance"] = provenance
        return _round_floats(payload)

    def delta_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical_payload()))
