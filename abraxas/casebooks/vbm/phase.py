"""VBM phase classification using deterministic rule-based approach."""

from __future__ import annotations

from abraxas.casebooks.vbm.models import VBMPhase
from abraxas.casebooks.vbm.corpus import TRIGGER_LEXICON


# Phase weights (higher = more severe escalation)
PHASE_WEIGHTS = {
    VBMPhase.MATH_PATTERN: 1.0,
    VBMPhase.REPRESENTATION_REDUCTION: 2.0,
    VBMPhase.CROSS_DOMAIN_ANALOGY: 3.0,
    VBMPhase.PHYSICS_LEXICON_INJECTION: 4.0,
    VBMPhase.CONSCIOUSNESS_ATTRIBUTION: 5.0,
    VBMPhase.UNFALSIFIABLE_CLOSURE: 6.0,
}


def classify_phase(text: str, extracted_tokens: dict[str, int] | None = None) -> tuple[VBMPhase, float]:
    """
    Classify text into VBM phase using deterministic lexeme-based rules.

    Args:
        text: Text to classify
        extracted_tokens: Optional pre-extracted token counts

    Returns:
        (phase, confidence) tuple where confidence is in [0, 1]
    """
    text_lower = text.lower()

    # Extract tokens if not provided
    if extracted_tokens is None:
        from abraxas.casebooks.vbm.corpus import _extract_tokens

        extracted_tokens = _extract_tokens(text)

    # Count hits per phase
    phase_scores: dict[VBMPhase, float] = {phase: 0.0 for phase in VBMPhase}

    for phase, lexemes in TRIGGER_LEXICON.items():
        hits = 0
        for lexeme in lexemes:
            if lexeme in extracted_tokens:
                hits += extracted_tokens[lexeme]

        # Normalize by lexeme group size
        if lexemes:
            phase_scores[phase] = hits / len(lexemes)

    # Find phase with highest score
    max_phase = VBMPhase.MATH_PATTERN
    max_score = 0.0

    for phase, score in phase_scores.items():
        if score > max_score:
            max_score = score
            max_phase = phase

    # Compute confidence based on margin and absolute score
    total_score = sum(phase_scores.values())
    if total_score == 0:
        # No lexeme hits at all
        return VBMPhase.MATH_PATTERN, 0.0

    # Confidence = (max_score / total_score) * min(1.0, max_score)
    confidence = (max_score / total_score) * min(1.0, max_score)

    return max_phase, confidence


def classify_episode(episode_text: str) -> tuple[VBMPhase, float]:
    """
    Classify a full episode into a phase.

    This is a convenience wrapper around classify_phase.
    """
    return classify_phase(episode_text)


def compute_phase_curve(episodes: list) -> list[dict[str, any]]:
    """
    Compute phase curve for all episodes.

    Args:
        episodes: List of VBMEpisode objects

    Returns:
        List of dicts with episode_id, phase, confidence
    """
    curve = []

    for episode in episodes:
        phase, confidence = classify_phase(
            episode.summary_text, episode.extracted_tokens
        )

        curve.append(
            {
                "episode_id": episode.episode_id,
                "phase": phase.value,
                "confidence": confidence,
                "weight": PHASE_WEIGHTS[phase],
            }
        )

    # Sort by episode_id for determinism
    curve.sort(key=lambda x: x["episode_id"])

    return curve
