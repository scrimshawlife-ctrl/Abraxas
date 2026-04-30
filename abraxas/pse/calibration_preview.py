from __future__ import annotations


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _adjust_probability(p: float, multiplier: float) -> float:
    return _clamp01(0.5 + ((p - 0.5) * multiplier))


def _mean_brier(predictions: list[dict], outcomes_by_event: dict[str, str], multiplier: float | None = None) -> float:
    scores = []
    for pred in sorted(predictions, key=lambda x: (x.get("event_id", ""), x.get("prediction_id", ""))):
        predicted = pred.get("predicted_outcome")
        resolved = outcomes_by_event.get(pred.get("event_id", ""))
        if predicted not in {"YES", "NO"} or resolved not in {"YES", "NO"}:
            continue
        p = _clamp01(pred.get("probability", 0.0))
        if multiplier is not None:
            p = _adjust_probability(p, multiplier)
        forecast_probability = p if predicted == "YES" else 1.0 - p
        observed = 1.0 if predicted == resolved else 0.0
        scores.append((forecast_probability - observed) ** 2)
    return round(sum(scores) / len(scores), 6) if scores else 1.0


def build_calibration_preview(predictions: list[dict], outcomes: list[dict], state: dict, readiness: dict) -> dict:
    base = {
        "schema_version": "CalibrationPreviewReport.v1",
        "status": "NOT_COMPUTABLE",
        "baseline": {"mean_brier": None},
        "calibrated_preview": {"mean_brier": None, "multiplier": None},
        "delta": {"mean_brier_delta": None, "improvement": False},
        "recommendation": "DO_NOT_ENABLE_RUNTIME_WIRING",
    }

    if readiness.get("status") != "READY":
        return base
    if state.get("status") != "ACTIVE_GENERATED_STATE":
        return base
    if state.get("applied") is not True:
        return base
    if state.get("runtime_wiring_enabled") is not False:
        return base

    outcomes_by_event = {item.get("event_id", ""): item.get("resolved_outcome", "") for item in outcomes}
    baseline = _mean_brier(predictions, outcomes_by_event, None)
    multiplier = float(state.get("calibration", {}).get("global_confidence_multiplier", 1.0))
    calibrated = _mean_brier(predictions, outcomes_by_event, multiplier)
    delta = round(calibrated - baseline, 6)
    improvement = calibrated < baseline

    return {
        "schema_version": "CalibrationPreviewReport.v1",
        "status": "PREVIEW_ONLY",
        "baseline": {"mean_brier": baseline},
        "calibrated_preview": {
            "mean_brier": calibrated,
            "multiplier": round(multiplier, 6),
        },
        "delta": {
            "mean_brier_delta": delta,
            "improvement": improvement,
        },
        "recommendation": "ENABLE_RUNTIME_WIRING_REVIEW" if improvement else "DO_NOT_ENABLE_RUNTIME_WIRING",
    }
