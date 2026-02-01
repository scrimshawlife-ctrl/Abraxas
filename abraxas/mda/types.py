from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, Literal, Optional, Tuple


class Domain(str, Enum):
    GEOPOLITICS = "geopolitics"
    TECH_AI = "tech_ai"
    FINANCE_MACRO = "finance_macro"
    CLIMATE_ENERGY = "climate_energy"
    CULTURE_MEMES = "culture_memes"
    BIOSECURITY_HEALTH = "biosecurity_health"
    WILDCARDS = "wildcards"


class DSPStatus(str, Enum):
    OK = "ok"
    NOT_COMPUTABLE = "not_computable"


class EdgeType(str, Enum):
    CORRELATES_WITH = "correlates_with"
    CAUSAL_HYPOTHESIS = "causal_hypothesis"
    SHARED_MEME = "shared_meme"
    SHARED_ACTOR = "shared_actor"
    TEMPORAL_ALIGNMENT = "temporal_alignment"


def _q(x: float, places: int = 6) -> float:
    """
    Quantize floats to stabilize hashing across runs/platforms.
    """
    d = Decimal(str(x)).quantize(Decimal("1." + "0" * places), rounding=ROUND_HALF_UP)
    return float(d)


def stable_json_dumps(obj: Any) -> str:
    """
    Deterministic JSON serialization for hashing.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Window:
    from_iso: str
    to_iso: str


@dataclass(frozen=True)
class Provenance:
    module: str
    version: str
    input_hash: str
    run_seed: int


@dataclass(frozen=True)
class Claim:
    claim: str
    confidence: float
    evidence_refs: Tuple[str, ...] = field(default_factory=tuple)

    def to_json(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "confidence": _q(self.confidence),
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class Event:
    event_id: str
    title: str
    time_iso: str
    claims: Tuple[Claim, ...] = field(default_factory=tuple)
    tags: Tuple[str, ...] = field(default_factory=tuple)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "title": self.title,
            "time": self.time_iso,
            "claims": [c.to_json() for c in self.claims],
            "tags": list(self.tags),
            "metrics": self.metrics,
        }


@dataclass(frozen=True)
class Scores:
    impact: float
    velocity: float
    uncertainty: float
    polarity: float = 0.0

    def to_json(self) -> Dict[str, Any]:
        return {
            "impact": _q(self.impact),
            "velocity": _q(self.velocity),
            "uncertainty": _q(self.uncertainty),
            "polarity": _q(self.polarity),
        }


@dataclass(frozen=True)
class DomainSignalPack:
    domain: str
    subdomain: str
    status: str
    window: Window
    scores: Scores
    events: Tuple[Event, ...] = field(default_factory=tuple)
    evidence_refs: Tuple[str, ...] = field(default_factory=tuple)
    notes: Optional[str] = None
    provenance: Provenance = field(
        default_factory=lambda: Provenance(
            module="abraxas.mda",
            version="0.0.0",
            input_hash="",
            run_seed=0,
        )
    )

    def to_json(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "subdomain": self.subdomain,
            "status": self.status,
            "window": {"from": self.window.from_iso, "to": self.window.to_iso},
            "scores": self.scores.to_json(),
            "events": [e.to_json() for e in self.events],
            "evidence_refs": list(self.evidence_refs),
            "notes": self.notes,
            "provenance": {
                "module": self.provenance.module,
                "version": self.provenance.version,
                "input_hash": self.provenance.input_hash,
                "run_seed": self.provenance.run_seed,
            },
        }

    def stable_hash(self) -> str:
        return sha256_hex(stable_json_dumps(self.to_json()))


@dataclass(frozen=True)
class FusionEdge:
    src_id: str
    dst_id: str
    edge_type: str
    evidence_refs: Tuple[str, ...] = field(default_factory=tuple)
    weight: float = 1.0
    notes: Optional[str] = None

    def to_json(self) -> Dict[str, Any]:
        return {
            "src_id": self.src_id,
            "dst_id": self.dst_id,
            "edge_type": self.edge_type,
            "evidence_refs": list(self.evidence_refs),
            "weight": _q(self.weight),
            "notes": self.notes,
        }


@dataclass(frozen=True)
class FusionGraph:
    nodes: Dict[str, Dict[str, Any]]
    edges: Tuple[FusionEdge, ...] = field(default_factory=tuple)

    def to_json(self) -> Dict[str, Any]:
        return {
            "nodes": self.nodes,
            "edges": [e.to_json() for e in self.edges],
        }

    def stable_hash(self) -> str:
        return sha256_hex(stable_json_dumps(self.to_json()))


@dataclass(frozen=True)
class MDARunEnvelope:
    env: Literal["sandbox", "prod", "dev"]
    run_at_iso: str
    seed: int
    promotion_enabled: bool
    enabled_domains: Tuple[str, ...]
    enabled_subdomains: Tuple[str, ...]
    inputs: Dict[str, Any]

    def input_hash(self) -> str:
        return sha256_hex(
            stable_json_dumps(
                {
                    "env": self.env,
                    "run_at_iso": self.run_at_iso,
                    "seed": self.seed,
                    "promotion_enabled": self.promotion_enabled,
                    "enabled_domains": list(self.enabled_domains),
                    "enabled_subdomains": list(self.enabled_subdomains),
                    "inputs": self.inputs,
                }
            )
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            "env": self.env,
            "run_at": self.run_at_iso,
            "seed": self.seed,
            "promotion_enabled": self.promotion_enabled,
            "enabled_domains": list(self.enabled_domains),
            "enabled_subdomains": list(self.enabled_subdomains),
            "inputs": self.inputs,
            "input_hash": self.input_hash(),
        }

