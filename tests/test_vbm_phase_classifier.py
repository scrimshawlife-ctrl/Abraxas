"""Tests for VBM phase classification."""

import json
import pytest
from pathlib import Path

from abraxas.casebooks.vbm.corpus import load_episodes_from_fixtures
from abraxas.casebooks.vbm.models import VBMPhase
from abraxas.casebooks.vbm.phase import classify_phase, compute_phase_curve


@pytest.fixture
def expected_phases():
    """Load expected phase curve."""
    fixture_path = Path(__file__).parent / "fixtures" / "vbm" / "vbm_expected_phase_curve.json"
    with open(fixture_path, "r") as f:
        data = json.load(f)
    return {item["episode_id"]: item["phase"] for item in data["expected_phases"]}


def test_phase_classification_episode_01():
    """Test phase classification for episode 1 (math pattern)."""
    episodes = load_episodes_from_fixtures()
    ep1 = next(ep for ep in episodes if ep.episode_id == "vbm_01")

    phase, confidence = classify_phase(ep1.summary_text, ep1.extracted_tokens)

    # Should be math_pattern or representation_reduction
    assert phase in [VBMPhase.MATH_PATTERN, VBMPhase.REPRESENTATION_REDUCTION]
    assert confidence > 0.0


def test_phase_classification_episode_04():
    """Test phase classification for episode 4 (physics lexicon)."""
    episodes = load_episodes_from_fixtures()
    ep4 = next(ep for ep in episodes if ep.episode_id == "vbm_04")

    phase, confidence = classify_phase(ep4.summary_text, ep4.extracted_tokens)

    # Should be physics_lexicon_injection
    assert phase == VBMPhase.PHYSICS_LEXICON_INJECTION
    assert confidence > 0.0


def test_phase_classification_episode_05():
    """Test phase classification for episode 5 (consciousness)."""
    episodes = load_episodes_from_fixtures()
    ep5 = next(ep for ep in episodes if ep.episode_id == "vbm_05")

    phase, confidence = classify_phase(ep5.summary_text, ep5.extracted_tokens)

    # Should be consciousness_attribution
    assert phase == VBMPhase.CONSCIOUSNESS_ATTRIBUTION
    assert confidence > 0.0


def test_phase_classification_episode_07():
    """Test phase classification for episode 7 (unfalsifiable closure)."""
    episodes = load_episodes_from_fixtures()
    ep7 = next(ep for ep in episodes if ep.episode_id == "vbm_07")

    phase, confidence = classify_phase(ep7.summary_text, ep7.extracted_tokens)

    # Should be unfalsifiable_closure
    assert phase == VBMPhase.UNFALSIFIABLE_CLOSURE
    assert confidence > 0.0


def test_phase_curve_matches_expected(expected_phases):
    """Test that phase curve matches expected curve."""
    episodes = load_episodes_from_fixtures()
    phase_curve = compute_phase_curve(episodes)

    # Check that we have 7 phases
    assert len(phase_curve) == 7

    # Check against expected (allowing some tolerance)
    matches = 0
    for item in phase_curve:
        episode_id = item["episode_id"]
        detected_phase = item["phase"]
        expected_phase = expected_phases.get(episode_id)

        if detected_phase == expected_phase:
            matches += 1

    # At least 5 out of 7 should match
    assert matches >= 5, f"Only {matches}/7 phases matched expected curve"


def test_phase_curve_deterministic():
    """Test that phase curve is deterministic."""
    episodes = load_episodes_from_fixtures()

    curve1 = compute_phase_curve(episodes)
    curve2 = compute_phase_curve(episodes)

    assert len(curve1) == len(curve2)

    for item1, item2 in zip(curve1, curve2):
        assert item1["episode_id"] == item2["episode_id"]
        assert item1["phase"] == item2["phase"]
        assert item1["confidence"] == item2["confidence"]


def test_phase_escalation():
    """Test that phases generally escalate in severity."""
    episodes = load_episodes_from_fixtures()
    phase_curve = compute_phase_curve(episodes)

    # Phase weights should generally increase
    weights = [item["weight"] for item in phase_curve]

    # Check that later episodes have higher or equal weights
    # (allowing some variation)
    early_avg = sum(weights[:3]) / 3
    late_avg = sum(weights[4:]) / 3

    assert late_avg >= early_avg, "Later episodes should have higher phase weights"


def test_confidence_ranges():
    """Test that all confidences are in valid range."""
    episodes = load_episodes_from_fixtures()

    for episode in episodes:
        phase, confidence = classify_phase(episode.summary_text, episode.extracted_tokens)

        assert 0.0 <= confidence <= 1.0, f"{episode.episode_id} has invalid confidence: {confidence}"


def test_empty_text_classification():
    """Test classification of empty text."""
    phase, confidence = classify_phase("")

    # Should return default phase with zero confidence
    assert phase == VBMPhase.MATH_PATTERN
    assert confidence == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
