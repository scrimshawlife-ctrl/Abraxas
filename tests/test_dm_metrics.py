"""Golden tests for D/M metrics.

Tests deterministic integrity and manipulation metrics.
"""

import pytest

from abraxas.integrity.dm_metrics import (
    compute_artifact_integrity,
    ConfidenceLevel,
)
from abraxas.integrity.composites import (
    compute_narrative_manipulation,
    compute_network_campaign,
    compute_composite_risk,
)
from abraxas.integrity.payload_taxonomy import classify_payload, PayloadType


def test_artifact_integrity_high_quality():
    """Test artifact integrity with all fields present."""
    metrics = compute_artifact_integrity(
        has_timestamp=True,
        has_source_id=True,
        has_author=True,
        has_provenance_hash=True,
        source_chain_length=3,
        has_edit_history=True,
        edit_count=1,
        cross_platform_matches=3,
        total_platforms_checked=3,
        has_supporting_evidence=True,
        evidence_quality_score=0.9,
    )

    assert metrics.pps == 1.0  # All provenance fields present
    assert metrics.confidence == ConfidenceLevel.HIGH
    assert metrics.eis == 0.9


def test_artifact_integrity_low_quality():
    """Test artifact integrity with minimal fields."""
    metrics = compute_artifact_integrity(
        has_timestamp=False,
        has_source_id=False,
        has_author=False,
        has_provenance_hash=False,
        source_chain_length=0,
        has_edit_history=False,
        edit_count=0,
        cross_platform_matches=0,
        total_platforms_checked=1,
        has_supporting_evidence=False,
        evidence_quality_score=0.0,
    )

    assert metrics.pps == 0.0  # No provenance fields
    assert metrics.confidence == ConfidenceLevel.LOW
    assert metrics.fields_present < 3


def test_narrative_manipulation_metrics():
    """Test narrative manipulation metrics calculation."""
    metrics = compute_narrative_manipulation(
        framing_indicators=3,
        total_framing_checked=5,
        emotional_word_count=25,
        total_word_count=100,
        omission_flags=2,
        total_omission_checks=3,
        repetition_count=10,
        unique_message_count=2,
        misattribution_indicators=1,
        total_attribution_checks=3,
        coordination_signals=2,
        total_coordination_checks=4,
    )

    assert metrics.fls == 0.6  # 3/5
    assert metrics.eil == 0.25  # 25/100
    assert metrics.rrs == 0.5  # 10/2 / 10 = 0.5
    assert metrics.confidence in [ConfidenceLevel.MED, ConfidenceLevel.HIGH]


def test_composite_risk_indices():
    """Test composite IRI/MRI calculation."""
    artifact_integrity = compute_artifact_integrity(
        has_timestamp=True,
        has_source_id=True,
        has_author=False,
        has_provenance_hash=True,
        source_chain_length=1,
    )

    narrative_manipulation = compute_narrative_manipulation(
        framing_indicators=4,
        total_framing_checked=5,
        emotional_word_count=40,
        total_word_count=100,
    )

    network_campaign = compute_network_campaign(
        uniformity_score=0.8,
        propagation_rate=50.0,
        burst_amplitude=10.0,
    )

    risk = compute_composite_risk(
        artifact_integrity, narrative_manipulation, network_campaign
    )

    assert 0 <= risk.iri <= 100
    assert 0 <= risk.mri <= 100
    assert risk.confidence in [ConfidenceLevel.LOW, ConfidenceLevel.MED, ConfidenceLevel.HIGH]


def test_payload_classification_authentic():
    """Test authentic payload classification."""
    artifact_integrity = compute_artifact_integrity(
        has_timestamp=True,
        has_source_id=True,
        has_author=True,
        has_provenance_hash=True,
        source_chain_length=3,
    )

    narrative_manipulation = compute_narrative_manipulation(
        framing_indicators=0,
        total_framing_checked=5,
        emotional_word_count=5,
        total_word_count=100,
    )

    network_campaign = compute_network_campaign(
        uniformity_score=0.2,
        propagation_rate=2.0,
    )

    risk = compute_composite_risk(
        artifact_integrity, narrative_manipulation, network_campaign
    )

    classification = classify_payload(risk)
    assert classification.payload_type == PayloadType.AUTHENTIC


def test_payload_classification_fabricated():
    """Test fabricated payload classification."""
    artifact_integrity = compute_artifact_integrity(
        has_timestamp=False,
        has_source_id=False,
        has_author=False,
        has_provenance_hash=False,
        source_chain_length=0,
    )

    narrative_manipulation = compute_narrative_manipulation(
        framing_indicators=5,
        total_framing_checked=5,
        emotional_word_count=80,
        total_word_count=100,
        repetition_count=20,
        unique_message_count=1,
    )

    network_campaign = compute_network_campaign(
        uniformity_score=0.9,
        propagation_rate=100.0,
        burst_amplitude=50.0,
        domain_count=8,
    )

    risk = compute_composite_risk(
        artifact_integrity, narrative_manipulation, network_campaign
    )

    classification = classify_payload(risk)
    assert classification.payload_type == PayloadType.FABRICATED
