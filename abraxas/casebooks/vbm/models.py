"""Data models for VBM casebook."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from abraxas.core.provenance import ProvenanceBundle


class VBMPhase(str, Enum):
    """
    Six-phase escalation model for VBM-class rhetoric.

    Each phase represents a stage in the escalation from mathematical pattern
    observation to unfalsifiable metaphysical claims.
    """

    MATH_PATTERN = "math_pattern"
    REPRESENTATION_REDUCTION = "representation_reduction"
    CROSS_DOMAIN_ANALOGY = "cross_domain_analogy"
    PHYSICS_LEXICON_INJECTION = "physics_lexicon_injection"
    CONSCIOUSNESS_ATTRIBUTION = "consciousness_attribution"
    UNFALSIFIABLE_CLOSURE = "unfalsifiable_closure"


class VBMEpisode(BaseModel):
    """A single episode in the VBM series."""

    episode_id: str = Field(..., description="Episode identifier (e.g., 'vbm_01')")
    title: str = Field(..., description="Episode title")
    summary_text: str = Field(..., description="Full episode summary")
    extracted_claims: list[str] = Field(
        default_factory=list,
        description="Short bullet claims derived deterministically from summary",
    )
    extracted_tokens: dict[str, int] = Field(
        default_factory=dict,
        description="Counts of trigger lexemes (e.g., 'tachyon', 'torus', etc.)",
    )
    provenance: ProvenanceBundle = Field(..., description="Provenance record")

    class Config:
        use_enum_values = True


class VBMCasebook(BaseModel):
    """Complete VBM casebook with all episodes and metadata."""

    casebook_id: str = Field(default="VBM_SERIES", description="Casebook identifier")
    episodes: list[VBMEpisode] = Field(default_factory=list, description="All episodes")
    phase_curve: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Episode phase classifications (episode_id -> phase + confidence)",
    )
    trigger_lexicon: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Lexeme groups per phase",
    )
    provenance: ProvenanceBundle = Field(..., description="Casebook provenance")

    class Config:
        use_enum_values = True


class VBMDriftScore(BaseModel):
    """Drift score for text evaluated against VBM casebook."""

    score: float = Field(..., ge=0.0, le=1.0, description="Overall drift score [0, 1]")
    phase: VBMPhase = Field(..., description="Detected VBM phase")
    phase_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in phase classification"
    )
    lattice_hits: list[str] = Field(
        default_factory=list,
        description="Operator lattice IDs hit (MKB/PAP/DOE/SCA/PAM/UCS)",
    )
    evidence: dict[str, Any] = Field(
        default_factory=dict,
        description="Token hits, phrases, feature values",
    )
    provenance: ProvenanceBundle = Field(..., description="Scoring provenance")

    class Config:
        use_enum_values = True
