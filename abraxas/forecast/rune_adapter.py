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
from abraxas.forecast.horizon_policy import compare_horizon as compare_horizon_core
from abraxas.forecast.horizon_policy import enforce_horizon_policy as enforce_horizon_policy_core
from abraxas.forecast.ledger import issue_prediction as issue_prediction_core
from abraxas.forecast.ledger import record_outcome as record_outcome_core
from abraxas.forecast.policy_candidates import candidates_v0_1 as candidates_v0_1_core
from abraxas.forecast.uncertainty import horizon_uncertainty_multiplier as horizon_uncertainty_multiplier_core


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


def load_policy_candidates_v0_1_deterministic(
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible horizon policy candidates loader.

    Returns policy threshold candidates with provenance envelope.
    """
    candidates = candidates_v0_1_core()

    envelope = canonical_envelope(
        result={"candidates": candidates},
        config={},
        inputs={},
        operation_id="forecast.policy_candidates.v0_1",
        seed=seed,
    )

    return {
        "candidates": candidates,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"],
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


def compare_horizon_deterministic(
    horizon: str,
    max_horizon: str,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible horizon comparison.

    Wraps existing compare_horizon with provenance envelope.
    Compares two horizon values returning -1, 0, or +1.

    Args:
        horizon: Horizon to compare (days, weeks, months, years, years_1, years_5)
        max_horizon: Maximum horizon to compare against
        seed: Optional deterministic seed (unused for comparison, kept for consistency)

    Returns:
        Dictionary with comparison_result (-1, 0, +1), provenance, and not_computable (always None)
    """
    # Call existing compare_horizon function (no changes to core logic)
    result = compare_horizon_core(horizon, max_horizon)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"comparison_result": result},
        config={},
        inputs={"horizon": horizon, "max_horizon": max_horizon},
        operation_id="forecast.horizon_policy.compare",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "comparison_result": result,
        "provenance": envelope["provenance"],
        "not_computable": None  # comparison never fails
    }


def enforce_horizon_policy_deterministic(
    horizon: str,
    gate: Dict[str, Any],
    emit_shadow: bool = True,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible horizon policy enforcement.

    Wraps existing enforce_horizon_policy with provenance envelope.
    Returns flags and optional shadow horizon when policy is exceeded.

    Args:
        horizon: Requested horizon
        gate: Gate decision dict with horizon_max field
        emit_shadow: Whether to emit shadow prediction on policy violation
        seed: Optional deterministic seed (unused for enforcement, kept for consistency)

    Returns:
        Dictionary with flags (list), shadow_horizon (str|null), provenance, and not_computable (always None)
    """
    # Call existing enforce_horizon_policy function (returns tuple: flags, shadow_horizon)
    flags, shadow_horizon = enforce_horizon_policy_core(
        horizon=horizon,
        gate=gate,
        emit_shadow=emit_shadow
    )

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"flags": flags, "shadow_horizon": shadow_horizon},
        config={"emit_shadow": emit_shadow},
        inputs={"horizon": horizon, "gate": gate},
        operation_id="forecast.horizon_policy.enforce",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "flags": flags,
        "shadow_horizon": shadow_horizon,
        "provenance": envelope["provenance"],
        "not_computable": None  # enforcement never fails
    }


def issue_prediction_deterministic(
    term: str,
    p: float,
    horizon: str,
    run_id: str,
    expected_error_band: Optional[Dict[str, Any]] = None,
    phase_context: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    flags: Optional[List[str]] = None,
    evidence: Optional[List[Dict[str, Any]]] = None,
    ts_issued: Optional[str] = None,
    ledger_path: str = "out/forecast_ledger/predictions.jsonl",
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible prediction issuance to ledger.

    Wraps existing issue_prediction with provenance envelope.
    Creates prediction record and appends to forecast ledger.

    Args:
        term: Term being predicted
        p: Probability [0, 1]
        horizon: Horizon band (days, weeks, months, years_1, years_5)
        run_id: Run identifier
        expected_error_band: Optional error band dict
        phase_context: Optional phase context (phase, half_life_days_fit, manipulation_risk_mean)
        context: Optional additional context (dmx, gate, etc.)
        flags: Optional flags list
        evidence: Optional evidence list
        ts_issued: Optional timestamp override
        ledger_path: Path to forecast ledger JSONL
        seed: Optional deterministic seed (unused for ledger write, kept for consistency)

    Returns:
        Dictionary with prediction_row, provenance, and not_computable (always None)
    """
    # Call existing issue_prediction function (writes to ledger, returns row dict)
    prediction_row = issue_prediction_core(
        term=term,
        p=p,
        horizon=horizon,
        run_id=run_id,
        expected_error_band=expected_error_band,
        phase_context=phase_context,
        context=context,
        flags=flags,
        evidence=evidence,
        ts_issued=ts_issued,
        ledger_path=ledger_path
    )

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"prediction_row": prediction_row},
        config={"ledger_path": ledger_path},
        inputs={
            "term": term,
            "p": p,
            "horizon": horizon,
            "run_id": run_id,
            "expected_error_band": expected_error_band,
            "phase_context": phase_context,
            "context": context,
            "flags": flags,
            "evidence": evidence,
            "ts_issued": ts_issued
        },
        operation_id="forecast.ledger.issue",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "prediction_row": prediction_row,
        "provenance": envelope["provenance"],
        "not_computable": None  # ledger write never fails (core function handles errors)
    }


def horizon_uncertainty_multiplier_deterministic(
    horizon: Any,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible horizon uncertainty multiplier calculator.

    Wraps existing horizon_uncertainty_multiplier with provenance envelope.
    Maps horizon values to uncertainty multipliers (1.00 for days, 1.05 for weeks, etc.).

    Args:
        horizon: Horizon value (days, weeks, months, years, or any string)
        seed: Optional deterministic seed (unused for multiplier, kept for consistency)

    Returns:
        Dictionary with multiplier, provenance, and not_computable (always None)
    """
    # Call existing horizon_uncertainty_multiplier function (no changes to core logic)
    multiplier = horizon_uncertainty_multiplier_core(horizon)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"multiplier": multiplier},
        config={},
        inputs={"horizon": horizon},
        operation_id="forecast.uncertainty.horizon_multiplier",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "multiplier": multiplier,
        "provenance": envelope["provenance"],
        "not_computable": None  # multiplier calculation never fails, returns default on unknown
    }


def record_forecast_outcome_deterministic(
    *,
    pred_id: str,
    result: str,
    run_id: str,
    evidence: Optional[List[Dict[str, Any]]] = None,
    notes: str = "",
    ts_observed: Optional[str] = None,
    ledger_path: str = "out/forecast_ledger/outcomes.jsonl",
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible forecast outcome recorder.

    Wraps existing record_outcome with provenance envelope.
    Appends outcome rows to the forecast outcomes ledger.

    Args:
        pred_id: Prediction identifier
        result: Outcome result (hit/miss/partial)
        run_id: Run identifier for provenance
        evidence: Optional evidence list
        notes: Optional notes string
        ts_observed: Optional observed timestamp (ISO8601)
        ledger_path: Output ledger path
        seed: Optional deterministic seed (unused, kept for consistency)

    Returns:
        Dictionary with outcome row, provenance, and not_computable (always None)
    """
    row = record_outcome_core(
        pred_id=pred_id,
        result=result,
        run_id=run_id,
        evidence=evidence,
        notes=notes,
        ts_observed=ts_observed,
        ledger_path=ledger_path,
    )

    envelope = canonical_envelope(
        result={"outcome": row},
        config={},
        inputs={
            "pred_id": pred_id,
            "result": result,
            "run_id": run_id,
            "evidence": evidence or [],
            "notes": notes,
            "ts_observed": ts_observed,
            "ledger_path": ledger_path,
        },
        operation_id="forecast.outcome.record",
        seed=seed,
    )

    return {
        "outcome": row,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"],
    }


def policy_candidates_v0_1_deterministic(
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible policy candidates loader.

    Wraps existing candidates_v0_1 with provenance envelope.
    Returns static policy candidate thresholds (conservative, balanced, aggressive).

    Args:
        seed: Optional deterministic seed (unused for static data, kept for consistency)

    Returns:
        Dictionary with candidates, provenance, and not_computable (always None)
    """
    # Call existing candidates_v0_1 function (returns static dict)
    candidates = candidates_v0_1_core()

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"candidates": candidates},
        config={},
        inputs={},
        operation_id="forecast.policy.candidates_v0_1",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "candidates": candidates,
        "provenance": envelope["provenance"],
        "not_computable": None  # static data never fails
    }


__all__ = [
    "compute_brier_score_deterministic",
    "compute_expected_error_band_deterministic",
    "classify_horizon_deterministic",
    "load_policy_candidates_v0_1_deterministic",
    "classify_term_deterministic",
    "load_term_class_map_deterministic",
    "decide_gate_deterministic",
    "compare_horizon_deterministic",
    "enforce_horizon_policy_deterministic",
    "issue_prediction_deterministic",
    "horizon_uncertainty_multiplier_deterministic",
    "policy_candidates_v0_1_deterministic",
    "record_forecast_outcome_deterministic"
]
