"""Source packet schema for deterministic intake."""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.evidence.claim_strength import ClaimStrength
from abraxas.evidence.data_grade import UNDECLARED


SOURCE_PACKET_SCHEMA_VERSION = "source_packet.v0.2"


class SourcePacket(BaseModel):
    source_id: str
    observed_at_utc: str
    window_start_utc: Optional[str]
    window_end_utc: Optional[str]
    schema_version: str = Field(default=SOURCE_PACKET_SCHEMA_VERSION)
    domain: str = Field(default="unknown")
    data_grade: str = Field(default=UNDECLARED)  # see abraxas/evidence/data_grade.py
    payload: Dict[str, Any]
    provenance: Dict[str, Any] = Field(default_factory=dict)
    #: Metadata, and excluded from `canonical_payload` (Risk 3). Typed as the VALIDATED model rather
    #: than `Dict[str, Any]`: it was a loose dict, so a malformed claim strength passed silently while
    #: `ClaimStrength` had no production caller at all. Typing it here means the schema enforces itself
    #: at the boundary. Typed BEFORE any producer emits the field, which is what makes it cheap -- after
    #: a producer exists, tightening the type would reject data already in flight.
    claim_strength: Optional[ClaimStrength] = None

    def canonical_payload(self) -> Dict[str, Any]:
        payload = self.model_dump(exclude={"claim_strength"})
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
