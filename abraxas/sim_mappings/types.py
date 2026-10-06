"""SML Types: Typed dataclasses for simulation parameter mapping.

Defines:
- PaperRef: Academic paper reference
- ModelFamily: Canonical model family taxonomy
- ModelParam: Individual model parameter with provenance
- KnobVector: Mapped Abraxas operational knobs (MRI/IRI/τ)
- MappingResult: Complete mapping from paper to knobs
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PaperRef:
    """Academic paper reference with metadata."""

    paper_id: str  # e.g. "PMC12281847", "DOI:10.1234/example"
    title: str
    url: str
    year: Optional[int] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "url": self.url,
            "year": self.year,
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> PaperRef:
        """Create from dict."""
        return PaperRef(
            paper_id=data["paper_id"],
            title=data["title"],
            url=data["url"],
            year=data.get("year"),
            notes=data.get("notes"),
        )


class ModelFamily(str, Enum):
    """Canonical model family taxonomy."""

    DIFFUSION_SIR = "DIFFUSION_SIR"  # SIR/SEIR compartment models
    OPINION_DYNAMICS = "OPINION_DYNAMICS"  # Voter, DeGroot, bounded confidence
    ABM_MISINFO = "ABM_MISINFO"  # Agent-based misinformation models
    NETWORK_CASCADES = "NETWORK_CASCADES"  # Threshold/cascade models
    GAME_THEORETIC = "GAME_THEORETIC"  # Evolutionary game theory, inspection games


@dataclass(frozen=True)
class ModelParam:
    """Individual model parameter with metadata and provenance."""

    name: str  # e.g. "beta", "gamma", "influence_weight"
    symbol: Optional[str] = None  # e.g. "β", "γ", "w_ij"
    description: str = ""
    value: Optional[float] = None  # None if paper-specific / variable
    units: Optional[str] = None  # e.g. "per day", "dimensionless"
    role: Optional[str] = None  # Free-text role from paper
    provenance: Dict[str, Any] = field(default_factory=dict)  # run_id/hash/source

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "name": self.name,
            "symbol": self.symbol,
            "description": self.description,
            "value": self.value,
            "units": self.units,
            "role": self.role,
            "provenance": self.provenance,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> ModelParam:
        """Create from dict."""
        return ModelParam(
            name=data["name"],
            symbol=data.get("symbol"),
            description=data.get("description", ""),
            value=data.get("value"),
            units=data.get("units"),
            role=data.get("role"),
            provenance=data.get("provenance", {}),
        )


@dataclass(frozen=True)
class KnobVector:
    """Mapped Abraxas operational knobs (normalized to [0,1] or time-like scalars).

    Fields:
    - mri: Manipulation Risk Index component [0,1]
    - iri: Integrity Risk Index component [0,1]
    - tau_latency: Temporal latency/delay component (normalized or time-like)
    - tau_memory: Temporal memory/persistence component [0,1]
    - confidence: Mapping confidence (LOW/MED/HIGH)
    - explanation: Human-readable explanation of mapping
    """

    mri: float  # [0,1] normalized
    iri: float  # [0,1] normalized
    tau_latency: float  # Normalized or time-like scalar
    tau_memory: float  # [0,1] normalized
    confidence: str  # LOW/MED/HIGH
    explanation: str  # Deterministic derived text

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "mri": self.mri,
            "iri": self.iri,
            "tau_latency": self.tau_latency,
            "tau_memory": self.tau_memory,
            "confidence": self.confidence,
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class MappingResult:
    """Complete mapping result from academic paper to Abraxas knobs."""

    paper: PaperRef
    family: ModelFamily
    input_params: List[ModelParam]
    mapped: KnobVector
    mapped_components: Dict[str, List[str]] = field(default_factory=dict)
    notes: str = ""

    @property
    def params(self) -> List[ModelParam]:
        """Backwards-compatible alias for ``input_params``."""
        return self.input_params

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "paper": self.paper.to_dict(),
            "family": self.family.value,
            "input_params": [p.to_dict() for p in self.input_params],
            "mapped": self.mapped.to_dict(),
            "mapped_components": self.mapped_components,
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> MappingResult:
        """Create from dict."""
        raw_params = data.get("input_params", data.get("params", []))
        return MappingResult(
            paper=PaperRef.from_dict(data["paper"]),
            family=ModelFamily(data["family"]),
            input_params=[ModelParam.from_dict(p) for p in raw_params],
            mapped=KnobVector(**data["mapped"]),
            mapped_components=data.get("mapped_components", {}),
            notes=data.get("notes", ""),
        )
