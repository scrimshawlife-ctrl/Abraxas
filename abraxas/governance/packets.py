"""Governance packet schema for document data."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex


class DocItem(BaseModel):
    ts_utc: str
    title: str
    body: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    raw_hash: str


class GovernancePacket(BaseModel):
    source_id: str
    window_start_utc: Optional[str]
    window_end_utc: Optional[str]
    documents: List[DocItem] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    def packet_hash(self) -> str:
        return sha256_hex(canonical_json(self.model_dump()))
