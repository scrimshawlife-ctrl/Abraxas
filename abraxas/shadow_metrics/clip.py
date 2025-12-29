"""CLIP - Cognitive Load Intensity Proxy.

Estimates cognitive processing burden on audience.

INTERNAL USE ONLY - Access via ABX-Runes ϟ₇ operator only.
"""

from __future__ import annotations

import re
from typing import Any


def extract_inputs(context: dict[str, Any]) -> dict[str, Any]:
    """Extract CLIP-specific inputs from context.

    Args:
        context: Computation context from rune invocation

    Returns:
        Inputs dict with text complexity metrics
    """
    symbol_pool = context.get("symbol_pool", [])

    # Extract text from symbol pool
    texts = []
    for event in symbol_pool:
        text = event.get("text", "") or event.get("content", "")
        if text:
            texts.append(text)

    # Aggregate text
    full_text = " ".join(texts)

    return {
        "text": full_text,
        "sample_count": len(texts),
    }


def get_default_config() -> dict[str, Any]:
    """Get default CLIP configuration.

    Returns:
        Config dict with weight parameters
    """
    return {
        "w1_complexity": 0.4,
        "w2_density": 0.3,
        "w3_novelty": 0.3,
        "flesch_kincaid_max": 18.0,  # Grade 18 = max complexity
        "bits_per_token_max": 10.0,  # Max information density
    }


def compute_flesch_kincaid(text: str) -> float:
    """Compute Flesch-Kincaid grade level.

    Simplified formula:
    FK = 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59

    Args:
        text: Input text

    Returns:
        Grade level (higher = more complex)
    """
    if not text:
        return 0.0

    # Count sentences (naive: split on .!?)
    sentences = len(re.split(r"[.!?]+", text))
    sentences = max(1, sentences)

    # Count words
    words = len(text.split())
    if words == 0:
        return 0.0

    # Count syllables (very naive: count vowel groups)
    syllables = len(re.findall(r"[aeiouy]+", text.lower()))
    syllables = max(words, syllables)  # At least one syllable per word

    # Flesch-Kincaid formula
    fk = 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59

    return max(0.0, fk)


def compute_information_density(text: str) -> float:
    """Compute information density (bits per token).

    Simplified: Use unique token ratio as proxy.

    Args:
        text: Input text

    Returns:
        Bits per token estimate
    """
    if not text:
        return 0.0

    tokens = text.lower().split()
    if not tokens:
        return 0.0

    unique_ratio = len(set(tokens)) / len(tokens)

    # Map to bits (higher unique ratio = more info per token)
    bits_per_token = unique_ratio * 10.0

    return bits_per_token


def compute_novelty(text: str) -> float:
    """Compute novelty score (proportion of low-frequency tokens).

    Simplified: Use token length as proxy for rarity.
    Longer tokens tend to be less frequent.

    Args:
        text: Input text

    Returns:
        Novelty score [0.0, 1.0]
    """
    if not text:
        return 0.0

    tokens = text.split()
    if not tokens:
        return 0.0

    # Tokens > 8 chars are considered "novel"
    novel_count = sum(1 for t in tokens if len(t) > 8)

    novelty = novel_count / len(tokens)

    return novelty


def compute(inputs: dict[str, Any], config: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """Compute CLIP value.

    CLIP = w1*complexity + w2*density + w3*novelty

    Args:
        inputs: Text data
        config: Configuration parameters

    Returns:
        Tuple of (CLIP value [0.0, 1.0], metadata dict)
    """
    text = inputs["text"]

    # Handle edge case: no text
    if not text:
        return 0.0, {
            "complexity_score": 0.0,
            "density_score": 0.0,
            "novelty_score": 0.0,
            "weights": {
                "w1": config["w1_complexity"],
                "w2": config["w2_density"],
                "w3": config["w3_novelty"],
            },
        }

    # Compute component scores
    fk = compute_flesch_kincaid(text)
    density = compute_information_density(text)
    novelty = compute_novelty(text)

    # Normalize to [0, 1]
    complexity_norm = min(1.0, fk / config["flesch_kincaid_max"])
    density_norm = min(1.0, density / config["bits_per_token_max"])
    novelty_norm = novelty  # Already in [0, 1]

    # Weighted combination
    w1 = config["w1_complexity"]
    w2 = config["w2_density"]
    w3 = config["w3_novelty"]

    clip = w1 * complexity_norm + w2 * density_norm + w3 * novelty_norm

    # Clamp to [0, 1]
    clip = max(0.0, min(1.0, clip))

    metadata = {
        "complexity_score": fk,
        "density_score": density,
        "novelty_score": novelty,
        "weights": {"w1": w1, "w2": w2, "w3": w3},
        "normalized_components": {
            "complexity": complexity_norm,
            "density": density_norm,
            "novelty": novelty_norm,
        },
    }

    return clip, metadata
