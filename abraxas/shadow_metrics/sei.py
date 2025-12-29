"""SEI - Sentiment Entropy Index.

Measures emotional volatility and sentiment manipulation potential.

INTERNAL USE ONLY - Access via ABX-Runes ϟ₇ operator only.
"""

from __future__ import annotations

import math
from typing import Any


def extract_inputs(context: dict[str, Any]) -> dict[str, Any]:
    """Extract SEI-specific inputs from context.

    Args:
        context: Computation context from rune invocation

    Returns:
        Inputs dict with sentiment distribution
    """
    symbol_pool = context.get("symbol_pool", [])

    # Extract sentiment counts from symbol pool
    # Each symbol event may have sentiment annotation
    positive = 0
    negative = 0
    neutral = 0

    for event in symbol_pool:
        sentiment = event.get("sentiment", "neutral")
        if sentiment == "positive":
            positive += 1
        elif sentiment == "negative":
            negative += 1
        else:
            neutral += 1

    return {
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "total": positive + negative + neutral,
    }


def get_default_config() -> dict[str, Any]:
    """Get default SEI configuration.

    Returns:
        Config dict with normalization parameters
    """
    return {
        "normalization_method": "shannon_entropy_trimodal",
        "max_entropy": math.log(3),  # log(3) for 3 sentiment classes
    }


def compute(inputs: dict[str, Any], config: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """Compute SEI value.

    SEI = H(p_positive, p_negative, p_neutral) / log(3)

    where H = Shannon entropy

    Args:
        inputs: Sentiment distribution
        config: Configuration parameters

    Returns:
        Tuple of (SEI value [0.0, 1.0], metadata dict)
    """
    total = inputs["total"]

    # Handle edge case: no data
    if total == 0:
        return 0.0, {
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
            "total_samples": 0,
            "normalization_method": config["normalization_method"],
            "entropy_raw": 0.0,
        }

    # Compute probabilities
    p_pos = inputs["positive"] / total
    p_neg = inputs["negative"] / total
    p_neu = inputs["neutral"] / total

    # Compute Shannon entropy
    # H = -Σ(p_i * log(p_i)) for p_i > 0
    entropy = 0.0
    for p in [p_pos, p_neg, p_neu]:
        if p > 0:
            entropy -= p * math.log(p)

    # Normalize by max entropy (log(3))
    sei = entropy / config["max_entropy"]

    # Clamp to [0, 1] for safety
    sei = max(0.0, min(1.0, sei))

    metadata = {
        "sentiment_distribution": {
            "positive": inputs["positive"],
            "negative": inputs["negative"],
            "neutral": inputs["neutral"],
        },
        "total_samples": total,
        "normalization_method": config["normalization_method"],
        "entropy_raw": entropy,
        "probabilities": {"p_positive": p_pos, "p_negative": p_neg, "p_neutral": p_neu},
    }

    return sei, metadata
