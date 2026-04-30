from __future__ import annotations

from abraxas.pse.brier_ledger import build_brier_ledger
from abraxas.pse.outcome_tracker import build_outcome_ledger

DEFAULT_MULTIPLIERS = [0.25, 0.5, 0.75, 0.9, 1.0]


def _clamp(value: float) -> float:
    return max(0.25, min(1.0, float(value)))


def _normalize_multipliers(multipliers: list[float] | None) -> list[float]:
    values = DEFAULT_MULTIPLIERS if multipliers is None else multipliers
    return sorted({round(_clamp(item), 6) for item in values})


def _adjust_probability(p: float, multiplier: float) -> float:
    raw = 0.5 + ((float(p) - 0.5) * multiplier)
    return max(0.0, min(1.0, raw))


def _apply_multiplier(predictions: list[dict], multiplier: float) -> list[dict]:
    adjusted = []
    for item in predictions:
        row = dict(item)
        row["probability"] = _adjust_probability(item.get("probability", 0.0), multiplier)
        adjusted.append(row)
    return adjusted


def build_calibration_candidate_cycle(
    predictions: list[dict],
    outcomes: list[dict],
    readiness: dict,
    activation_decision: dict,
    multipliers: list[float] | None = None,
) -> dict:
    base = {
        "schema_version": "CalibrationCandidateCycleReport.v1",
        "status": "NOT_COMPUTABLE",
        "baseline": {"mean_brier": None},
        "candidates": [],
        "best_candidate": None,
        "recommendation": "NO_IMPROVING_CANDIDATE",
        "runtime_wiring_enabled": False,
    }

    if readiness.get("status") != "READY":
        return base
    if activation_decision.get("status") != "DECISION_RECORDED":
        return base
    if activation_decision.get("runtime_wiring_enabled") is not False:
        return base

    baseline_ledger = build_outcome_ledger(predictions, outcomes)
    baseline_brier = build_brier_ledger(baseline_ledger)
    baseline_mean = baseline_brier["summary"]["mean_brier"]

    candidates = []
    for multiplier in _normalize_multipliers(multipliers):
        adjusted_predictions = _apply_multiplier(predictions, multiplier)
        outcome_ledger = build_outcome_ledger(adjusted_predictions, outcomes)
        brier = build_brier_ledger(outcome_ledger)
        mean_brier = brier["summary"]["mean_brier"]
        delta = round(mean_brier - baseline_mean, 6)
        candidate = {
            "multiplier": multiplier,
            "mean_brier": mean_brier,
            "delta_vs_baseline": delta,
            "improvement": mean_brier < baseline_mean,
        }
        candidates.append(candidate)

    candidates = sorted(candidates, key=lambda item: (item["mean_brier"], item["multiplier"]))
    best_candidate = candidates[0] if candidates else None
    any_improve = any(item["improvement"] for item in candidates)

    return {
        "schema_version": "CalibrationCandidateCycleReport.v1",
        "status": "CANDIDATE_CYCLE_COMPLETE",
        "baseline": {"mean_brier": baseline_mean},
        "candidates": candidates,
        "best_candidate": best_candidate,
        "recommendation": "CREATE_NEW_PROPOSAL_CANDIDATE" if any_improve else "NO_IMPROVING_CANDIDATE",
        "runtime_wiring_enabled": False,
    }
