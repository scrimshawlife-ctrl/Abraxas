"""Rune adapter for forecast capabilities.

Thin adapter layer exposing forecast.* modules via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.forecast.scoring import brier_score as brier_score_core
from abraxas.forecast.scoring import expected_error_band as expected_error_band_core
from abraxas.forecast.horizon_bins import horizon_bucket as horizon_bucket_core
from abraxas.forecast.term_classify import classify_term as classify_term_core
from abraxas.forecast.term_class_map import load_term_class_map as load_term_class_map_core
from abraxas.forecast.gating_policy import decide_gate as decide_gate_core


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


def classify_horizon_deterministic(
    horizon: Any,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible horizon classifier.

    Wraps existing horizon_bucket with provenance envelope.
    Normalizes horizon values into stable bins (days/weeks/months/years/unknown).

    Args:
        horizon: Horizon value to classify (any type - converted to string)
        seed: Optional deterministic seed (unused for classification, kept for consistency)

    Returns:
        Dictionary with horizon_bucket, provenance, and not_computable (always None)
    """
    # Call existing horizon_bucket function (no changes to core logic)
    bucket = horizon_bucket_core(horizon)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"horizon_bucket": bucket},
        config={},
        inputs={"horizon": horizon},
        operation_id="forecast.horizon.classify",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "horizon_bucket": bucket,
        "provenance": envelope["provenance"],
        "not_computable": None  # horizon classification never fails
    }


def classify_term_deterministic(
    profile: Dict[str, Any],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible term stability classifier.

    Wraps existing classify_term with provenance envelope.
    Classifies terms into stability categories based on A2 profile metrics.

    Args:
        profile: A2 profile dict with metrics (consensus_gap_term, half_life_days, manipulation_risk, momentum, flags)
        seed: Optional deterministic seed (unused for classification, kept for consistency)

    Returns:
        Dictionary with term_class, provenance, and not_computable (always None)
    """
    # Call existing classify_term function (no changes to core logic)
    term_class = classify_term_core(profile)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"term_class": term_class},
        config={},
        inputs={"profile": profile},
        operation_id="forecast.term.classify",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "term_class": term_class,
        "provenance": envelope["provenance"],
        "not_computable": None  # term classification never fails, returns "unknown" for invalid inputs
    }


def load_term_class_map_deterministic(
    a2_phase_path: str,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible term class map loader.

    Wraps existing load_term_class_map with provenance envelope.
    Loads mapping from terms (lowercase) to their classification categories.

    Args:
        a2_phase_path: Path to a2_phase JSON artifact with term profiles
        seed: Optional deterministic seed (unused for loading, kept for consistency)

    Returns:
        Dictionary with term_class_map, provenance, and not_computable (always None)
    """
    # Call existing load_term_class_map function (no changes to core logic)
    term_map = load_term_class_map_core(a2_phase_path)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"term_class_map": term_map},
        config={},
        inputs={"a2_phase_path": a2_phase_path},
        operation_id="forecast.term_class_map.load",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "term_class_map": term_map,
        "provenance": envelope["provenance"],
        "not_computable": None  # map loading never fails, returns empty dict on error
    }


def decide_gate_deterministic(
    dmx_overall: float,
    attribution_strength: float,
    source_diversity: float,
    consensus_gap: float,
    manipulation_risk_mean: float,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible forecast gating policy decision.

    Wraps existing decide_gate with provenance envelope.
    Determines forecast constraints based on DMX risk and evidence quality.

    Args:
        dmx_overall: Overall DMX manipulation risk [0, 1]
        attribution_strength: Attribution strength metric [0, 1]
        source_diversity: Source diversity metric [0, 1]
        consensus_gap: Consensus gap metric [0, 1]
        manipulation_risk_mean: Mean manipulation risk across terms [0, 1]
        seed: Optional deterministic seed (unused for gating, kept for consistency)

    Returns:
        Dictionary with gate_decision, provenance, and not_computable (always None)
    """
    # Call existing decide_gate function (returns GateDecision dataclass)
    gate_decision_obj = decide_gate_core(
        dmx_overall=dmx_overall,
        attribution_strength=attribution_strength,
        source_diversity=source_diversity,
        consensus_gap=consensus_gap,
        manipulation_risk_mean=manipulation_risk_mean
    )

    # Convert dataclass to dict
    gate_decision = gate_decision_obj.to_dict()

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"gate_decision": gate_decision},
        config={},
        inputs={
            "dmx_overall": dmx_overall,
            "attribution_strength": attribution_strength,
            "source_diversity": source_diversity,
            "consensus_gap": consensus_gap,
            "manipulation_risk_mean": manipulation_risk_mean
        },
        operation_id="forecast.gating_policy.decide_gate",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "gate_decision": gate_decision,
        "provenance": envelope["provenance"],
        "not_computable": None  # gating decision never fails, returns default values on error
    }


__all__ = [
    "compute_brier_score_deterministic",
    "compute_expected_error_band_deterministic",
    "classify_horizon_deterministic",
    "classify_term_deterministic",
    "load_term_class_map_deterministic",
    "decide_gate_deterministic"
]
