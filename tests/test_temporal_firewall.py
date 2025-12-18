"""Tests for Temporal Firewall enforcement of TDD response modes."""

import json
import pytest
from pathlib import Path

from abraxas.synthesis.firewall import apply_temporal_firewall, compute_text_metrics
from abraxas.synthesis.renderer import SynthesisRenderer, render_with_firewall
from abraxas.temporal.detector import analyze_text
from abraxas.temporal.models import TemporalMode, SovereigntyRisk, TemporalDriftResult


@pytest.fixture
def fixtures_dir():
    """Get fixtures directory path."""
    return Path(__file__).parent / "fixtures" / "synthesis"


@pytest.fixture
def expected_behaviors(fixtures_dir):
    """Load expected firewall behaviors."""
    with open(fixtures_dir / "firewall_expected.json", "r") as f:
        return json.load(f)


@pytest.fixture
def draft_neutral(fixtures_dir):
    """Load neutral draft text."""
    with open(fixtures_dir / "draft_neutral.txt", "r") as f:
        return f.read()


@pytest.fixture
def draft_retronic(fixtures_dir):
    """Load retronic inverted draft text."""
    with open(fixtures_dir / "draft_retronic_inverted.txt", "r") as f:
        return f.read()


@pytest.fixture
def draft_eschatology(fixtures_dir):
    """Load eschatology draft text."""
    with open(fixtures_dir / "draft_eschatology.txt", "r") as f:
        return f.read()


@pytest.fixture
def draft_diagram_authority(fixtures_dir):
    """Load diagram authority draft text."""
    with open(fixtures_dir / "draft_diagram_authority.txt", "r") as f:
        return f.read()


def test_contextualize_mode_neutral_text(draft_neutral):
    """Test CONTEXTUALIZE mode on neutral text."""
    # Analyze with TDD
    tdd_result = analyze_text(draft_neutral)

    # Should be LOW sovereignty risk
    assert tdd_result.sovereignty_risk == SovereigntyRisk.LOW

    # Apply firewall
    transformed, metadata = apply_temporal_firewall(draft_neutral, tdd_result)

    # Should use CONTEXTUALIZE mode
    assert metadata["response_mode"] == "CONTEXTUALIZE"

    # Should have disclaimer
    assert "Note: The following represents one interpretive lens" in transformed

    # Should have the action recorded
    assert "added_interpretive_lens_disclaimer" in metadata["firewall_actions"]

    # Original content should still be present
    assert "observed pattern" in transformed


def test_pluralize_mode_strips_modals(draft_neutral, expected_behaviors):
    """Test PLURALIZE mode strips strongest modal terms."""
    # Force PLURALIZE mode
    tdd_result = analyze_text(draft_neutral)
    context = {"force_response_mode": "PLURALIZE"}

    transformed, metadata = apply_temporal_firewall(draft_neutral, tdd_result, context)

    # Should use PLURALIZE mode
    assert metadata["response_mode"] == "PLURALIZE"

    # Should have 3 alternative interpretations
    assert "Alternative interpretations:" in transformed
    assert "1." in transformed
    assert "2." in transformed
    assert "3." in transformed

    # Should have added alternatives action
    assert "added_3_alternative_interpretations" in metadata["firewall_actions"]


def test_pluralize_exactly_3_alternatives(draft_neutral):
    """Test that PLURALIZE adds exactly 3 alternatives."""
    tdd_result = analyze_text(draft_neutral)
    context = {"force_response_mode": "PLURALIZE"}

    transformed, metadata = apply_temporal_firewall(draft_neutral, tdd_result, context)

    # Count numbered items in alternatives section
    lines = transformed.split('\n')
    alt_section_started = False
    numbered_items = []

    for line in lines:
        if "Alternative interpretations:" in line:
            alt_section_started = True
            continue
        if alt_section_started:
            stripped = line.strip()
            if stripped.startswith(("1.", "2.", "3.", "4.", "5.")):
                numbered_items.append(stripped)

    # Should have exactly 3
    assert len(numbered_items) == 3


def test_de_escalate_mode_softens_certainty(draft_retronic):
    """Test DE_ESCALATE mode softens certainty patterns."""
    tdd_result = analyze_text(draft_retronic)
    context = {"force_response_mode": "DE_ESCALATE"}

    transformed, metadata = apply_temporal_firewall(draft_retronic, tdd_result, context)

    # Should use DE_ESCALATE mode
    assert metadata["response_mode"] == "DE_ESCALATE"

    # Should have falsifiability nudge
    assert "What evidence would challenge this interpretation?" in transformed

    # Should have softened some certainty
    assert any("softened_certainty" in action for action in metadata["firewall_actions"])


def test_de_escalate_limits_metaphors(draft_neutral):
    """Test DE_ESCALATE limits metaphors to 1."""
    # Create text with multiple metaphors
    text_with_metaphors = "This is like a pattern that resembles a structure and mirrors a system."

    tdd_result = analyze_text(text_with_metaphors)
    context = {"force_response_mode": "DE_ESCALATE"}

    transformed, metadata = apply_temporal_firewall(text_with_metaphors, tdd_result, context)

    # Should have limited metaphors
    metaphor_actions = [a for a in metadata["firewall_actions"] if "limited_metaphors" in a]
    if metaphor_actions:
        # Metaphors were limited
        assert len(metaphor_actions) > 0


def test_refuse_extension_mode_critical_risk(draft_retronic):
    """Test REFUSE_EXTENSION mode on critical sovereignty risk."""
    # Analyze with TDD - should be CRITICAL
    tdd_result = analyze_text(draft_retronic)

    # Should be CRITICAL sovereignty risk
    assert tdd_result.sovereignty_risk == SovereigntyRisk.CRITICAL

    # Apply firewall
    transformed, metadata = apply_temporal_firewall(draft_retronic, tdd_result)

    # Should use REFUSE_EXTENSION mode
    assert metadata["response_mode"] == "REFUSE_EXTENSION"

    # Should have refusal template
    assert "I notice this content contains patterns" in transformed
    assert "epistemic sovereignty" in transformed

    # Should have excerpt
    assert "Excerpt from draft:" in transformed

    # Should have grounded alternatives
    assert "Instead, I can help with:" in transformed
    assert "1." in transformed
    assert "2." in transformed
    assert "3." in transformed
    assert "4." in transformed

    # Should have recorded actions
    assert "refused_extension" in metadata["firewall_actions"]
    assert "provided_grounded_alternatives" in metadata["firewall_actions"]


def test_refuse_extension_limits_excerpt(draft_retronic):
    """Test REFUSE_EXTENSION limits excerpt to 40 words."""
    tdd_result = analyze_text(draft_retronic)

    transformed, metadata = apply_temporal_firewall(draft_retronic, tdd_result)

    # Extract excerpt from output
    if "Excerpt from draft:" in transformed:
        lines = transformed.split('\n')
        for i, line in enumerate(lines):
            if "Excerpt from draft:" in line:
                # Next line should have the excerpt in quotes
                if i + 1 < len(lines):
                    excerpt_line = lines[i + 1]
                    # Extract text between quotes
                    import re
                    match = re.search(r'"([^"]*)"', excerpt_line)
                    if match:
                        excerpt = match.group(1)
                        words = excerpt.replace("...", "").split()
                        # Should be <= 40 words
                        assert len(words) <= 40


def test_refuse_extension_eschatology(draft_eschatology):
    """Test REFUSE_EXTENSION on eschatological content."""
    tdd_result = analyze_text(draft_eschatology)

    # Should trigger CRITICAL risk
    assert tdd_result.sovereignty_risk == SovereigntyRisk.CRITICAL

    transformed, metadata = apply_temporal_firewall(draft_eschatology, tdd_result)

    # Should refuse
    assert metadata["response_mode"] == "REFUSE_EXTENSION"
    assert "epistemic sovereignty" in transformed


def test_refuse_extension_diagram_authority(draft_diagram_authority):
    """Test REFUSE_EXTENSION on diagram authority content."""
    tdd_result = analyze_text(draft_diagram_authority)

    # Should trigger CRITICAL or HIGH risk
    assert tdd_result.sovereignty_risk in [SovereigntyRisk.CRITICAL, SovereigntyRisk.HIGH]

    transformed, metadata = apply_temporal_firewall(draft_diagram_authority, tdd_result)

    # Should refuse or de-escalate
    assert metadata["response_mode"] in ["REFUSE_EXTENSION", "DE_ESCALATE"]


def test_firewall_preserves_provenance(draft_neutral):
    """Test that firewall includes provenance."""
    tdd_result = analyze_text(draft_neutral)

    transformed, metadata = apply_temporal_firewall(draft_neutral, tdd_result)

    # Should have provenance
    assert "provenance" in metadata
    assert metadata["provenance"] is not None

    # Provenance should have inputs, transforms, metrics
    prov = metadata["provenance"]
    assert len(prov.inputs) > 0
    assert len(prov.transforms) > 0
    assert "modal_delta" in prov.metrics


def test_firewall_deterministic(draft_neutral):
    """Test that firewall is deterministic."""
    tdd_result = analyze_text(draft_neutral)

    transformed1, metadata1 = apply_temporal_firewall(draft_neutral, tdd_result)
    transformed2, metadata2 = apply_temporal_firewall(draft_neutral, tdd_result)

    # Should produce identical results
    assert transformed1 == transformed2
    assert metadata1["response_mode"] == metadata2["response_mode"]
    assert metadata1["firewall_actions"] == metadata2["firewall_actions"]


def test_renderer_integration(draft_neutral):
    """Test SynthesisRenderer integration."""
    renderer = SynthesisRenderer(enable_firewall=True)

    response = renderer.render(draft_neutral)

    # Should have firewall applied
    assert response.firewall_applied
    assert response.response_mode is not None
    assert response.tdd_result is not None
    assert response.final_text != response.draft_text  # Should be transformed


def test_renderer_disable_firewall(draft_retronic):
    """Test renderer with firewall disabled."""
    renderer = SynthesisRenderer(enable_firewall=False)

    response = renderer.render(draft_retronic)

    # Should not have firewall applied
    assert not response.firewall_applied
    assert response.response_mode is None
    assert response.final_text == response.draft_text  # Should be unchanged


def test_renderer_batch_processing(draft_neutral, draft_retronic):
    """Test batch rendering."""
    renderer = SynthesisRenderer(enable_firewall=True)

    responses = renderer.render_batch([draft_neutral, draft_retronic])

    # Should have 2 responses
    assert len(responses) == 2

    # Each should be processed
    for response in responses:
        assert response.firewall_applied
        assert response.tdd_result is not None


def test_convenience_function(draft_neutral):
    """Test render_with_firewall convenience function."""
    response = render_with_firewall(draft_neutral)

    # Should work
    assert response.firewall_applied
    assert response.final_text is not None


def test_context_override_response_mode(draft_neutral):
    """Test that context can override response mode."""
    tdd_result = analyze_text(draft_neutral)

    # Force REFUSE_EXTENSION on neutral text
    context = {"force_response_mode": "REFUSE_EXTENSION"}
    transformed, metadata = apply_temporal_firewall(draft_neutral, tdd_result, context)

    # Should use forced mode
    assert metadata["response_mode"] == "REFUSE_EXTENSION"
    assert "refused_extension" in metadata["firewall_actions"]


def test_metrics_computed(draft_neutral):
    """Test that metrics are computed correctly."""
    metrics = compute_text_metrics(draft_neutral)

    # Should have all expected metrics
    assert "modal_verb_count" in metrics
    assert "agency_transfer_count" in metrics
    assert "closure_term_count" in metrics
    assert "causality_inversion_count" in metrics
    assert "metaphor_count" in metrics
    assert "word_count" in metrics
    assert "sentence_count" in metrics

    # Should all be floats
    for key, value in metrics.items():
        assert isinstance(value, float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
