"""Schema for deterministic live atlas packs."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.schema.tvm import _round_floats

LIVE_SCHEMA_VERSION = "atlas.live.v1.0"


class LiveAtlasPack(BaseModel):
    live_version: str = Field(LIVE_SCHEMA_VERSION, description="Live atlas schema version")
    generated_at_utc: str = Field(..., description="Generation timestamp")
    window_config: Dict[str, Any] = Field(default_factory=dict)
    windows: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    def canonical_payload(self) -> Dict[str, Any]:
        payload = self.model_dump()
        provenance = dict(payload.get("provenance") or {})
        provenance.pop("live_hash", None)
        payload["provenance"] = provenance
        return _round_floats(payload)

    def live_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical_payload()))
