"""Lifecycle IR schema for storage cache management."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex


class TierPolicy(BaseModel):
    max_age_days: Optional[int] = None
    min_age_days: Optional[int] = None
    codec: str
    zstd_level: int = 3
    dict_enabled: bool = False


class ArtifactPolicy(BaseModel):
    retain: bool = True
    allow_relocate: bool = True
    allow_delete: bool = False
    delete_after_days: Optional[int] = None
    rebuildable: bool = False


class DictionaryPolicy(BaseModel):
    retain: bool = True
    retrain_policy: str = "age_only"


class CompactionPolicy(BaseModel):
    target_ratio_gain_min: float = 0.05
    max_cpu_ms_per_run: int = 60_000
    max_bytes_written_per_run: int = 100_000_000
    max_files_per_run: int = 500


class EvictionPolicy(BaseModel):
    order: List[str] = Field(default_factory=lambda: ["parsed", "packets", "raw"])
    delete_requires_explicit_flag: bool = True


class LifecycleProvenance(BaseModel):
    derived_from_portfolio_ir_hash: str
    created_at_utc: str
    author: str


class LifecycleIR(BaseModel):
    ir_version: str = "1.0"
    tiers: Dict[str, TierPolicy]
    artifacts: Dict[str, ArtifactPolicy]
    dict_policy: DictionaryPolicy = Field(default_factory=DictionaryPolicy)
    compaction: CompactionPolicy = Field(default_factory=CompactionPolicy)
    eviction: EvictionPolicy = Field(default_factory=EvictionPolicy)
    provenance: LifecycleProvenance

    def canonical_payload(self) -> Dict[str, Any]:
        payload = self.model_dump()
        payload["tiers"] = {k: self.tiers[k].model_dump() for k in sorted(self.tiers.keys())}
        payload["artifacts"] = {k: self.artifacts[k].model_dump() for k in sorted(self.artifacts.keys())}
        payload["eviction"] = self.eviction.model_dump()
        payload["compaction"] = self.compaction.model_dump()
        payload["dict_policy"] = self.dict_policy.model_dump()
        payload["provenance"] = self.provenance.model_dump()
        return payload

    def ir_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical_payload()))
