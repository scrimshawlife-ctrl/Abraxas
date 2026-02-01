"""
SDCT v0.1 (Symbolic Domain Cartridge Template) - Core Types

Domain-agnostic type contracts for the cartridge system.
All domains emit NormalizedEvidence; chassis scores/promotes without domain knowledge.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional

from ..provenance import sha256_hex, stable_json_dumps


# -----------------------------------------------------------------------------
# DomainDescriptor: describes a cartridge's identity and constraints
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class DomainDescriptor:
    """
    Describes a symbolic domain cartridge.

    Attributes:
        domain_id: Unique identifier (e.g., "text.subword.v1")
        domain_name: Human-readable name
        domain_version: SemVer string
        motif_kind: Type of motif this domain extracts (e.g., "subword", "digit", "numogram")
        alphabet: Character set constraint (e.g., "a-z", "0-9", "mixed")
        constraints: List of constraint tags (e.g., ["alpha_only", "min_len>=3"])
        params_schema_id: Reference to JSON schema for domain-specific params
    """

    domain_id: str
    domain_name: str
    domain_version: str
    motif_kind: str
    alphabet: str
    constraints: FrozenSet[str]
    params_schema_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "domain_name": self.domain_name,
            "domain_version": self.domain_version,
            "motif_kind": self.motif_kind,
            "alphabet": self.alphabet,
            "constraints": sorted(self.constraints),
            "params_schema_id": self.params_schema_id,
        }

    def content_hash(self) -> str:
        """Deterministic hash of descriptor for provenance."""
        return sha256_hex(stable_json_dumps(self.to_dict()).encode("utf-8"))


# -----------------------------------------------------------------------------
# Motif: domain-specific extracted pattern (must stringify deterministically)
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class Motif:
    """
    A motif extracted by a domain cartridge.

    The `motif_id` must be namespaced by domain to allow coexistence.
    Example: "text.subword.v1:sator", "digit.v1:1776"
    """

    domain_id: str
    motif_id: str  # Namespaced: "{domain_id}:{motif_text}" or similar
    motif_text: str
    motif_len: int
    motif_complexity: float  # Domain-defined; 0.0-1.0 normalized
    lane_hint: str  # "core" | "canary" | "shadow" | "candidate"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "motif_id": self.motif_id,
            "motif_text": self.motif_text,
            "motif_len": self.motif_len,
            "motif_complexity": self.motif_complexity,
            "lane_hint": self.lane_hint,
            "metadata": self.metadata,
        }


# -----------------------------------------------------------------------------
# NormalizedEvidence: the spine contract (domain-agnostic)
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class NormalizedEvidence:
    """
    Normalized evidence emitted by cartridges.

    This is THE spine contract - chassis can score/promote without knowing domain internals.
    All cartridges MUST emit this structure.
    """

    domain_id: str
    motif_id: str  # Namespaced motif identifier
    item_id: str
    source: str
    event_key: str  # Cluster key (keyed in Academic/Enterprise tiers)
    mentions: int  # Per-item mention count (usually 1)
    signals: Dict[str, float] = field(default_factory=dict)  # tap, sas, pfdi, etc.
    tags: Dict[str, Any] = field(default_factory=dict)  # lane, tier, etc.

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "motif_id": self.motif_id,
            "item_id": self.item_id,
            "source": self.source,
            "event_key": self.event_key,
            "mentions": self.mentions,
            "signals": dict(self.signals),
            "tags": dict(self.tags),
        }


# -----------------------------------------------------------------------------
# AggregatedMotifStats: what SAS/LPS consume (post-aggregation)
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class AggregatedMotifStats:
    """
    Aggregated statistics for a motif across all evidence in a run.

    This is what SAS/LPS scoring consumes.
    """

    domain_id: str
    motif_id: str
    lane: str  # Current lane assignment
    mentions_total: int
    sources_count: int
    events_count: int
    sas: float  # Subword Aggregation Score (domain-agnostic)
    tap_max: float  # Max TAP (for token domains); 0.0 for non-token domains
    pfdi_max: float  # Max PFDI observed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "motif_id": self.motif_id,
            "lane": self.lane,
            "mentions_total": self.mentions_total,
            "sources_count": self.sources_count,
            "events_count": self.events_count,
            "sas": self.sas,
            "tap_max": self.tap_max,
            "pfdi_max": self.pfdi_max,
        }


# -----------------------------------------------------------------------------
# RawItem: minimal assumed input shape
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class RawItem:
    """
    Minimal item structure expected by cartridges.

    Cartridges receive this; they encode it into domain-specific SymbolObject.
    """

    id: str
    source: str
    published_at: str  # ISO8601
    title: str
    text: str
    url: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RawItem":
        return cls(
            id=str(d.get("id", "")),
            source=str(d.get("source", "")),
            published_at=str(d.get("published_at", "")),
            title=str(d.get("title", "")),
            text=str(d.get("text", "")),
            url=d.get("url"),
        )

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "id": self.id,
            "source": self.source,
            "published_at": self.published_at,
            "title": self.title,
            "text": self.text,
        }
        if self.url is not None:
            d["url"] = self.url
        return d


# -----------------------------------------------------------------------------
# Lane ordering (canonical, shared across domains)
# -----------------------------------------------------------------------------

LANE_ORDER = {
    "candidate": 0,
    "shadow": 1,
    "canary": 2,
    "core": 3,
}

LANE_NAMES = ["candidate", "shadow", "canary", "core"]


def lane_index(lane: str) -> int:
    """Get canonical lane index (0=candidate, 3=core)."""
    return LANE_ORDER.get(lane, 0)


def lane_name(index: int) -> str:
    """Get lane name from index."""
    if 0 <= index < len(LANE_NAMES):
        return LANE_NAMES[index]
    return "candidate"
