"""Economic packet schema for time series data."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex


class TimeSeriesPoint(BaseModel):
    ts_utc: str
    value: float
    unit: str
    meta: Dict[str, Any] = Field(default_factory=dict)


class EconomicPacket(BaseModel):
    source_id: str
    window_start_utc: Optional[str]
    window_end_utc: Optional[str]
    series: List[TimeSeriesPoint] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    def packet_hash(self) -> str:
        return sha256_hex(canonical_json(self.model_dump()))
