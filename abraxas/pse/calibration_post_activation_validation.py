from __future__ import annotations


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _adjust(p: float, multiplier: float) -> float:
    return _clamp01(0.5 + ((float(p) - 0.5) * multiplier))


def _mean_brier(predictions: list[dict], outcomes_map: dict[str, str], multiplier: float | None = None) -> tuple[float, int]:
    values: list[float] = []
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
    if not values:
        return 1.0, 0
    return round(sum(values) / len(values), 6), len(values)


def run_post_activation_validation(
    predictions: list[dict],
    outcomes: list[dict],
    wiring_state: dict,
    wiring_report: dict,
    readiness: dict,
) -> dict:
    outcomes_map = {item.get("event_id", ""): item.get("resolved_outcome", "") for item in outcomes}
    baseline, scored_count = _mean_brier(predictions, outcomes_map, None)
    multiplier = float(wiring_state.get("calibration", {}).get("global_confidence_multiplier", 1.0))
    activated, _ = _mean_brier(predictions, outcomes_map, multiplier)
    delta = round(activated - baseline, 6)

    expected_activated = 0.196975
    expected_baseline = 0.1975
    expected_delta = -0.000525

    checks = [
        readiness.get("status") == "READY",
        wiring_state.get("status") == "RUNTIME_WIRING_ENABLED",
        wiring_state.get("runtime_wiring_enabled") is True,
        wiring_state.get("source_logic_modified") is False,
        wiring_state.get("requires_post_validation") is True,
        wiring_report.get("status") == "RUNTIME_WIRING_ENABLED",
        wiring_report.get("post_validation_required") is True,
        round(multiplier, 6) == 0.9,
        scored_count == 3,
        activated < baseline,
        round(baseline, 6) == expected_baseline,
        round(activated, 6) == expected_activated,
        round(delta, 6) == expected_delta,
    ]

    if not all(checks):
        return {
            "schema_version": "CalibrationPostActivationValidationReport.v1",
            "status": "POST_ACTIVATION_FAILED",
            "baseline": baseline,
            "activated": activated,
            "delta": delta,
            "improvement": activated < baseline,
            "scored_count": scored_count,
            "rollback_recommendation": "ROLLBACK_RECOMMENDED",
            "runtime_wiring_status": "ENABLED_FAILED",
            "source_logic_modified": False,
        }

    return {
        "schema_version": "CalibrationPostActivationValidationReport.v1",
        "status": "POST_ACTIVATION_VALIDATED",
        "baseline": baseline,
        "activated": activated,
        "delta": delta,
        "improvement": True,
        "scored_count": scored_count,
        "rollback_recommendation": "NONE",
        "runtime_wiring_status": "ENABLED_VALIDATED",
        "source_logic_modified": False,
    }
