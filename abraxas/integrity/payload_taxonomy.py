"""Payload Taxonomy: 5 canonical types for content classification.

Types:
1. Authentic — High PPS/PCS, Low MRI
2. Contested — Mixed scores, high variance
3. Manipulated — Low PPS/PCS, High FLS/RRS
4. Coordinated — High CUS/MDS, synchronized patterns
5. Fabricated — Near-zero provenance, high MPS
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from abraxas.integrity.composites import CompositeRiskIndices


class PayloadType(str, Enum):
    """Canonical payload types for content classification."""

    AUTHENTIC = "Authentic"
    CONTESTED = "Contested"
    MANIPULATED = "Manipulated"
    COORDINATED = "Coordinated"
    FABRICATED = "Fabricated"


@dataclass(frozen=True)
class PayloadClassification:
    """Payload classification with confidence and reasoning."""

    payload_type: PayloadType
    confidence_score: float  # [0,1]
    reasoning: str


def classify_payload(risk_indices: CompositeRiskIndices) -> PayloadClassification:
    """
    Classify payload type based on composite risk indices.

    Classification rules (deterministic thresholds):
    - Authentic: IRI < 30 AND MRI < 30
    - Fabricated: IRI > 70 AND MRI > 70
    - Coordinated: MRI > 60 AND (CUS > 0.7 OR MDS > 0.7)
    - Manipulated: IRI < 50 AND MRI > 50
    - Contested: All others (mixed/uncertain signals)

    Args:
        risk_indices: CompositeRiskIndices

    Returns:
        PayloadClassification
    """
    iri = risk_indices.iri
    mri = risk_indices.mri
    cus = risk_indices.network_campaign.cus
    mds = risk_indices.network_campaign.mds

    # Rule 1: Authentic
    if iri < 30 and mri < 30:
        confidence = 1.0 - max(iri, mri) / 30.0
        return PayloadClassification(
            payload_type=PayloadType.AUTHENTIC,
            confidence_score=confidence,
            reasoning=f"Low integrity risk (IRI={iri:.1f}) and manipulation risk (MRI={mri:.1f})",
        )

    # Rule 2: Fabricated
    if iri > 70 and mri > 70:
        confidence = min(iri, mri) / 100.0
        return PayloadClassification(
            payload_type=PayloadType.FABRICATED,
            confidence_score=confidence,
            reasoning=f"High integrity risk (IRI={iri:.1f}) and manipulation risk (MRI={mri:.1f})",
        )

    # Rule 3: Coordinated
    if mri > 60 and (cus > 0.7 or mds > 0.7):
        confidence = mri / 100.0
        return PayloadClassification(
            payload_type=PayloadType.COORDINATED,
            confidence_score=confidence,
            reasoning=f"High manipulation (MRI={mri:.1f}) with coordination signals (CUS={cus:.2f}, MDS={mds:.2f})",
        )

    # Rule 4: Manipulated
    if iri < 50 and mri > 50:
        confidence = mri / 100.0
        return PayloadClassification(
            payload_type=PayloadType.MANIPULATED,
            confidence_score=confidence,
            reasoning=f"Moderate integrity (IRI={iri:.1f}) but high manipulation (MRI={mri:.1f})",
        )

    # Rule 5: Contested (default)
    confidence = 0.5
    return PayloadClassification(
        payload_type=PayloadType.CONTESTED,
        confidence_score=confidence,
        reasoning=f"Mixed signals: IRI={iri:.1f}, MRI={mri:.1f}",
    )
