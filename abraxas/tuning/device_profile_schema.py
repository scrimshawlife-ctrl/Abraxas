"""Device profile schema for deterministic portfolio selection."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex


class DeviceMatchCriteria(BaseModel):
    cpu_arch: List[str] = Field(default_factory=lambda: ["*"])
    platform: List[str] = Field(default_factory=lambda: ["*"])
    mem_max_bytes: Optional[int] = None
    storage_class: Optional[str] = "*"
    gpu_present: Optional[bool] = None


class PortfolioRef(BaseModel):
    portfolio_ir_hash: str


class DeviceProfileProvenance(BaseModel):
    created_at_utc: str
    author: str
    evidence_profiles: List[str] = Field(default_factory=list)


class DeviceProfile(BaseModel):
    profile_id: str
    label: str
    match_criteria: DeviceMatchCriteria
    portfolio_ref: PortfolioRef
    priority: int = 100
    provenance: DeviceProfileProvenance

    def canonical_payload(self) -> Dict[str, Any]:
        payload = self.model_dump()
        payload["match_criteria"]["cpu_arch"] = sorted(payload["match_criteria"].get("cpu_arch") or [])
        payload["match_criteria"]["platform"] = sorted(payload["match_criteria"].get("platform") or [])
        payload["provenance"]["evidence_profiles"] = sorted(payload["provenance"].get("evidence_profiles") or [])
        return payload

    def profile_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical_payload()))
