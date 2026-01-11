"""
Token Density Detector — Example using new util helpers.

Demonstrates the canonical pattern for shadow detectors using:
- ok(value, provenance) for successful computation
- not_computable(missing) for missing inputs
- err(message) for errors

This is a simple detector that computes token density metrics:
- tokens_per_100_chars: token density measure
- unique_ratio: unique tokens / total tokens
- avg_token_length: average token length

Shadow-only: feeds into observation metrics, does NOT influence prediction.
"""

from __future__ import annotations

from typing import Any, Dict
import re

from abraxas.detectors.shadow.util import ok, not_computable, err
from abraxas.detectors.shadow.types import ShadowResult


DETECTOR_VERSION = "0.1.0"


def run_token_density(ctx: Dict[str, Any]) -> ShadowResult:
    """
    Compute token density metrics from text.

    Args:
        ctx: Context dict with:
            - text: str (required) - text to analyze

    Returns:
        ShadowResult with status and value/missing/error as appropriate
    """
    # Check for required input
    text = ctx.get("text")
    if text is None:
        return not_computable(["text"])

    # Validate input type
    if not isinstance(text, str):
        return err(f"Expected text to be str, got {type(text).__name__}")

    # Handle empty text
    text = text.strip()
    if not text:
        return not_computable(["text"], provenance={"reason": "empty_text"})

    try:
        # Tokenize (simple whitespace + punctuation split)
        tokens = re.findall(r'\b\w+\b', text.lower())

        if not tokens:
            return ok(
                {
                    "tokens_per_100_chars": 0.0,
                    "unique_ratio": 0.0,
                    "avg_token_length": 0.0,
                    "token_count": 0,
                    "char_count": len(text),
                },
                provenance={"version": DETECTOR_VERSION, "note": "no_tokens_found"},
            )

        # Compute metrics
        char_count = len(text)
        token_count = len(tokens)
        unique_tokens = set(tokens)
        unique_count = len(unique_tokens)

        tokens_per_100_chars = (token_count / char_count) * 100.0 if char_count > 0 else 0.0
        unique_ratio = unique_count / token_count if token_count > 0 else 0.0
        avg_token_length = sum(len(t) for t in tokens) / token_count if token_count > 0 else 0.0

        return ok(
            {
                "tokens_per_100_chars": round(tokens_per_100_chars, 4),
                "unique_ratio": round(unique_ratio, 4),
                "avg_token_length": round(avg_token_length, 4),
                "token_count": token_count,
                "unique_count": unique_count,
                "char_count": char_count,
            },
            provenance={"version": DETECTOR_VERSION},
        )

    except Exception as e:
        return err(f"Computation failed: {type(e).__name__}: {e}")


__all__ = ["run_token_density", "DETECTOR_VERSION"]
