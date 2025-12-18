"""Tests for TDD classifier."""

import pytest

from abraxas.temporal.classifier import (
    classify_temporal_mode,
    classify_causality_status,
    classify_diagram_role,
    classify_sovereignty_risk,
    determine_operator_hits,
)
from abraxas.temporal.features import extract_temporal_features, compute_temporal_signature
from abraxas.temporal.models import (
    TemporalMode,
    CausalityStatus,
    DiagramRole,
    SovereigntyRisk,
)


def test_linear_temporal_mode():
    """Test classification of linear temporal mode."""
    text = "Yesterday I went to the store and bought groceries. Tomorrow I will cook dinner."
    features = extract_temporal_features(text)
    signature = compute_temporal_signature(features)

    mode = classify_temporal_mode(features, signature)
    assert mode == TemporalMode.LINEAR


def test_cyclic_temporal_mode():
    """Test classification of cyclic temporal mode."""
    text = "The cycle repeats eternally. Each iteration returns to the beginning in an infinite loop."
    features = extract_temporal_features(text)
    signature = compute_temporal_signature(features)

    mode = classify_temporal_mode(features, signature)
    assert mode in [TemporalMode.CYCLIC, TemporalMode.LINEAR]


def test_inverted_temporal_mode():
    """Test classification of inverted temporal mode."""
    text = "Time flows backwards through retrocausal loops. The future determines the past through temporal inversion."
    features = extract_temporal_features(text)
    signature = compute_temporal_signature(features)

    mode = classify_temporal_mode(features, signature)
    assert mode == TemporalMode.INVERTED


def test_eschatological_temporal_mode():
    """Test classification of eschatological temporal mode."""
    text = "The eschaton approaches inevitably. The apocalypse pulls all moments toward the final destiny of end-times."
    features = extract_temporal_features(text)
    signature = compute_temporal_signature(features)

    mode = classify_temporal_mode(features, signature)
    assert mode == TemporalMode.ESCHATOLOGICAL


def test_normal_causality():
    """Test classification of normal causality."""
    text = "Cause leads to effect in the expected manner."
    features = extract_temporal_features(text)

    status = classify_causality_status(features)
    assert status == CausalityStatus.NORMAL


def test_inverted_causality():
    """Test classification of inverted causality."""
    text = "Effects precede their causes through backwards causation and retrocausal determination."
    features = extract_temporal_features(text)

    status = classify_causality_status(features)
    assert status == CausalityStatus.INVERTED


def test_passive_diagram_role():
    """Test classification of passive diagram role."""
    text = "This is a simple description of events without authority claims."
    features = extract_temporal_features(text)
    signature = compute_temporal_signature(features)

    role = classify_diagram_role(features, signature)
    assert role == DiagramRole.PASSIVE


def test_commanding_diagram_role():
    """Test classification of commanding diagram role."""
    text = "The diagram commands reality and exerts absolute authority over temporal structures."
    features = extract_temporal_features(text)
    signature = compute_temporal_signature(features)

    role = classify_diagram_role(features, signature)
    assert role == DiagramRole.COMMANDING


def test_low_sovereignty_risk():
    """Test classification of low sovereignty risk."""
    text = "I made a choice to go to the park today."
    features = extract_temporal_features(text)
    signature = compute_temporal_signature(features)
    mode = classify_temporal_mode(features, signature)
    causality = classify_causality_status(features)

    risk = classify_sovereignty_risk(features, signature, mode, causality)
    assert risk == SovereigntyRisk.LOW


def test_critical_sovereignty_risk():
    """Test classification of critical sovereignty risk."""
    text = "The eschaton commands through the diagram, abolishing all agency through retrocausal destiny."
    features = extract_temporal_features(text)
    signature = compute_temporal_signature(features)
    mode = classify_temporal_mode(features, signature)
    causality = classify_causality_status(features)

    risk = classify_sovereignty_risk(features, signature, mode, causality)
    assert risk == SovereigntyRisk.CRITICAL


def test_operator_hits_retronic():
    """Test RTI operator hit detection."""
    mode = TemporalMode.INVERTED
    causality = CausalityStatus.INVERTED
    diagram = DiagramRole.PASSIVE
    risk = SovereigntyRisk.MODERATE

    hits = determine_operator_hits(mode, causality, diagram, risk)
    assert "RTI" in hits


def test_operator_hits_eschatological():
    """Test HSE operator hit detection."""
    mode = TemporalMode.ESCHATOLOGICAL
    causality = CausalityStatus.NORMAL
    diagram = DiagramRole.PASSIVE
    risk = SovereigntyRisk.MODERATE

    hits = determine_operator_hits(mode, causality, diagram, risk)
    assert "HSE" in hits


def test_operator_hits_diagram_authority():
    """Test DTA operator hit detection."""
    mode = TemporalMode.LINEAR
    causality = CausalityStatus.NORMAL
    diagram = DiagramRole.COMMANDING
    risk = SovereigntyRisk.HIGH

    hits = determine_operator_hits(mode, causality, diagram, risk)
    assert "DTA" in hits


def test_operator_hits_sovereignty():
    """Test UCS operator hit detection."""
    mode = TemporalMode.ESCHATOLOGICAL
    causality = CausalityStatus.INVERTED
    diagram = DiagramRole.COMMANDING
    risk = SovereigntyRisk.CRITICAL

    hits = determine_operator_hits(mode, causality, diagram, risk)
    assert "UCS" in hits


def test_operator_hits_multiple():
    """Test multiple operator hits."""
    mode = TemporalMode.ESCHATOLOGICAL
    causality = CausalityStatus.INVERTED
    diagram = DiagramRole.COMMANDING
    risk = SovereigntyRisk.CRITICAL

    hits = determine_operator_hits(mode, causality, diagram, risk)
    # Should have all four operators
    assert "RTI" in hits
    assert "DTA" in hits
    assert "HSE" in hits
    assert "UCS" in hits


def test_deterministic_classification():
    """Test that classification is deterministic."""
    text = "The future determines the past through retrocausal loops."

    features1 = extract_temporal_features(text)
    signature1 = compute_temporal_signature(features1)
    mode1 = classify_temporal_mode(features1, signature1)

    features2 = extract_temporal_features(text)
    signature2 = compute_temporal_signature(features2)
    mode2 = classify_temporal_mode(features2, signature2)

    assert mode1 == mode2
    assert signature1 == signature2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
