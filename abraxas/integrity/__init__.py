"""Integrity Layer: D/M metrics for information integrity assessment.

IMPORTANT: These are risk/likelihood estimators, NOT truth adjudication.
Provides evidence-based scores to support human judgment.
"""

from abraxas.integrity.dm_metrics import (
    ArtifactIntegrityMetrics,
    compute_artifact_integrity,
)
from abraxas.integrity.composites import (
    NarrativeManipulationMetrics,
    NetworkCampaignMetrics,
    CompositeRiskIndices,
    compute_composite_risk,
)
from abraxas.integrity.payload_taxonomy import PayloadType, classify_payload
from abraxas.integrity.propaganda_archetypes import PropagandaArchetype, PROPAGANDA_REGISTRY

__all__ = [
    "ArtifactIntegrityMetrics",
    "compute_artifact_integrity",
    "NarrativeManipulationMetrics",
    "NetworkCampaignMetrics",
    "CompositeRiskIndices",
    "compute_composite_risk",
    "PayloadType",
    "classify_payload",
    "PropagandaArchetype",
    "PROPAGANDA_REGISTRY",
]
