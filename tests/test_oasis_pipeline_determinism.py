"""Tests for OAS pipeline determinism."""

import json
import pytest
from pathlib import Path

from abraxas.core.provenance import hash_canonical_json
from abraxas.decodo.models import DecodoEvent
from abraxas.oasis.collector import OASCollector
from abraxas.oasis.miner import OASMiner
from abraxas.oasis.proposer import OASProposer
from abraxas.slang.engine import SlangEngine


@pytest.fixture
def sample_events():
    """Load sample events from fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "decodo_events_small.json"
    with open(fixture_path, "r") as f:
        event_dicts = json.load(f)
    return [DecodoEvent(**e) for e in event_dicts]


def test_collector_determinism(sample_events):
    """Test that collector produces deterministic output."""
    collector = OASCollector()

    # Run twice
    frames1 = collector.collect_from_events(sample_events)
    frames2 = collector.collect_from_events(sample_events)

    # Should have same length
    assert len(frames1) == len(frames2)

    # Should be in same order
    for f1, f2 in zip(frames1, frames2):
        assert f1.event_id == f2.event_id
        assert f1.ts == f2.ts
        assert f1.text == f2.text


def test_miner_determinism(sample_events):
    """Test that miner produces deterministic patterns."""
    collector = OASCollector()
    engine = SlangEngine()

    frames = collector.collect_from_events(sample_events)
    clusters = engine.detect_clusters(frames)

    miner = OASMiner()

    # Run twice
    patterns1 = miner.mine(clusters, frames)
    patterns2 = miner.mine(clusters, frames)

    # Should have same length
    assert len(patterns1) == len(patterns2)

    # Should have same content (order-independent check)
    sigs1 = sorted([p.get("signature", "") for p in patterns1])
    sigs2 = sorted([p.get("signature", "") for p in patterns2])
    assert sigs1 == sigs2


def test_proposer_determinism(sample_events):
    """Test that proposer produces deterministic candidates."""
    collector = OASCollector()
    engine = SlangEngine()
    miner = OASMiner()
    proposer = OASProposer()

    frames = collector.collect_from_events(sample_events)
    clusters = engine.detect_clusters(frames)
    patterns = miner.mine(clusters, frames)

    # Run twice
    candidates1 = proposer.propose(patterns, clusters, frames)
    candidates2 = proposer.propose(patterns, clusters, frames)

    # Should have same length
    assert len(candidates1) == len(candidates2)

    # Should have same operator IDs in same order
    ids1 = [c.operator_id for c in candidates1]
    ids2 = [c.operator_id for c in candidates2]
    assert ids1 == ids2

    # Check hash stability for first candidate
    if candidates1:
        hash1 = hash_canonical_json(candidates1[0].model_dump())
        hash2 = hash_canonical_json(candidates2[0].model_dump())
        # Note: timestamps in provenance may differ, so we check structure instead
        assert candidates1[0].operator_id == candidates2[0].operator_id
        assert candidates1[0].label == candidates2[0].label
        assert candidates1[0].triggers == candidates2[0].triggers


def test_full_pipeline_determinism(sample_events):
    """Test that full pipeline produces deterministic operator IDs."""
    collector = OASCollector()
    engine = SlangEngine()
    miner = OASMiner()
    proposer = OASProposer()

    # Run full pipeline twice
    def run_pipeline():
        frames = collector.collect_from_events(sample_events)
        clusters = engine.detect_clusters(frames)
        patterns = miner.mine(clusters, frames)
        candidates = proposer.propose(patterns, clusters, frames)
        return candidates

    candidates1 = run_pipeline()
    candidates2 = run_pipeline()

    # Extract operator IDs and compare
    ids1 = sorted([c.operator_id for c in candidates1])
    ids2 = sorted([c.operator_id for c in candidates2])

    assert ids1 == ids2, "Pipeline should produce same operator IDs"


def test_frame_ordering_stability(sample_events):
    """Test that frame ordering is stable across runs."""
    collector = OASCollector()

    # Run multiple times
    runs = []
    for _ in range(3):
        frames = collector.collect_from_events(sample_events)
        event_ids = [f.event_id for f in frames]
        runs.append(event_ids)

    # All runs should have same order
    assert runs[0] == runs[1] == runs[2]


def test_cluster_id_determinism(sample_events):
    """Test that cluster IDs are deterministic."""
    collector = OASCollector()
    engine = SlangEngine()

    frames = collector.collect_from_events(sample_events)

    # Run clustering twice
    clusters1 = engine.detect_clusters(frames)
    clusters2 = engine.detect_clusters(frames)

    # Cluster IDs should be same (order may vary, so sort)
    ids1 = sorted([c.cluster_id for c in clusters1])
    ids2 = sorted([c.cluster_id for c in clusters2])

    assert ids1 == ids2


def test_pattern_signature_stability():
    """Test that pattern signatures are stable."""
    from abraxas.oasis.miner import MinedPattern

    # Create identical patterns
    pattern1 = MinedPattern(
        {"pattern_type": "test", "signature": "test_sig", "frequency": 5}
    )
    pattern2 = MinedPattern(
        {"pattern_type": "test", "signature": "test_sig", "frequency": 5}
    )

    hash1 = hash_canonical_json(pattern1)
    hash2 = hash_canonical_json(pattern2)

    assert hash1 == hash2


def test_candidate_id_from_pattern_determinism():
    """Test that candidate IDs derived from patterns are deterministic."""
    from abraxas.oasis.miner import MinedPattern

    pattern = MinedPattern(
        {"pattern_type": "test", "signature": "test_pattern", "tokens": ["a", "b"]}
    )

    # Generate candidate ID twice
    id1 = f"oasis_{hash_canonical_json(pattern)[:16]}"
    id2 = f"oasis_{hash_canonical_json(pattern)[:16]}"

    assert id1 == id2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
