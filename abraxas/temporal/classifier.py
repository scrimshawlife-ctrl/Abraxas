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
    - High eschatology → ESCHATOLOGICAL
    - High retronic + causality assertion → INVERTED
    - Moderate cyclic patterns → CYCLIC
    - Default → LINEAR
    """
    retronic_score = signature.get("retronic_score", 0.0)
    eschatological_score = signature.get("eschatological_score", 0.0)

    # Thresholds
    INVERTED_THRESHOLD = 0.15
    ESCHATOLOGICAL_THRESHOLD = 0.03

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
    Classify causality status based on retronic density and assertion strength.

    Rules:
    - High retronic density → INVERTED (causality from future to past)
    - Low retronic density → NORMAL
    """
    retronic = features.get("retronic_density", 0.0)

    # Retronic density > 0.05 indicates inverted causality
    INVERTED_THRESHOLD = 0.05

    if retronic >= INVERTED_THRESHOLD:
        return CausalityStatus.INVERTED

    return CausalityStatus.NORMAL


def classify_diagram_role(features: dict[str, float], signature: dict[str, float]) -> DiagramRole:
    """
    Classify diagram role based on authority claims.

    Rules:
    - High diagram authority → COMMANDING
    - No/low diagram authority → PASSIVE
    """
    diagram_auth = signature.get("diagram_authority_score", 0.0)

    # Threshold for commanding role
    COMMANDING_THRESHOLD = 0.1

    if diagram_auth >= COMMANDING_THRESHOLD:
        return DiagramRole.COMMANDING

    return DiagramRole.PASSIVE


def classify_sovereignty_risk(
    features: dict[str, float],
    signature: dict[str, float],
    temporal_mode: TemporalMode,
    causality_status: CausalityStatus,
) -> SovereigntyRisk:
    """
    Classify sovereignty risk based on all factors.

    Rules:
    - ESCHATOLOGICAL mode → CRITICAL (unconditional)
    - High diagram authority → HIGH
    - INVERTED temporal mode or causality → HIGH
    - High agency migration or sovereignty score → HIGH
    - Moderate assertion → MODERATE
    - Default → LOW
    """
    risk_score = signature.get("sovereignty_risk_score", 0.0)
    agency = features.get("agency_migration_density", 0.0)
    diagram_auth = signature.get("diagram_authority_score", 0.0)

    DIAGRAM_HIGH_THRESHOLD = 0.1

    # ESCHATOLOGICAL mode alone is sufficient for CRITICAL risk
    if temporal_mode == TemporalMode.ESCHATOLOGICAL:
        return SovereigntyRisk.CRITICAL

    # High diagram authority → HIGH (commands reality via diagram)
    if diagram_auth >= DIAGRAM_HIGH_THRESHOLD:
        return SovereigntyRisk.HIGH

    # INVERTED temporal mode → HIGH
    if temporal_mode == TemporalMode.INVERTED:
        return SovereigntyRisk.HIGH

    # INVERTED causality without eschatological context → HIGH
    if causality_status == CausalityStatus.INVERTED:
        return SovereigntyRisk.HIGH

    if risk_score >= 0.5 or agency >= 0.4:
        return SovereigntyRisk.HIGH

    if risk_score >= 0.3:
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

    # RTI: Retronic Time Inversion - triggered by inverted mode OR causality
    if temporal_mode == TemporalMode.INVERTED or causality_status == CausalityStatus.INVERTED:
        operators.append("RTI")

    # DTA: Diagrammatic Temporal Authority - triggered by commanding diagram role
    if diagram_role in [DiagramRole.COMMANDING, DiagramRole.PRESCRIPTIVE, DiagramRole.DETERMINATIVE]:
        operators.append("DTA")

    # HSE: High Sovereignty Escalation - triggered by eschatological mode or HIGH/CRITICAL risk
    if temporal_mode == TemporalMode.ESCHATOLOGICAL or sovereignty_risk in [SovereigntyRisk.HIGH, SovereigntyRisk.CRITICAL]:
        operators.append("HSE")

    # UCS: Unfalsifiable Cosmic Scope (eschatological closure)
    if temporal_mode == TemporalMode.ESCHATOLOGICAL and causality_status in [
        CausalityStatus.INVERTED,
        CausalityStatus.AUTHORITATIVE,
    ]:
        operators.append("UCS")

    return sorted(operators)  # Sort for determinism
