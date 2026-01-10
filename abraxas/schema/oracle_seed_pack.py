"""Schemas for deterministic seed packs used by Oracle baselines."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.schema.tvm import TVM_VECTOR_IDS, _round_floats

SEEDPACK_SCHEMA_VERSION = "seedpack.v0.1"


class SeedRecord(BaseModel):
    """Single record in a seed pack."""

    record_id: str = Field(..., description="Deterministic record ID")
    date_utc: str = Field(..., description="ISO8601 date for the observation")
    domain: str = Field(..., description="Domain label")
    summary: str = Field(..., description="Brief description")
    vectors: Dict[str, Optional[float]] = Field(
        default_factory=dict, description="TVM vector values"
    )
    inference_score: float = Field(..., description="Explicit inference confidence [0,1]")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Provenance bundle")


class SeedPackProvenance(BaseModel):
    """Provenance for the seed pack."""

    generated_at_utc: str = Field(..., description="ISO8601 timestamp")
    sources: List[str] = Field(default_factory=list, description="Global source URLs")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions applied")
    run_id: str = Field(..., description="Deterministic run ID")


class SeedPack(BaseModel):
    """Deterministic seed pack container."""

    schema_version: str = Field(SEEDPACK_SCHEMA_VERSION, description="Seed pack schema version")
    year: int = Field(..., description="Year represented")
    records: List[SeedRecord] = Field(default_factory=list)
    provenance: SeedPackProvenance = Field(...)

    def canonical_payload(self) -> Dict[str, Any]:
        payload = self.model_dump()
        payload["records"] = [
            _round_floats(_normalize_vectors(rec)) for rec in payload.get("records") or []
        ]
        return _round_floats(payload)

    def seedpack_hash(self) -> str:
        return sha256_hex(canonical_seedpack_json(self))


def _normalize_vectors(record: Dict[str, Any]) -> Dict[str, Any]:
    vectors = record.get("vectors") or {}
    normalized: Dict[str, Optional[float]] = {}
    for vid in TVM_VECTOR_IDS:
        key = vid.value
        val = vectors.get(key)
        normalized[key] = val if val is not None else None
    record["vectors"] = normalized
    return record


def canonical_seedpack_json(pack: SeedPack | Dict[str, Any]) -> str:
    payload = pack.canonical_payload() if isinstance(pack, SeedPack) else _round_floats(pack)
    return canonical_json(payload)
