from __future__ import annotations


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _adjust(p: float, multiplier: float) -> float:
    return _clamp01(0.5 + ((float(p) - 0.5) * multiplier))


def _mean_brier(predictions: list[dict], outcomes_map: dict[str, str], multiplier: float | None = None) -> float:
    values = []
    for pred in sorted(predictions, key=lambda item: (item.get("event_id", ""), item.get("prediction_id", ""))):
        predicted = pred.get("predicted_outcome")
        resolved = outcomes_map.get(pred.get("event_id", ""))
        if predicted not in {"YES", "NO"} or resolved not in {"YES", "NO"}:
            continue
        p = _clamp01(pred.get("probability", 0.0))
        if multiplier is not None:
            p = _adjust(p, multiplier)
        forecast = p if predicted == "YES" else 1.0 - p
        observed = 1.0 if predicted == resolved else 0.0
        values.append((forecast - observed) ** 2)
    return round(sum(values) / len(values), 6) if values else 1.0


def build_candidate_preview(predictions: list[dict], outcomes: list[dict], state: dict, readiness: dict) -> dict:
    base = {
        "schema_version": "CalibrationCandidatePreviewReport.v1",
        "status": "NOT_COMPUTABLE",
        "baseline": {"mean_brier": None},
        "candidate_preview": {"mean_brier": None, "multiplier": None},
        "delta": {"mean_brier_delta": None, "improvement": False},
        "recommendation": "DO_NOT_ENABLE_RUNTIME_WIRING",
        "runtime_behavior_changed": False,
    }

    if readiness.get("status") != "READY":
        return base
    if state.get("status") != "ACTIVE_GENERATED_STATE":
        return base
    if state.get("applied") is not True:
        return base
    if state.get("runtime_wiring_enabled") is not False:
        return base

    outcomes_map = {item.get("event_id", ""): item.get("resolved_outcome", "") for item in outcomes}
    baseline = _mean_brier(predictions, outcomes_map, None)
    multiplier = float(state.get("calibration", {}).get("global_confidence_multiplier", 1.0))
    candidate = _mean_brier(predictions, outcomes_map, multiplier)
    delta = round(candidate - baseline, 6)
    improvement = candidate < baseline

    return {
        "schema_version": "CalibrationCandidatePreviewReport.v1",
        "status": "PREVIEW_ONLY",
        "baseline": {"mean_brier": baseline},
        "candidate_preview": {"mean_brier": candidate, "multiplier": round(multiplier, 6)},
        "delta": {"mean_brier_delta": delta, "improvement": improvement},
        "recommendation": "ELIGIBLE_FOR_ACTIVATION_REVIEW" if improvement else "DO_NOT_ENABLE_RUNTIME_WIRING",
        "runtime_behavior_changed": False,
    }
