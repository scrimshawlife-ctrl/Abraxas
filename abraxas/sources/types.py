"""Core types for SourceAtlas and intake adapters."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex

SourceId = str


class SourceKind(str, Enum):
    meteorological_climate = "meteorological_climate"
    space_weather = "space_weather"
    geomagnetic = "geomagnetic"
    schumann_resonance = "schumann_resonance"
    astronomical = "astronomical"
    astronomy = "astronomy"
    astrology = "astrology"
    numerology = "numerology"
    calendars_localization = "calendars_localization"
    calendars = "calendars"
    timezones = "timezones"
    time_integrity = "time_integrity"
    linguistic = "linguistic"
    linguistic_news = "linguistic_news"
    linguistic_social = "linguistic_social"
    linguistic_search_trends = "linguistic_search_trends"
    linguistic_meme_artifacts = "linguistic_meme_artifacts"
    linguistic_forums = "linguistic_forums"
    linguistic_transcripts = "linguistic_transcripts"
    governance_docs = "governance_docs"
    legislative_agenda = "legislative_agenda"
    regulatory_updates = "regulatory_updates"
    economic_macro = "economic_macro"
    market_calendar = "market_calendar"
    inflation_prices = "inflation_prices"
    labor_stats = "labor_stats"
    supply_chain_indicators = "supply_chain_indicators"
    economic = "economic"
    governance = "governance"


class Cadence(str, Enum):
    hourly = "hourly"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    event_driven = "event_driven"
    on_release = "on_release"


class CachePolicy(str, Enum):
    required = "required"
    optional = "optional"
    disallowed = "disallowed"


class SourceRef(BaseModel):
    id: str
    title: str
    url: str


class SourceSpec(BaseModel):
    source_id: SourceId
    kind: SourceKind
    provider: str
    cadence: Cadence
    backfill: str
    tvm_vectors: List[str] = Field(default_factory=list)
    mda_domains: List[str] = Field(default_factory=list)
    adapter: str
    cache_policy: CachePolicy
    determinism_notes: str
    provenance_notes: str
    legal_notes: Optional[str] = None
    refs: List[SourceRef] = Field(default_factory=list)

    def canonical_payload(self) -> Dict[str, Any]:
        payload = self.model_dump()
        payload["tvm_vectors"] = sorted(payload.get("tvm_vectors") or [])
        payload["mda_domains"] = sorted(payload.get("mda_domains") or [])
        payload["refs"] = sorted(
            [ref.model_dump() for ref in self.refs],
            key=lambda ref: ref["id"],
        )
        return payload

    def record_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical_payload()))


class SourceCoverage(BaseModel):
    tvm_vectors: List[str] = Field(default_factory=list)
    mda_domains: List[str] = Field(default_factory=list)


class SourceAccess(BaseModel):
    adapter: str = Field(..., description="Adapter name")
    params_schema: Dict[str, Any] = Field(default_factory=dict)
    cache_policy: str = Field(..., description="cache_required|vendored_snapshot|optional")


class SourceProvenance(BaseModel):
    publisher: str
    method: str
    latency: str
    backfill_depth: str
    independence_tags: List[str] = Field(default_factory=list)


SourceRecord = SourceSpec


class SourceWindow(BaseModel):
    start_utc: Optional[str] = None
    end_utc: Optional[str] = None
    timezone: str = "UTC"


class CandidateSourceRecord(BaseModel):
    candidate_id: str
    proposed_kind: SourceKind
    proposed_provider: str
    rationale: Dict[str, Any]
    estimated_coverage: Dict[str, Any]
    redundancy_estimate: Dict[str, Any]
    provenance_plan: Dict[str, Any]
    confidence: float

    def record_hash(self) -> str:
        return sha256_hex(canonical_json(self.model_dump()))


from abraxas.sources.packets import SourcePacket  # noqa: E402
