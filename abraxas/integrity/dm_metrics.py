"""D/M Metrics: Artifact Integrity Metrics.

Metrics:
- PPS (Provenance Presence Score): [0,1], metadata completeness
- PCS (Provenance Chain Score): [0,1], traceable source chain
- MMS (Mutation Marker Score): [0,1], edit history present
- SLS (Source Locality Score): [0,1], cross-platform coherence
- EIS (Evidence Integrity Score): [0,1], supporting data quality

All metrics are deterministic and based on explicit inputs.
Confidence bands: LOW/MED/HIGH based on evidence completeness.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class ConfidenceLevel(str, Enum):
    """Confidence band for metric assessment."""

    LOW = "LOW"
    MED = "MED"
    HIGH = "HIGH"


@dataclass(frozen=True)
class ArtifactIntegrityMetrics:
    """Complete artifact integrity metric suite."""

    pps: float  # Provenance Presence Score [0,1]
    pcs: float  # Provenance Chain Score [0,1]
    mms: float  # Mutation Marker Score [0,1]
    sls: float  # Source Locality Score [0,1]
    eis: float  # Evidence Integrity Score [0,1]
    confidence: ConfidenceLevel
    fields_present: int
    fields_total: int


def compute_artifact_integrity(
    has_timestamp: bool = False,
    has_source_id: bool = False,
    has_author: bool = False,
    has_provenance_hash: bool = False,
    source_chain_length: int = 0,
    has_edit_history: bool = False,
    edit_count: int = 0,
    cross_platform_matches: int = 0,
    total_platforms_checked: int = 1,
    has_supporting_evidence: bool = False,
    evidence_quality_score: float = 0.0,
) -> ArtifactIntegrityMetrics:
    """
    Compute artifact integrity metrics from explicit inputs.

    Args:
        has_timestamp: Timestamp present
        has_source_id: Source identifier present
        has_author: Author/creator attribution present
        has_provenance_hash: Provenance hash present
        source_chain_length: Length of traceable source chain
        has_edit_history: Edit history present
        edit_count: Number of edits recorded
        cross_platform_matches: Number of platforms with matching content
        total_platforms_checked: Total platforms checked
        has_supporting_evidence: Supporting evidence present
        evidence_quality_score: Quality score [0,1] for supporting evidence

    Returns:
        ArtifactIntegrityMetrics with confidence band
    """
    # PPS: Provenance Presence Score
    pps_components = [
        has_timestamp,
        has_source_id,
        has_author,
        has_provenance_hash,
    ]
    pps = sum(pps_components) / len(pps_components)

    # PCS: Provenance Chain Score
    # Longer chain = higher score (clamped at 5)
    pcs = min(source_chain_length / 5.0, 1.0)

    # MMS: Mutation Marker Score
    if has_edit_history:
        # Score based on edit count (0 edits = 1.0, many edits = lower)
        # Heuristic: 0-2 edits = high integrity, 3-5 = medium, 6+ = low
        if edit_count <= 2:
            mms = 1.0
        elif edit_count <= 5:
            mms = 0.6
        else:
            mms = 0.3
    else:
        mms = 0.5  # No history = medium score

    # SLS: Source Locality Score
    # Cross-platform coherence
    if total_platforms_checked > 0:
        sls = cross_platform_matches / total_platforms_checked
    else:
        sls = 0.0

    # EIS: Evidence Integrity Score
    if has_supporting_evidence:
        eis = evidence_quality_score
    else:
        eis = 0.0

    # Count fields present
    all_fields = [
        has_timestamp,
        has_source_id,
        has_author,
        has_provenance_hash,
        source_chain_length > 0,
        has_edit_history,
        cross_platform_matches > 0,
        has_supporting_evidence,
    ]
    fields_present = sum(all_fields)
    fields_total = len(all_fields)

    # Compute confidence
    completeness = fields_present / fields_total
    if completeness < 0.4:
        confidence = ConfidenceLevel.LOW
    elif completeness < 0.8:
        confidence = ConfidenceLevel.MED
    else:
        confidence = ConfidenceLevel.HIGH

    return ArtifactIntegrityMetrics(
        pps=pps,
        pcs=pcs,
        mms=mms,
        sls=sls,
        eis=eis,
        confidence=confidence,
        fields_present=fields_present,
        fields_total=fields_total,
    )
