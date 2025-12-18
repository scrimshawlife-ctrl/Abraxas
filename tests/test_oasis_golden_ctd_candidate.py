"""Golden test for CTD candidate generation."""

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


@pytest.fixture
def golden_candidate():
    """Load golden CTD candidate."""
    fixture_path = Path(__file__).parent / "fixtures" / "golden_ctd_candidate.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


def test_ctd_operator_detection(sample_events):
    """Test that CTD operator correctly detects patterns."""
    from abraxas.slang.operators.builtin_ctd import CTDOperator

    ctd = CTDOperator()

    # Test affiliative pattern
    readout1 = ctd.apply("rawr xD this is cute")
    assert readout1 is not None
    assert readout1.label == "affiliative"
    assert readout1.operator_id == "ctd_v1"

    # Test play aggression
    readout2 = ctd.apply("bonk! gonna yeet this lmao")
    assert readout2 is not None
    assert readout2.label == "play_aggression"

    # Test no match
    readout3 = ctd.apply("just normal text")
    assert readout3 is None


def test_pipeline_produces_phonetic_candidates(sample_events):
    """Test that pipeline produces phonetic pattern candidates."""
    collector = OASCollector()
    engine = SlangEngine()
    miner = OASMiner()
    proposer = OASProposer()

    frames = collector.collect_from_events(sample_events)
    clusters = engine.detect_clusters(frames)
    patterns = miner.mine(clusters, frames)
    candidates = proposer.propose(patterns, clusters, frames)

    # Should have some phonetic candidates
    phonetic_candidates = [
        c for c in candidates if "phonetic" in c.class_tags
    ]

    assert len(phonetic_candidates) > 0, "Should generate phonetic candidates"

    # Check structure of first phonetic candidate
    if phonetic_candidates:
        candidate = phonetic_candidates[0]
        assert candidate.operator_id.startswith("oasis_")
        assert "phonetic" in candidate.class_tags
        assert len(candidate.triggers) > 0
        assert len(candidate.readouts) > 0
        assert candidate.version == "1.0.0"


def test_golden_candidate_structure(golden_candidate):
    """Test that golden candidate has expected structure."""
    # Required fields
    assert "operator_id" in golden_candidate
    assert "label" in golden_candidate
    assert "class_tags" in golden_candidate
    assert "triggers" in golden_candidate
    assert "readouts" in golden_candidate
    assert "provenance" in golden_candidate
    assert "discovery_window" in golden_candidate

    # Check types
    assert isinstance(golden_candidate["class_tags"], list)
    assert isinstance(golden_candidate["triggers"], list)
    assert isinstance(golden_candidate["readouts"], list)

    # Check provenance structure
    prov = golden_candidate["provenance"]
    assert "inputs" in prov
    assert "transforms" in prov
    assert "metrics" in prov
    assert "created_by" in prov


def test_candidate_matches_golden_structure(sample_events, golden_candidate):
    """Test that generated candidates match golden structure."""
    collector = OASCollector()
    engine = SlangEngine()
    miner = OASMiner()
    proposer = OASProposer()

    frames = collector.collect_from_events(sample_events)
    clusters = engine.detect_clusters(frames)
    patterns = miner.mine(clusters, frames)
    candidates = proposer.propose(patterns, clusters, frames)

    # Find a phonetic candidate
    phonetic_candidates = [
        c for c in candidates if "phonetic" in c.class_tags
    ]

    if phonetic_candidates:
        candidate = phonetic_candidates[0]
        candidate_dict = candidate.model_dump()

        # Check that all golden keys exist in candidate
        golden_keys = set(golden_candidate.keys())
        candidate_keys = set(candidate_dict.keys())

        # All golden keys should be present
        assert golden_keys.issubset(candidate_keys), \
            f"Missing keys: {golden_keys - candidate_keys}"


def test_operator_id_stability(sample_events):
    """Test that operator IDs are stable for same patterns."""
    collector = OASCollector()
    engine = SlangEngine()
    miner = OASMiner()
    proposer = OASProposer()

    # Run pipeline twice
    def get_operator_ids():
        frames = collector.collect_from_events(sample_events)
        clusters = engine.detect_clusters(frames)
        patterns = miner.mine(clusters, frames)
        candidates = proposer.propose(patterns, clusters, frames)
        return sorted([c.operator_id for c in candidates])

    ids1 = get_operator_ids()
    ids2 = get_operator_ids()

    assert ids1 == ids2, "Operator IDs should be stable"


def test_candidate_score_in_valid_range(sample_events):
    """Test that all candidate scores are in [0, 1]."""
    collector = OASCollector()
    engine = SlangEngine()
    miner = OASMiner()
    proposer = OASProposer()

    frames = collector.collect_from_events(sample_events)
    clusters = engine.detect_clusters(frames)
    patterns = miner.mine(clusters, frames)
    candidates = proposer.propose(patterns, clusters, frames)

    for candidate in candidates:
        assert 0.0 <= candidate.candidate_score <= 1.0, \
            f"Candidate {candidate.operator_id} has invalid score: {candidate.candidate_score}"


def test_provenance_completeness(sample_events):
    """Test that all candidates have complete provenance."""
    collector = OASCollector()
    engine = SlangEngine()
    miner = OASMiner()
    proposer = OASProposer()

    frames = collector.collect_from_events(sample_events)
    clusters = engine.detect_clusters(frames)
    patterns = miner.mine(clusters, frames)
    candidates = proposer.propose(patterns, clusters, frames)

    for candidate in candidates:
        prov = candidate.provenance

        # Check required provenance fields
        assert len(prov.inputs) > 0, f"Candidate {candidate.operator_id} missing provenance inputs"
        assert len(prov.transforms) > 0, f"Candidate {candidate.operator_id} missing transforms"
        assert prov.created_by is not None

        # Check that input refs have hashes
        for inp in prov.inputs:
            assert len(inp.sha256) > 0, "ProvenanceRef missing hash"


def test_discovery_window_validity(sample_events):
    """Test that discovery windows are valid."""
    collector = OASCollector()
    engine = SlangEngine()
    miner = OASMiner()
    proposer = OASProposer()

    frames = collector.collect_from_events(sample_events)
    clusters = engine.detect_clusters(frames)
    patterns = miner.mine(clusters, frames)
    candidates = proposer.propose(patterns, clusters, frames)

    for candidate in candidates:
        window = candidate.discovery_window

        assert "start_ts" in window
        assert "end_ts" in window
        assert "sources" in window

        # Start should be before or equal to end
        from datetime import datetime
        start = datetime.fromisoformat(window["start_ts"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(window["end_ts"].replace("Z", "+00:00"))
        assert start <= end, f"Invalid discovery window for {candidate.operator_id}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
