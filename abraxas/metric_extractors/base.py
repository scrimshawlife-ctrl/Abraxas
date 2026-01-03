"""Base metric extractor interfaces and schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex


class MetricPoint(BaseModel):
    metric_id: str
    value: Optional[float | str]
    ts_utc: str
    window_start_utc: Optional[str]
    window_end_utc: Optional[str]
    source_id: str
    provenance: Dict[str, Any] = Field(default_factory=dict)
    computability: str = "computed"

    def canonical_payload(self) -> Dict[str, Any]:
        payload = self.model_dump()
        payload["provenance"] = {k: payload["provenance"][k] for k in sorted(payload["provenance"].keys())}
        return payload

    def point_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical_payload()))


class MetricExtractor:
    extractor_name: str = "base"
    version: str = "0.1"

    def extractor_id(self) -> str:
        return self.extractor_name

    def extractor_version(self) -> str:
        return self.version

    def accepts(self, source_id: str) -> bool:
        raise NotImplementedError

    def extract(self, packets: List[Dict[str, Any]], run_ctx: Dict[str, Any]) -> List[MetricPoint]:
        raise NotImplementedError


def packet_hash(packet: Dict[str, Any]) -> str:
    return sha256_hex(canonical_json(packet))
