"""D/M Composites: Narrative Manipulation, Network Metrics, and Risk Indices.

Narrative Manipulation Metrics:
- FLS (Framing Leverage Score)
- EIL (Emotional Intensity Level)
- OCS (Omission/Contextualization Score)
- RRS (Repetition/Redundancy Score)
- MPS (Misattribution Probability Score)
- CIS (Coordination Indicator Score)

Network/Campaign Metrics:
- CUS (Coordination/Uniformity Score)
- SVS (Source Velocity Score)
- BAS (Bursting/Amplification Score)
- MDS (Multi-Domain Spread Score)

Composite Risk Indices:
- IRI (Integrity Risk Index): [0,100]
- MRI (Manipulation Risk Index): [0,100]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from abraxas.integrity.dm_metrics import (
    ArtifactIntegrityMetrics,
    ConfidenceLevel,
    compute_artifact_integrity,
)


@dataclass(frozen=True)
class NarrativeManipulationMetrics:
    """Narrative manipulation metric suite."""

    fls: float  # Framing Leverage Score [0,1]
    eil: float  # Emotional Intensity Level [0,1]
    ocs: float  # Omission/Contextualization Score [0,1]
    rrs: float  # Repetition/Redundancy Score [0,1]
    mps: float  # Misattribution Probability Score [0,1]
    cis: float  # Coordination Indicator Score [0,1]
    confidence: ConfidenceLevel


@dataclass(frozen=True)
class NetworkCampaignMetrics:
    """Network and campaign metric suite."""

    cus: float  # Coordination/Uniformity Score [0,1]
    svs: float  # Source Velocity Score [0,1]
    bas: float  # Bursting/Amplification Score [0,1]
    mds: float  # Multi-Domain Spread Score [0,1]
    confidence: ConfidenceLevel


@dataclass(frozen=True)
class CompositeRiskIndices:
    """Composite risk indices combining all metrics."""

    iri: float  # Integrity Risk Index [0,100]
    mri: float  # Manipulation Risk Index [0,100]
    confidence: ConfidenceLevel
    artifact_integrity: ArtifactIntegrityMetrics
    narrative_manipulation: NarrativeManipulationMetrics
    network_campaign: NetworkCampaignMetrics


def compute_narrative_manipulation(
    framing_indicators: int = 0,
    total_framing_checked: int = 5,
    emotional_word_count: int = 0,
    total_word_count: int = 1,
    omission_flags: int = 0,
    total_omission_checks: int = 3,
    repetition_count: int = 0,
    unique_message_count: int = 1,
    misattribution_indicators: int = 0,
    total_attribution_checks: int = 3,
    coordination_signals: int = 0,
    total_coordination_checks: int = 4,
) -> NarrativeManipulationMetrics:
    """
    Compute narrative manipulation metrics.

    Args:
        framing_indicators: Count of framing leverage indicators detected
        total_framing_checked: Total framing indicators checked
        emotional_word_count: Count of emotionally loaded words
        total_word_count: Total word count
        omission_flags: Count of omission/selective presentation flags
        total_omission_checks: Total omission checks performed
        repetition_count: Count of repeated messages/phrases
        unique_message_count: Count of unique messages
        misattribution_indicators: Count of misattribution signals
        total_attribution_checks: Total attribution checks
        coordination_signals: Count of coordination signals
        total_coordination_checks: Total coordination checks

    Returns:
        NarrativeManipulationMetrics with confidence
    """
    # FLS: Framing Leverage Score
    fls = (
        framing_indicators / total_framing_checked if total_framing_checked > 0 else 0.0
    )

    # EIL: Emotional Intensity Level
    eil = (
        emotional_word_count / total_word_count if total_word_count > 0 else 0.0
    )
    eil = min(eil, 1.0)  # Clamp to [0,1]

    # OCS: Omission/Contextualization Score
    ocs = (
        omission_flags / total_omission_checks if total_omission_checks > 0 else 0.0
    )

    # RRS: Repetition/Redundancy Score
    if unique_message_count > 0:
        redundancy_ratio = repetition_count / unique_message_count
        rrs = min(redundancy_ratio / 10.0, 1.0)  # Normalize: 10x = max
    else:
        rrs = 0.0

    # MPS: Misattribution Probability Score
    mps = (
        misattribution_indicators / total_attribution_checks
        if total_attribution_checks > 0
        else 0.0
    )

    # CIS: Coordination Indicator Score
    cis = (
        coordination_signals / total_coordination_checks
        if total_coordination_checks > 0
        else 0.0
    )

    # Compute confidence based on completeness
    all_checks = [
        total_framing_checked > 0,
        total_word_count > 10,  # Meaningful word count
        total_omission_checks > 0,
        unique_message_count > 0,
        total_attribution_checks > 0,
        total_coordination_checks > 0,
    ]
    completeness = sum(all_checks) / len(all_checks)

    if completeness < 0.4:
        confidence = ConfidenceLevel.LOW
    elif completeness < 0.8:
        confidence = ConfidenceLevel.MED
    else:
        confidence = ConfidenceLevel.HIGH

    return NarrativeManipulationMetrics(
        fls=fls,
        eil=eil,
        ocs=ocs,
        rrs=rrs,
        mps=mps,
        cis=cis,
        confidence=confidence,
    )


def compute_network_campaign(
    uniformity_score: float = 0.0,
    propagation_rate: float = 0.0,
    max_propagation_rate: float = 100.0,
    burst_amplitude: float = 0.0,
    max_burst_amplitude: float = 1000.0,
    domain_count: int = 1,
    max_domains: int = 10,
) -> NetworkCampaignMetrics:
    """
    Compute network and campaign metrics.

    Args:
        uniformity_score: Content uniformity score [0,1]
        propagation_rate: Propagation rate (events/hour)
        max_propagation_rate: Maximum expected propagation rate
        burst_amplitude: Burst amplitude (peak/baseline ratio)
        max_burst_amplitude: Maximum expected burst amplitude
        domain_count: Number of domains/platforms
        max_domains: Maximum expected domains

    Returns:
        NetworkCampaignMetrics with confidence
    """
    # CUS: Coordination/Uniformity Score
    cus = uniformity_score

    # SVS: Source Velocity Score
    svs = min(propagation_rate / max_propagation_rate, 1.0)

    # BAS: Bursting/Amplification Score
    bas = min(burst_amplitude / max_burst_amplitude, 1.0)

    # MDS: Multi-Domain Spread Score
    mds = min(domain_count / max_domains, 1.0)

    # Compute confidence
    all_checks = [
        uniformity_score >= 0,
        propagation_rate >= 0,
        burst_amplitude >= 0,
        domain_count > 0,
    ]
    completeness = sum(all_checks) / len(all_checks)

    if completeness < 0.5:
        confidence = ConfidenceLevel.LOW
    elif completeness < 0.8:
        confidence = ConfidenceLevel.MED
    else:
        confidence = ConfidenceLevel.HIGH

    return NetworkCampaignMetrics(
        cus=cus,
        svs=svs,
        bas=bas,
        mds=mds,
        confidence=confidence,
    )


def compute_composite_risk(
    artifact_integrity: ArtifactIntegrityMetrics,
    narrative_manipulation: NarrativeManipulationMetrics,
    network_campaign: NetworkCampaignMetrics,
) -> CompositeRiskIndices:
    """
    Compute composite risk indices from component metrics.

    IRI (Integrity Risk Index):
      100 * (1 - mean(PPS, PCS, MMS, SLS, EIS))

    MRI (Manipulation Risk Index):
      100 * weighted_mean(FLS, EIL, OCS, RRS, MPS, CIS, CUS, SVS, BAS, MDS)

    Args:
        artifact_integrity: Artifact integrity metrics
        narrative_manipulation: Narrative manipulation metrics
        network_campaign: Network campaign metrics

    Returns:
        CompositeRiskIndices with IRI and MRI
    """
    # IRI: Integrity Risk Index
    integrity_mean = (
        artifact_integrity.pps
        + artifact_integrity.pcs
        + artifact_integrity.mms
        + artifact_integrity.sls
        + artifact_integrity.eis
    ) / 5.0
    iri = 100.0 * (1.0 - integrity_mean)

    # MRI: Manipulation Risk Index
    # Weighted average of all manipulation indicators
    # Weights: narrative metrics = 0.6, network metrics = 0.4
    narrative_mean = (
        narrative_manipulation.fls
        + narrative_manipulation.eil
        + narrative_manipulation.ocs
        + narrative_manipulation.rrs
        + narrative_manipulation.mps
        + narrative_manipulation.cis
    ) / 6.0

    network_mean = (
        network_campaign.cus
        + network_campaign.svs
        + network_campaign.bas
        + network_campaign.mds
    ) / 4.0

    mri = 100.0 * (0.6 * narrative_mean + 0.4 * network_mean)

    # Confidence: minimum of component confidences
    confidence_levels = [
        artifact_integrity.confidence,
        narrative_manipulation.confidence,
        network_campaign.confidence,
    ]
    # Convert to numeric for comparison
    confidence_map = {ConfidenceLevel.LOW: 0, ConfidenceLevel.MED: 1, ConfidenceLevel.HIGH: 2}
    min_confidence_val = min(confidence_map[c] for c in confidence_levels)
    confidence = [ConfidenceLevel.LOW, ConfidenceLevel.MED, ConfidenceLevel.HIGH][
        min_confidence_val
    ]

    return CompositeRiskIndices(
        iri=iri,
        mri=mri,
        confidence=confidence,
        artifact_integrity=artifact_integrity,
        narrative_manipulation=narrative_manipulation,
        network_campaign=network_campaign,
    )
