"""Tests for VBM casebook ingestion and determinism."""

import json
import pytest
from pathlib import Path

from abraxas.casebooks.vbm.corpus import load_episodes_from_fixtures, build_casebook
from abraxas.casebooks.vbm.models import VBMEpisode
from abraxas.core.provenance import hash_canonical_json


def test_load_episodes_deterministic():
    """Test that episodes load deterministically."""
    episodes1 = load_episodes_from_fixtures()
    episodes2 = load_episodes_from_fixtures()

    # Should load same episodes in same order
    assert len(episodes1) == len(episodes2)

    for ep1, ep2 in zip(episodes1, episodes2):
        assert ep1.episode_id == ep2.episode_id
        assert ep1.title == ep2.title
        assert ep1.summary_text == ep2.summary_text


def test_episode_count():
    """Test that exactly 7 episodes are loaded."""
    episodes = load_episodes_from_fixtures()
    assert len(episodes) == 7, f"Expected 7 episodes, got {len(episodes)}"


def test_episode_ids_sequential():
    """Test that episode IDs are sequential."""
    episodes = load_episodes_from_fixtures()
    episode_ids = [ep.episode_id for ep in episodes]

    expected_ids = [f"vbm_0{i}" for i in range(1, 8)]
    assert episode_ids == expected_ids


def test_episode_sha256_stable():
    """Test that episode hashes are stable across loads."""
    episodes1 = load_episodes_from_fixtures()
    episodes2 = load_episodes_from_fixtures()

    for ep1, ep2 in zip(episodes1, episodes2):
        hash1 = hash_canonical_json(ep1.model_dump())
        hash2 = hash_canonical_json(ep2.model_dump())
        assert hash1 == hash2, f"Hash mismatch for {ep1.episode_id}"


def test_extracted_tokens_present():
    """Test that token extraction works."""
    episodes = load_episodes_from_fixtures()

    # Episode 1 should have pattern-related tokens
    ep1 = next(ep for ep in episodes if ep.episode_id == "vbm_01")
    assert len(ep1.extracted_tokens) > 0, "Episode 1 should have extracted tokens"
    assert any("pattern" in token or "torus" in token for token in ep1.extracted_tokens)

    # Episode 4 should have physics tokens
    ep4 = next(ep for ep in episodes if ep.episode_id == "vbm_04")
    assert len(ep4.extracted_tokens) > 0, "Episode 4 should have extracted tokens"
    assert any(
        token in ["tachyon", "ether", "zero-point", "photon", "electron", "monopole"]
        for token in ep4.extracted_tokens
    )


def test_extracted_claims_present():
    """Test that claims extraction works."""
    episodes = load_episodes_from_fixtures()

    for episode in episodes:
        # Each episode should have some claims (at least 1)
        assert len(episode.extracted_claims) > 0, f"{episode.episode_id} has no claims"


def test_casebook_build():
    """Test building complete casebook."""
    episodes = load_episodes_from_fixtures()
    casebook = build_casebook(episodes)

    assert casebook.casebook_id == "VBM_SERIES"
    assert len(casebook.episodes) == 7
    assert len(casebook.trigger_lexicon) > 0


def test_provenance_complete():
    """Test that all episodes have complete provenance."""
    episodes = load_episodes_from_fixtures()

    for episode in episodes:
        prov = episode.provenance

        assert len(prov.inputs) > 0, f"{episode.episode_id} missing provenance inputs"
        assert len(prov.transforms) > 0, f"{episode.episode_id} missing transforms"
        assert prov.created_by == "vbm_corpus_loader"


def test_whitespace_normalization():
    """Test that whitespace is normalized."""
    episodes = load_episodes_from_fixtures()

    for episode in episodes:
        # No double spaces
        assert "  " not in episode.summary_text, f"{episode.episode_id} has double spaces"

        # No leading/trailing whitespace
        assert episode.summary_text == episode.summary_text.strip()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
