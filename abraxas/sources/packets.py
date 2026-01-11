"""Source packet schema for deterministic intake."""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex


SOURCE_PACKET_SCHEMA_VERSION = "source_packet.v0.2"


class SourcePacket(BaseModel):
    source_id: str
    observed_at_utc: str
    window_start_utc: Optional[str]
    window_end_utc: Optional[str]
    schema_version: str = Field(default=SOURCE_PACKET_SCHEMA_VERSION)
    domain: str = Field(default="unknown")
    data_grade: str = Field(default="real")  # real | simulated | derived
    payload: Dict[str, Any]
    provenance: Dict[str, Any] = Field(default_factory=dict)

    def canonical_payload(self) -> Dict[str, Any]:
        payload = self.model_dump()
        payload["payload"] = _sort_obj(payload.get("payload") or {})
        payload["provenance"] = _sort_obj(payload.get("provenance") or {})
        return payload

    def packet_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical_payload()))


def _sort_obj(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _sort_obj(obj[k]) for k in sorted(obj.keys())}
    if isinstance(obj, list):
        return [_sort_obj(item) for item in obj]
    return obj
