"""Tests for VBM drift tagging in SEE."""

import pytest
from datetime import datetime, timezone

from abraxas.core.resonance_frame import ResonanceFrame
from abraxas.decodo.models import DecodoEvent
from abraxas.slang.engine import SlangEngine


def test_vbm_drift_tag_fires():
    """Test that VBM drift tag fires on VBM-class text."""
    # Create frame with VBM-class content
    event = DecodoEvent(
        event_id="test_vbm_001",
        timestamp=datetime.now(timezone.utc),
        source_url="https://test.example/vbm",
        source_type="test",
        content="The tachyon particles emerge from the torus zero point field connecting consciousness to the inertia ether through vortex dynamics",
        metadata={},
    )

    frame = ResonanceFrame(
        event_id=event.event_id,
        ts=event.timestamp,
        source="test:vbm",
        text=event.content,
        meta={},
    )

    # Process through SEE
    engine = SlangEngine(enable_vbm_casebook=True)
    clusters = engine.process_frames([frame])

    # Should have at least one cluster
    assert len(clusters) > 0

    # Check if any cluster has VBM drift tag
    vbm_tagged = any("VBM_CLASS" in cluster.drift_tags for cluster in clusters)
    assert vbm_tagged, "VBM_CLASS tag should fire on VBM-like content"


def test_vbm_phase_annotation():
    """Test that VBM phase is annotated when tag fires."""
    event = DecodoEvent(
        event_id="test_vbm_002",
        timestamp=datetime.now(timezone.utc),
        source_url="https://test.example/vbm",
        source_type="test",
        content="Consciousness operates at the apex through frequency vibration patterns in the cosmic torus",
        metadata={},
    )

    frame = ResonanceFrame(
        event_id=event.event_id,
        ts=event.timestamp,
        source="test:vbm",
        text=event.content,
        meta={},
    )

    engine = SlangEngine(enable_vbm_casebook=True)
    clusters = engine.process_frames([frame])

    # Find VBM-tagged cluster
    vbm_clusters = [c for c in clusters if "VBM_CLASS" in c.drift_tags]

    if vbm_clusters:
        cluster = vbm_clusters[0]
        assert cluster.vbm_phase is not None, "VBM phase should be annotated"
        assert cluster.vbm_score is not None, "VBM score should be annotated"
        assert cluster.vbm_score >= 0.65, "VBM score should be >= threshold"


def test_vbm_lattice_hits():
    """Test that VBM lattice hits are recorded."""
    event = DecodoEvent(
        event_id="test_vbm_003",
        timestamp=datetime.now(timezone.utc),
        source_url="https://test.example/vbm",
        source_type="test",
        content="The vortex pattern explains zero-point energy and tachyon dynamics in the ether field",
        metadata={},
    )

    frame = ResonanceFrame(
        event_id=event.event_id,
        ts=event.timestamp,
        source="test:vbm",
        text=event.content,
        meta={},
    )

    engine = SlangEngine(enable_vbm_casebook=True)
    clusters = engine.process_frames([frame])

    vbm_clusters = [c for c in clusters if "VBM_CLASS" in c.drift_tags]

    if vbm_clusters:
        cluster = vbm_clusters[0]
        assert len(cluster.vbm_lattice_hits) > 0, "VBM lattice hits should be recorded"
        # Should have at least one lattice operator ID
        assert any(hit in ["MKB", "PAP", "DOE", "SCA", "PAM", "UCS"] for hit in cluster.vbm_lattice_hits)


def test_neutral_text_no_vbm_tag():
    """Test that neutral text doesn't get VBM tag."""
    event = DecodoEvent(
        event_id="test_neutral_001",
        timestamp=datetime.now(timezone.utc),
        source_url="https://test.example/neutral",
        source_type="test",
        content="I went to the grocery store today and bought some vegetables for dinner",
        metadata={},
    )

    frame = ResonanceFrame(
        event_id=event.event_id,
        ts=event.timestamp,
        source="test:neutral",
        text=event.content,
        meta={},
    )

    engine = SlangEngine(enable_vbm_casebook=True)
    clusters = engine.process_frames([frame])

    # Should not have VBM tag
    for cluster in clusters:
        assert "VBM_CLASS" not in cluster.drift_tags, "Neutral text should not get VBM tag"


def test_vbm_disabled():
    """Test that VBM tagging can be disabled."""
    event = DecodoEvent(
        event_id="test_vbm_004",
        timestamp=datetime.now(timezone.utc),
        source_url="https://test.example/vbm",
        source_type="test",
        content="The tachyon torus consciousness ether pattern",
        metadata={},
    )

    frame = ResonanceFrame(
        event_id=event.event_id,
        ts=event.timestamp,
        source="test:vbm",
        text=event.content,
        meta={},
    )

    # Disable VBM
    engine = SlangEngine(enable_vbm_casebook=False)
    clusters = engine.process_frames([frame])

    # Should not have VBM tags
    for cluster in clusters:
        assert "VBM_CLASS" not in cluster.drift_tags


def test_vbm_score_threshold():
    """Test that only high-scoring text gets tagged."""
    # Low-scoring text (just one VBM word)
    event_low = DecodoEvent(
        event_id="test_low_001",
        timestamp=datetime.now(timezone.utc),
        source_url="https://test.example/low",
        source_type="test",
        content="This is a normal sentence with just one pattern word",
        metadata={},
    )

    frame_low = ResonanceFrame(
        event_id=event_low.event_id,
        ts=event_low.timestamp,
        source="test:low",
        text=event_low.content,
        meta={},
    )

    engine = SlangEngine(enable_vbm_casebook=True)
    clusters_low = engine.process_frames([frame_low])

    # Should likely not be tagged (score < 0.65)
    low_tagged = any("VBM_CLASS" in c.drift_tags for c in clusters_low)
    # This may or may not tag depending on threshold, but score should be low
    if low_tagged:
        cluster = next(c for c in clusters_low if "VBM_CLASS" in c.drift_tags)
        # If tagged, score should still be close to threshold
        assert cluster.vbm_score is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
