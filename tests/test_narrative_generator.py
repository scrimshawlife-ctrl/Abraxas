from abraxas.core.provenance import Provenance
from abraxas.narratives.generator import NarrativeGenerator
from abraxas.phase.early_warning import PhaseTransitionWarning


def _warning(observation_count):
    return PhaseTransitionWarning(
        warning_id="WARN-1",
        domain="politics",
        current_phase="seed",
        predicted_phase="emergence",
        estimated_hours=18.0,
        confidence=0.72,
        trigger_signals=("tau_velocity",),
        evidence={"observation_count": observation_count},
        issued_utc="2026-01-01T00:00:00Z",
        provenance=Provenance(
            run_id="RUN-1",
            started_at_utc="2026-01-01T00:00:00Z",
            inputs_hash="a" * 64,
            config_hash="b" * 64,
        ),
    )


def test_generate_phase_transition_narrative_uses_integer_observation_count():
    generator = NarrativeGenerator()
    narrative = generator.generate_phase_transition_narrative(_warning(12), run_id="TEST")

    assert "**Token Count:** 12" in narrative.content
    assert narrative.narrative_id == "NARR-PHASE-WARN-1"


def test_generate_phase_transition_narrative_defaults_non_integer_observation_count_to_zero():
    generator = NarrativeGenerator()
    narrative = generator.generate_phase_transition_narrative(_warning(["x", "y"]), run_id="TEST")

    assert "**Token Count:** 0" in narrative.content


def test_generate_phase_transition_narrative_treats_boolean_count_as_zero():
    generator = NarrativeGenerator()
    narrative = generator.generate_phase_transition_narrative(_warning(True), run_id="TEST")

    assert "**Token Count:** 0" in narrative.content


def test_generate_phase_transition_narrative_clamps_negative_count_to_zero():
    generator = NarrativeGenerator()
    narrative = generator.generate_phase_transition_narrative(_warning(-4), run_id="TEST")

    assert "**Token Count:** 0" in narrative.content
