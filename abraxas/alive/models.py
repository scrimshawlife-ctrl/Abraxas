"""
ALIVE data models (Pydantic).

Mirror the TypeScript schemas from shared/alive/schema.ts
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MetricStatus(str, Enum):
    """Metric lifecycle status."""

    PROVISIONAL = "provisional"
    SHADOWED = "shadowed"
    PROMOTED = "promoted"


class InfluenceMetric(BaseModel):
    """I = Influence (social gravity ↔ network position ↔ persuasive reach)."""

    metricId: str
    metricVersion: str
    status: MetricStatus
    value: float
    confidence: float = Field(ge=0, le=1)
    timestamp: datetime


class VitalityMetric(BaseModel):
    """V = Vitality (creative momentum ↔ discourse velocity ↔ engagement coherence)."""

    metricId: str
    metricVersion: str
    status: MetricStatus
    value: float
    confidence: float = Field(ge=0, le=1)
    timestamp: datetime


class LifeLogisticsMetric(BaseModel):
    """L = Life-Logistics (lived cost ↔ material condition ↔ operational constraint)."""

    metricId: str
    metricVersion: str
    status: MetricStatus
    value: float
    confidence: float = Field(ge=0, le=1)
    timestamp: datetime


class CorpusProvenance(BaseModel):
    """Provenance record for corpus source."""

    sourceId: str
    sourceType: str
    weight: float
    timestamp: datetime


class MetricStrain(BaseModel):
    """Metric strain detection report."""

    detected: bool
    strainReport: Optional[str] = None


class CompositeScore(BaseModel):
    """Composite ALIVE score."""

    overall: float = Field(ge=0, le=1)
    influenceWeight: float
    vitalityWeight: float
    lifeLogisticsWeight: float


class ALIVEFieldSignature(BaseModel):
    """
    Canonical ALIVE field signature output.

    Same structure across all tiers; filtering happens at presentation layer.
    """

    analysisId: str
    subjectId: str
    timestamp: datetime

    # The three axes
    influence: list[InfluenceMetric]
    vitality: list[VitalityMetric]
    lifeLogistics: list[LifeLogisticsMetric]

    # Composite
    compositeScore: CompositeScore

    # Provenance
    corpusProvenance: list[CorpusProvenance]

    # Strain
    metricStrain: Optional[MetricStrain] = None


class ALIVERunInput(BaseModel):
    """Input for ALIVE analysis run."""

    subjectId: str
    tier: str  # "psychonaut" | "academic" | "enterprise"
    corpusConfig: dict
    metricConfig: Optional[dict] = None
