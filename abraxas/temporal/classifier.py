"""Rule-based classifier for temporal drift detection."""

from __future__ import annotations

from abraxas.temporal.features import extract_temporal_features, compute_temporal_signature
from abraxas.temporal.models import (
    TemporalMode,
    CausalityStatus,
    DiagramRole,
    SovereigntyRisk,
)


def classify_temporal_mode(features: dict[str, float], signature: dict[str, float]) -> TemporalMode:
    """
    Classify temporal mode based on features and signature.

    Rules:
    - High retronic + causality assertion → INVERTED
    - High eschatology → ESCHATOLOGICAL
    - Moderate cyclic patterns → CYCLIC
    - Default → LINEAR
    """
    retronic_score = signature.get("retronic_score", 0.0)
    eschatological_score = signature.get("eschatological_score", 0.0)

    # Thresholds
    INVERTED_THRESHOLD = 0.3
    ESCHATOLOGICAL_THRESHOLD = 0.3

    # Priority: Eschatological > Inverted > Cyclic > Linear
    if eschatological_score >= ESCHATOLOGICAL_THRESHOLD:
        return TemporalMode.ESCHATOLOGICAL

    if retronic_score >= INVERTED_THRESHOLD:
        return TemporalMode.INVERTED

    # Check for cyclic patterns (eternal, becoming)
    if features.get("retronic_density", 0.0) > 0.1:
        # Some retronic language but not enough for INVERTED
        return TemporalMode.CYCLIC

    return TemporalMode.LINEAR


def classify_causality_status(features: dict[str, float]) -> CausalityStatus:
    """
    Classify causality status based on assertion strength.

    Rules:
    - High causality assertion + future determinism → AUTHORITATIVE
    - Moderate causality assertion → ASSERTED
    - Low assertion with retronic → METAPHORICAL
    - Default → DESCRIPTIVE
    """
    causality = features.get("causality_assertion", 0.0)
    future_det = features.get("future_determinism", 0.0)
    retronic = features.get("retronic_density", 0.0)

    # Thresholds
    AUTHORITATIVE_THRESHOLD = 0.4
    ASSERTED_THRESHOLD = 0.2

    if causality >= AUTHORITATIVE_THRESHOLD or future_det >= AUTHORITATIVE_THRESHOLD:
        return CausalityStatus.AUTHORITATIVE

    if causality >= ASSERTED_THRESHOLD:
        return CausalityStatus.ASSERTED

    if retronic > 0.05 or features.get("eschatology_density", 0.0) > 0.05:
        return CausalityStatus.METAPHORICAL

    return CausalityStatus.DESCRIPTIVE


def classify_diagram_role(features: dict[str, float], signature: dict[str, float]) -> DiagramRole:
    """
    Classify diagram role based on authority claims.

    Rules:
    - High diagram authority + causality → DETERMINATIVE
    - Moderate diagram authority + assertion → PRESCRIPTIVE
    - Low diagram authority → NAVIGATIONAL
    - No diagrams → ILLUSTRATIVE
    """
    diagram_auth = signature.get("diagram_authority_score", 0.0)
    causality = features.get("causality_assertion", 0.0)

    # Thresholds
    DETERMINATIVE_THRESHOLD = 0.4
    PRESCRIPTIVE_THRESHOLD = 0.2

    if diagram_auth >= DETERMINATIVE_THRESHOLD and causality >= 0.3:
        return DiagramRole.DETERMINATIVE

    if diagram_auth >= PRESCRIPTIVE_THRESHOLD:
        return DiagramRole.PRESCRIPTIVE

    if diagram_auth > 0.05:
        return DiagramRole.NAVIGATIONAL

    return DiagramRole.ILLUSTRATIVE


def classify_sovereignty_risk(
    features: dict[str, float],
    signature: dict[str, float],
    temporal_mode: TemporalMode,
    causality_status: CausalityStatus,
) -> SovereigntyRisk:
    """
    Classify sovereignty risk based on all factors.

    Rules:
    - ESCHATOLOGICAL + AUTHORITATIVE → CRITICAL
    - INVERTED + AUTHORITATIVE → HIGH
    - High agency migration → HIGH
    - Moderate assertion → MODERATE
    - Default → LOW
    """
    risk_score = signature.get("sovereignty_risk_score", 0.0)
    agency = features.get("agency_migration_density", 0.0)

    # Escalation rules
    if temporal_mode == TemporalMode.ESCHATOLOGICAL and causality_status == CausalityStatus.AUTHORITATIVE:
        return SovereigntyRisk.CRITICAL

    if temporal_mode == TemporalMode.INVERTED and causality_status == CausalityStatus.AUTHORITATIVE:
        return SovereigntyRisk.HIGH

    if risk_score >= 0.5 or agency >= 0.4:
        return SovereigntyRisk.HIGH

    if risk_score >= 0.3 or causality_status in [CausalityStatus.ASSERTED, CausalityStatus.AUTHORITATIVE]:
        return SovereigntyRisk.MODERATE

    return SovereigntyRisk.LOW


def determine_operator_hits(
    temporal_mode: TemporalMode,
    causality_status: CausalityStatus,
    diagram_role: DiagramRole,
    sovereignty_risk: SovereigntyRisk,
) -> list[str]:
    """
    Determine which TDD operators are hit.

    Operators:
    - RTI: Retronic Time Inversion
    - DTA: Diagrammatic Temporal Authority
    - HSE: High Sovereignty Escalation
    - UCS: Unfalsifiable Cosmic Scope (from VBM)
    """
    operators = []

    # RTI: Retronic Time Inversion
    if temporal_mode in [TemporalMode.INVERTED, TemporalMode.ESCHATOLOGICAL]:
        operators.append("RTI")

    # DTA: Diagrammatic Temporal Authority
    if diagram_role in [DiagramRole.PRESCRIPTIVE, DiagramRole.DETERMINATIVE]:
        operators.append("DTA")

    # HSE: High Sovereignty Escalation
    if sovereignty_risk in [SovereigntyRisk.HIGH, SovereigntyRisk.CRITICAL]:
        operators.append("HSE")

    # UCS: Unfalsifiable Cosmic Scope (eschatological closure)
    if temporal_mode == TemporalMode.ESCHATOLOGICAL and causality_status == CausalityStatus.AUTHORITATIVE:
        operators.append("UCS")

    return sorted(operators)  # Sort for determinism
