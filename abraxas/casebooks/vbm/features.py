"""VBM feature extraction for drift scoring."""

from __future__ import annotations

import re
from abraxas.casebooks.vbm.corpus import TRIGGER_LEXICON


def extract_vbm_features(text: str) -> dict[str, float]:
    """
    Extract VBM-relevant features from text.

    Returns normalized feature dict with values in [0, 1] range.
    """
    text_lower = text.lower()
    tokens = text.split()
    token_count = max(len(tokens), 1)  # Avoid division by zero

    features = {}

    # Lexeme hit density (normalized by text length)
    total_lexeme_hits = 0
    for phase_lexemes in TRIGGER_LEXICON.values():
        for lexeme in phase_lexemes:
            total_lexeme_hits += text_lower.count(lexeme.lower())

    features["lexeme_density"] = min(1.0, total_lexeme_hits / token_count)

    # Analogy density (cross-domain words / tokens)
    analogy_terms = TRIGGER_LEXICON.get("cross_domain_analogy", [])
    analogy_hits = sum(text_lower.count(term.lower()) for term in analogy_terms)
    features["analogy_density"] = min(1.0, analogy_hits / token_count)

    # Reduction language proxy
    reduction_terms = TRIGGER_LEXICON.get("representation_reduction", [])
    reduction_hits = sum(text_lower.count(term.lower()) for term in reduction_terms)
    features["reduction_language"] = min(1.0, reduction_hits / token_count)

    # Closure language proxy
    closure_terms = TRIGGER_LEXICON.get("unfalsifiable_closure", [])
    closure_hits = sum(text_lower.count(term.lower()) for term in closure_terms)
    features["closure_language"] = min(1.0, closure_hits / token_count)

    # Physics lexicon density
    physics_terms = TRIGGER_LEXICON.get("physics_lexicon_injection", [])
    physics_hits = sum(text_lower.count(term.lower()) for term in physics_terms)
    features["physics_lexicon"] = min(1.0, physics_hits / token_count)

    # Consciousness attribution
    consciousness_terms = TRIGGER_LEXICON.get("consciousness_attribution", [])
    consciousness_hits = sum(text_lower.count(term.lower()) for term in consciousness_terms)
    features["consciousness_attribution"] = min(1.0, consciousness_hits / token_count)

    # Pattern language (baseline)
    pattern_terms = TRIGGER_LEXICON.get("math_pattern", [])
    pattern_hits = sum(text_lower.count(term.lower()) for term in pattern_terms)
    features["pattern_language"] = min(1.0, pattern_hits / token_count)

    return features


def compute_escalation_score(features: dict[str, float]) -> float:
    """
    Compute escalation score from features.

    Higher-phase features are weighted more heavily.
    """
    weights = {
        "pattern_language": 1.0,
        "reduction_language": 2.0,
        "analogy_density": 3.0,
        "physics_lexicon": 4.0,
        "consciousness_attribution": 5.0,
        "closure_language": 6.0,
    }

    weighted_sum = 0.0
    weight_total = 0.0

    for feature, value in features.items():
        weight = weights.get(feature, 1.0)
        weighted_sum += value * weight
        weight_total += weight

    if weight_total == 0:
        return 0.0

    # Normalize to [0, 1]
    return min(1.0, weighted_sum / weight_total)
