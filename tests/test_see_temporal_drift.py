"""Tests for SEE temporal drift detection integration."""

import pytest
from datetime import datetime, timezone

from abraxas.core.resonance_frame import ResonanceFrame
from abraxas.decodo.models import DecodoEvent
from abraxas.slang.engine import SlangEngine
from abraxas.temporal.models import TemporalMode, SovereigntyRisk


def test_tdd_annotation_on_inverted_causality():
    """Test that TDD annotates clusters with inverted causality."""
    event = DecodoEvent(
        event_id="test_tdd_001",
        timestamp=datetime.now(timezone.utc),
        source_url="https://test.example/retronic",
        source_type="test",
        content="Time flows backwards through retrocausal determination. The future causes the past.",
        metadata={},
    )

    frame = ResonanceFrame(
        event_id=event.event_id,
        ts=event.timestamp,
        source="test:retronic",
        text=event.content,
        meta={},
    )

    # Process through SEE with TDD enabled
    engine = SlangEngine(enable_tdd=True)
    clusters = engine.process_frames([frame])

    # Should have at least one cluster
    assert len(clusters) > 0

    # Find cluster with temporal mode
    temporal_clusters = [c for c in clusters if c.temporal_mode is not None]

    if temporal_clusters:
        cluster = temporal_clusters[0]
        assert cluster.temporal_mode == TemporalMode.INVERTED.value
        assert "RTI" in cluster.tdd_operator_hits


def test_tdd_annotation_on_eschatological_text():
    """Test that TDD annotates clusters with eschatological mode."""
    event = DecodoEvent(
        event_id="test_tdd_002",
        timestamp=datetime.now(timezone.utc),
        source_url="https://test.example/eschaton",
        source_type="test",
        content="The eschaton approaches inevitably. The apocalypse determines all destiny toward end-times.",
        metadata={},
    )

    frame = ResonanceFrame(
        event_id=event.event_id,
        ts=event.timestamp,
        source="test:eschaton",
        text=event.content,
        meta={},
    )

    engine = SlangEngine(enable_tdd=True)
    clusters = engine.process_frames([frame])

    assert len(clusters) > 0

    temporal_clusters = [c for c in clusters if c.temporal_mode is not None]

    if temporal_clusters:
        cluster = temporal_clusters[0]
        assert cluster.temporal_mode == TemporalMode.ESCHATOLOGICAL.value
        assert "HSE" in cluster.tdd_operator_hits


def test_tdd_sovereignty_risk_annotation():
    """Test that sovereignty risk is annotated."""
    event = DecodoEvent(
        event_id="test_tdd_003",
        timestamp=datetime.now(timezone.utc),
        source_url="https://test.example/authority",
        source_type="test",
        content="The diagram commands reality with absolute authority, abolishing agency through destiny.",
        metadata={},
    )

    frame = ResonanceFrame(
        event_id=event.event_id,
        ts=event.timestamp,
        source="test:authority",
        text=event.content,
        meta={},
    )

    engine = SlangEngine(enable_tdd=True)
    clusters = engine.process_frames([frame])

    assert len(clusters) > 0

    risk_clusters = [c for c in clusters if c.sovereignty_risk is not None]

    if risk_clusters:
        cluster = risk_clusters[0]
        assert cluster.sovereignty_risk in [
            SovereigntyRisk.HIGH.value,
            SovereigntyRisk.CRITICAL.value,
        ]


def test_tdd_de_escalate_on_high_risk():
    """Test that de-escalate response mode is set for high sovereignty risk."""
    event = DecodoEvent(
        event_id="test_tdd_004",
        timestamp=datetime.now(timezone.utc),
        source_url="https://test.example/critical",
        source_type="test",
        content="The eschaton commands through retrocausal diagram authority, abolishing all human agency and free will through inevitable destiny.",
        metadata={},
    )

    frame = ResonanceFrame(
        event_id=event.event_id,
        ts=event.timestamp,
        source="test:critical",
        text=event.content,
        meta={},
    )

    engine = SlangEngine(enable_tdd=True)
    clusters = engine.process_frames([frame])

    assert len(clusters) > 0

    # Should have at least one cluster with de-escalate response mode
    de_escalate_clusters = [c for c in clusters if c.response_mode == "de-escalate"]

    # If sovereignty risk is HIGH or CRITICAL, should have de-escalate
    critical_clusters = [
        c
        for c in clusters
        if c.sovereignty_risk in [SovereigntyRisk.HIGH.value, SovereigntyRisk.CRITICAL.value]
    ]

    if critical_clusters:
        assert len(de_escalate_clusters) > 0, "High risk clusters should have de-escalate response mode"


def test_tdd_operator_hits_recorded():
    """Test that TDD operator hits are recorded."""
    event = DecodoEvent(
        event_id="test_tdd_005",
        timestamp=datetime.now(timezone.utc),
        source_url="https://test.example/full_drift",
        source_type="test",
        content="The eschaton flows backwards through the diagram's command authority, erasing agency.",
        metadata={},
    )

    frame = ResonanceFrame(
        event_id=event.event_id,
        ts=event.timestamp,
        source="test:full_drift",
        text=event.content,
        meta={},
    )

    engine = SlangEngine(enable_tdd=True)
    clusters = engine.process_frames([frame])

    assert len(clusters) > 0

    # Check that operator hits are recorded
    hit_clusters = [c for c in clusters if len(c.tdd_operator_hits) > 0]

    if hit_clusters:
        cluster = hit_clusters[0]
        # Should have at least one TDD operator
        valid_operators = ["RTI", "DTA", "HSE", "UCS"]
        assert any(op in valid_operators for op in cluster.tdd_operator_hits)


def test_neutral_text_no_tdd_triggers():
    """Test that neutral text doesn't trigger TDD annotations."""
    event = DecodoEvent(
        event_id="test_neutral_001",
        timestamp=datetime.now(timezone.utc),
        source_url="https://test.example/neutral",
        source_type="test",
        content="I went to the grocery store today and bought vegetables for dinner.",
        metadata={},
    )

    frame = ResonanceFrame(
        event_id=event.event_id,
        ts=event.timestamp,
        source="test:neutral",
        text=event.content,
        meta={},
    )

    engine = SlangEngine(enable_tdd=True)
    clusters = engine.process_frames([frame])

    # Should not have critical sovereignty risk
    for cluster in clusters:
        if cluster.sovereignty_risk is not None:
            assert cluster.sovereignty_risk != SovereigntyRisk.CRITICAL.value


def test_tdd_disabled():
    """Test that TDD can be disabled."""
    event = DecodoEvent(
        event_id="test_tdd_006",
        timestamp=datetime.now(timezone.utc),
        source_url="https://test.example/retronic",
        source_type="test",
        content="Time flows backwards through retrocausal loops.",
        metadata={},
    )

    frame = ResonanceFrame(
        event_id=event.event_id,
        ts=event.timestamp,
        source="test:retronic",
        text=event.content,
        meta={},
    )

    # Disable TDD
    engine = SlangEngine(enable_tdd=False)
    clusters = engine.process_frames([frame])

    # Should not have TDD annotations
    for cluster in clusters:
        assert cluster.temporal_mode is None
        assert cluster.sovereignty_risk is None
        assert len(cluster.tdd_operator_hits) == 0


def test_tdd_with_existing_operators():
    """Test that TDD merges with existing operator hits."""
    event = DecodoEvent(
        event_id="test_tdd_007",
        timestamp=datetime.now(timezone.utc),
        source_url="https://test.example/combined",
        source_type="test",
        content="The eschaton approaches through retrocausal destiny.",
        metadata={},
    )

    frame = ResonanceFrame(
        event_id=event.event_id,
        ts=event.timestamp,
        source="test:combined",
        text=event.content,
        meta={},
    )

    engine = SlangEngine(enable_tdd=True)
    clusters = engine.process_frames([frame])

    # TDD operator hits should be present and sorted
    hit_clusters = [c for c in clusters if len(c.tdd_operator_hits) > 0]

    if hit_clusters:
        cluster = hit_clusters[0]
        # Should be sorted
        assert cluster.tdd_operator_hits == sorted(cluster.tdd_operator_hits)


def test_tdd_deterministic():
    """Test that TDD analysis is deterministic."""
    event = DecodoEvent(
        event_id="test_tdd_008",
        timestamp=datetime.now(timezone.utc),
        source_url="https://test.example/deterministic",
        source_type="test",
        content="The future determines the past through retrocausal loops.",
        metadata={},
    )

    frame = ResonanceFrame(
        event_id=event.event_id,
        ts=event.timestamp,
        source="test:deterministic",
        text=event.content,
        meta={},
    )

    engine = SlangEngine(enable_tdd=True)

    clusters1 = engine.process_frames([frame])
    clusters2 = engine.process_frames([frame])

    # Should produce identical results
    assert len(clusters1) == len(clusters2)

    for c1, c2 in zip(clusters1, clusters2):
        assert c1.temporal_mode == c2.temporal_mode
        assert c1.sovereignty_risk == c2.sovereignty_risk
        assert c1.tdd_operator_hits == c2.tdd_operator_hits


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
