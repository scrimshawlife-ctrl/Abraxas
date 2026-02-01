"""Tests for Numogram Retrónic Time casebook ingestion."""

import json
import pytest
from pathlib import Path

from abraxas.casebooks.numogram.corpus import load_numogram_episodes, build_numogram_casebook
from abraxas.casebooks.numogram.models import NumogramEpisode
from abraxas.temporal.detector import analyze_text
from abraxas.temporal.models import TemporalMode, SovereigntyRisk
from abraxas.core.provenance import hash_canonical_json


@pytest.fixture
def expected_tdd_results():
    """Load expected TDD results."""
    fixture_path = Path(__file__).parent / "fixtures" / "numogram" / "retronic_expected_tdd.json"
    with open(fixture_path, "r") as f:
        data = json.load(f)
    return data["expected_results"][0]


def test_load_retronic_episode():
    """Test loading Retrónic Time episode."""
    episodes = load_numogram_episodes()

    # Should have exactly 1 episode (numogram_08)
    assert len(episodes) == 1

    retronic = episodes[0]
    assert retronic.episode_id == "numogram_08"
    assert "Retrónic Time" in retronic.title
    assert "temporal inversion" in retronic.summary_text.lower()


def test_retronic_episode_deterministic():
    """Test that Retrónic episode loads deterministically."""
    episodes1 = load_numogram_episodes()
    episodes2 = load_numogram_episodes()

    assert len(episodes1) == len(episodes2)

    ep1 = episodes1[0]
    ep2 = episodes2[0]

    assert ep1.episode_id == ep2.episode_id
    assert ep1.title == ep2.title
    assert ep1.summary_text == ep2.summary_text


def test_retronic_episode_sha256_stable():
    """Test that episode hash is stable across loads."""
    episodes1 = load_numogram_episodes()
    episodes2 = load_numogram_episodes()

    ep1 = episodes1[0]
    ep2 = episodes2[0]

    hash1 = hash_canonical_json(ep1.model_dump())
    hash2 = hash_canonical_json(ep2.model_dump())
    assert hash1 == hash2


def test_retronic_token_extraction():
    """Test that temporal tokens are extracted from Retrónic episode."""
    episodes = load_numogram_episodes()
    retronic = episodes[0]

    # Should have tokens from all categories
    assert len(retronic.extracted_tokens) > 0

    # Should have retronic terms
    retronic_terms = ["retronic", "retrocausal", "temporal inversion", "backwards"]
    assert any(term in retronic.extracted_tokens for term in retronic_terms)

    # Should have eschatology terms
    eschat_terms = ["eschaton", "apocalypse", "destiny", "inevitable"]
    assert any(term in retronic.extracted_tokens for term in eschat_terms)

    # Should have diagram authority terms
    diagram_terms = ["diagram", "authority", "teleology", "commands"]
    assert any(term in retronic.extracted_tokens for term in diagram_terms)


def test_retronic_claims_extraction():
    """Test that claims are extracted from Retrónic episode."""
    episodes = load_numogram_episodes()
    retronic = episodes[0]

    # Should have extracted claims
    assert len(retronic.extracted_claims) > 0

    # Claims should be substantial
    for claim in retronic.extracted_claims:
        assert len(claim) > 10


def test_retronic_tdd_analysis(expected_tdd_results):
    """Test TDD analysis on Retrónic episode matches expected results."""
    episodes = load_numogram_episodes()
    retronic = episodes[0]

    # Analyze with TDD
    tdd_result = analyze_text(retronic.summary_text)

    # Check temporal mode
    assert tdd_result.temporal_mode.value == expected_tdd_results["temporal_mode"]

    # Check causality status
    assert tdd_result.causality_status.value == expected_tdd_results["causality_status"]

    # Check diagram role
    assert tdd_result.diagram_role.value == expected_tdd_results["diagram_role"]

    # Check sovereignty risk
    assert tdd_result.sovereignty_risk.value == expected_tdd_results["sovereignty_risk"]

    # Check operator hits (should have all expected operators)
    expected_ops = set(expected_tdd_results["operator_hits"])
    actual_ops = set(tdd_result.operator_hits)
    assert expected_ops.issubset(actual_ops), f"Missing operators: {expected_ops - actual_ops}"


def test_retronic_critical_sovereignty_risk():
    """Test that Retrónic episode triggers CRITICAL sovereignty risk."""
    episodes = load_numogram_episodes()
    retronic = episodes[0]

    tdd_result = analyze_text(retronic.summary_text)

    # Should be CRITICAL due to eschatological + inverted + commanding combination
    assert tdd_result.sovereignty_risk == SovereigntyRisk.CRITICAL


def test_retronic_eschatological_mode():
    """Test that Retrónic episode triggers ESCHATOLOGICAL mode."""
    episodes = load_numogram_episodes()
    retronic = episodes[0]

    tdd_result = analyze_text(retronic.summary_text)

    # Should be ESCHATOLOGICAL due to eschaton/apocalypse/destiny terms
    assert tdd_result.temporal_mode == TemporalMode.ESCHATOLOGICAL


def test_build_numogram_casebook():
    """Test building complete Numogram casebook."""
    episodes = load_numogram_episodes()
    casebook = build_numogram_casebook(episodes)

    assert casebook.casebook_id == "NUMOGRAM_TT_CB"
    assert len(casebook.episodes) == 1
    assert len(casebook.trigger_lexicon) > 0

    # Check that all lexicon categories are present
    assert "retronic" in casebook.trigger_lexicon
    assert "eschatology" in casebook.trigger_lexicon
    assert "diagram_authority" in casebook.trigger_lexicon
    assert "agency" in casebook.trigger_lexicon


def test_provenance_complete():
    """Test that Retrónic episode has complete provenance."""
    episodes = load_numogram_episodes()
    retronic = episodes[0]

    prov = retronic.provenance

    assert len(prov.inputs) > 0
    assert prov.inputs[0].scheme == "fixture"
    assert len(prov.transforms) > 0
    assert prov.created_by == "numogram_corpus_loader"
    assert "token_count" in prov.metrics


def test_whitespace_normalization():
    """Test that whitespace is normalized in Retrónic episode."""
    episodes = load_numogram_episodes()
    retronic = episodes[0]

    # No double spaces
    assert "  " not in retronic.summary_text

    # No leading/trailing whitespace
    assert retronic.summary_text == retronic.summary_text.strip()


def test_phase_is_terminal():
    """Test that Retrónic episode is marked as terminal phase."""
    episodes = load_numogram_episodes()
    retronic = episodes[0]

    # Numogram episodes are terminal unfalsifiable closure
    assert retronic.phase == "unfalsifiable_closure"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
