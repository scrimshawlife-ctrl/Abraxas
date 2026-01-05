"""Rune adapter for forecast scoring capabilities.

Thin adapter layer exposing forecast.scoring via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.forecast.scoring import brier_score as brier_score_core
from abraxas.forecast.scoring import expected_error_band as expected_error_band_core


def compute_brier_score_deterministic(
    probs: List[float],
    outcomes: List[int],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible Brier score calculator.

    Wraps existing brier_score with provenance envelope and validation.

    Args:
        probs: List of predicted probabilities [0, 1]
        outcomes: List of binary outcomes (0 or 1)
        seed: Optional deterministic seed (unused for brier score, but kept for consistency)

    Returns:
        Dictionary with brier_score, provenance, and optionally not_computable
    """
    # Validate inputs
    if not probs or not outcomes:
        return {
            "brier_score": None,
            "not_computable": {
                "reason": "Empty probs or outcomes list",
                "missing_inputs": ["probs" if not probs else "", "outcomes" if not outcomes else ""]
            },
            "provenance": None
        }

    if len(probs) != len(outcomes):
        return {
            "brier_score": None,
            "not_computable": {
                "reason": f"Length mismatch: {len(probs)} probs vs {len(outcomes)} outcomes",
                "missing_inputs": []
            },
            "provenance": None
        }

    # Call existing brier_score function (no changes to core logic)
    try:
        score = brier_score_core(probs=probs, outcomes=outcomes)
    except Exception as e:
        # Not computable - return structured error
        return {
            "brier_score": None,
            "not_computable": {
                "reason": str(e),
                "missing_inputs": []
            },
            "provenance": None
        }

    # Check for NaN result
    import math
    if math.isnan(score):
        return {
            "brier_score": None,
            "not_computable": {
                "reason": "Brier score computation returned NaN",
                "missing_inputs": []
            },
            "provenance": None
        }

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"brier_score": score},
        config={},
        inputs={"probs": probs, "outcomes": outcomes},
        operation_id="forecast.scoring.brier",
        seed=seed
    )

    # Return with renamed key for clarity
    return {
        "brier_score": score,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"]
    }


def compute_expected_error_band_deterministic(
    horizon: str,
    phase: str,
    half_life_days: float,
    manipulation_risk: float,
    recurrence_days: Optional[float] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible Expected Error Band calculator.

    Wraps existing expected_error_band with provenance envelope.

    Args:
        horizon: Horizon band (days, weeks, months, years_1, years_5)
        phase: Lifecycle phase
        half_life_days: Half-life in days
        manipulation_risk: Manipulation risk score [0, 1]
        recurrence_days: Optional recurrence period in days
        seed: Optional deterministic seed (unused, kept for consistency)

    Returns:
        Dictionary with error_band, provenance, and optionally not_computable
    """
    # Call existing expected_error_band function
    try:
        band = expected_error_band_core(
            horizon=horizon,
            phase=phase,
            half_life_days=half_life_days,
            manipulation_risk=manipulation_risk,
            recurrence_days=recurrence_days
        )
    except Exception as e:
        # Not computable - return structured error
        return {
            "error_band": None,
            "not_computable": {
                "reason": str(e),
                "missing_inputs": []
            },
            "provenance": None
        }

    # Convert to dict
    band_dict = band.to_dict()

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result=band_dict,
        config={},
        inputs={
            "horizon": horizon,
            "phase": phase,
            "half_life_days": half_life_days,
            "manipulation_risk": manipulation_risk,
            "recurrence_days": recurrence_days
        },
        operation_id="forecast.scoring.expected_error_band",
        seed=seed
    )

    # Return with renamed key for clarity
    return {
        "error_band": band_dict,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"]
    }


__all__ = [
    "compute_brier_score_deterministic",
    "compute_expected_error_band_deterministic"
]
