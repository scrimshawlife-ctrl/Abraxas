"""Data models for Temporal Drift Detection (TDD)."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from abraxas.core.provenance import ProvenanceBundle


class TemporalMode(str, Enum):
    """Classification of temporal framing in text."""

    LINEAR = "linear"  # Standard past->present->future
    CYCLIC = "cyclic"  # Cyclical/eternal return patterns
    INVERTED = "inverted"  # Causality flows from future to past
    ESCHATOLOGICAL = "eschatological"  # End-times/destiny/apocalyptic framing


class CausalityStatus(str, Enum):
    """Status of causality claims in text."""

    DESCRIPTIVE = "descriptive"  # Describing observed patterns
    METAPHORICAL = "metaphorical"  # Using metaphorical language
    ASSERTED = "asserted"  # Asserting causal relationships
    AUTHORITATIVE = "authoritative"  # Claiming definitive causal knowledge


class DiagramRole(str, Enum):
    """Role of diagrams/symbols in establishing authority."""

    ILLUSTRATIVE = "illustrative"  # Diagrams illustrate concepts
    NAVIGATIONAL = "navigational"  # Diagrams help navigate ideas
    PRESCRIPTIVE = "prescriptive"  # Diagrams prescribe actions/interpretations
    DETERMINATIVE = "determinative"  # Diagrams determine reality/truth


class SovereigntyRisk(str, Enum):
    """Risk level to user epistemic sovereignty."""

    LOW = "low"  # Minimal risk to independent judgment
    MODERATE = "moderate"  # Some pressure on judgment
    HIGH = "high"  # Significant pressure, de-escalation recommended
    CRITICAL = "critical"  # Severe risk, strong de-escalation required


class TemporalDriftResult(BaseModel):
    """Result from temporal drift analysis."""

    temporal_mode: TemporalMode = Field(..., description="Detected temporal framing")
    causality_status: CausalityStatus = Field(..., description="Causality claim status")
    diagram_role: DiagramRole = Field(..., description="Role of diagrams/symbols")
    sovereignty_risk: SovereigntyRisk = Field(
        ..., description="Risk to user epistemic sovereignty"
    )
    operator_hits: list[str] = Field(
        default_factory=list,
        description="TDD operator IDs hit (RTI, DTA, HSE, UCS)",
    )
    evidence: dict[str, Any] = Field(
        default_factory=dict, description="Evidence for classification"
    )
    provenance: ProvenanceBundle = Field(..., description="Analysis provenance")

    class Config:
        use_enum_values = True
