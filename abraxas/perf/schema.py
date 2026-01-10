"""Performance event schema.

Performance Drop v1.0 - PerfEvent for rent payment tracking.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


OpName = Literal[
    "acquire",
    "compress",
    "dict_train",
    "dedup",
    "packet_write",
    "packet_read",
    "cas_put",
    "cas_get",
]


class PerfEvent(BaseModel):
    """Performance event for rent payment metrics."""

    run_id: str = Field(..., description="Run identifier")
    op_name: OpName = Field(..., description="Operation name")
    source_id: str | None = Field(None, description="Optional source identifier")
    bytes_in: int = Field(0, description="Input bytes")
    bytes_out: int = Field(0, description="Output bytes")
    duration_ms: float = Field(0.0, description="Duration in milliseconds")
    cache_hit: bool = Field(False, description="Cache hit flag")
    codec_used: str | None = Field(None, description="Codec used for compression")
    compression_ratio: float | None = Field(None, description="Compression ratio (input/output)")
    decodo_used: bool = Field(False, description="Decodo scraping used flag")
    reason_code: str | None = Field(None, description="Reason code for operation")
    provenance_hashes: dict[str, str] = Field(
        default_factory=dict,
        description="Provenance hashes (input_hash, output_hash)",
    )
    timestamp_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Event timestamp",
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
