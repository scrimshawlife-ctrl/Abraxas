"""Rune adapter for forecast term classification capability.

Thin adapter layer exposing forecast.term.classify via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.forecast.term_classify import classify_term as classify_term_core


def classify_term_deterministic(
    profile: Dict[str, Any],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible term classification.

    Wraps existing classify_term with provenance envelope.

    Args:
        profile: A2 profile dict with classification fields
        seed: Optional deterministic seed (kept for consistency)

    Returns:
        Dictionary with classification, success status, and provenance
    """
    # Validate inputs
    if not isinstance(profile, dict):
        return {
            "success": False,
            "classification": None,
            "not_computable": {
                "reason": "Invalid profile: expected dict",
                "missing_inputs": ["profile"]
            },
            "provenance": None
        }

    # Call existing classify_term function (pure, deterministic)
    try:
        classification = classify_term_core(profile)
    except Exception as e:
        # Not computable - return structured error
        return {
            "success": False,
            "classification": None,
            "not_computable": {
                "reason": str(e),
                "missing_inputs": []
            },
            "provenance": None
        }

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"success": True, "classification": classification},
        config={},
        inputs={"profile": profile},
        operation_id="forecast.term.classify",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "success": True,
        "classification": classification,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"]
    }


__all__ = ["classify_term_deterministic"]
