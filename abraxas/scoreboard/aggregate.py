"""
Score Aggregation

Normalize backtest results into a single score shape for portfolio reporting.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from abraxas.backtest.schema import BacktestResult, BacktestStatus


def aggregate_scores_for_cases(
    backtest_results: List[BacktestResult],
) -> Dict[str, Optional[float]]:
    """
    Aggregate forecast scores across backtest cases.

    Returns:
        Dict with normalized score shape.
    """
    brier_values: List[float] = []
    log_values: List[float] = []
    trend_values: List[float] = []
    crps_values: List[float] = []

    calibration_error_sum = 0.0
    calibration_weight_sum = 0.0

    hit_count = 0
    miss_count = 0
    abstain_count = 0
    unknown_count = 0

    for result in backtest_results:
        if result.status == BacktestStatus.HIT:
            hit_count += 1
        elif result.status == BacktestStatus.MISS:
            miss_count += 1
        elif result.status == BacktestStatus.ABSTAIN:
            abstain_count += 1
        else:
            unknown_count += 1

        forecast_scoring = result.forecast_scoring or {}
        _append_metric(brier_values, forecast_scoring, "brier")
        _append_metric(log_values, forecast_scoring, "log")
        _append_metric(trend_values, forecast_scoring, "trend_acc")
        _append_metric(crps_values, forecast_scoring, "crps")

        if "calibration_error" in forecast_scoring:
            calibration_error_sum += float(forecast_scoring["calibration_error"])
            calibration_weight_sum += 1.0
        else:
            calibration_bins = forecast_scoring.get("calibration_bins", [])
            for bin_entry in calibration_bins:
                predicted = bin_entry.get("predicted_p_avg")
                observed = bin_entry.get("observed_frequency")
                if predicted is None or observed is None:
                    continue
                weight = float(bin_entry.get("n", 1))
                calibration_error_sum += abs(float(predicted) - float(observed)) * weight
                calibration_weight_sum += weight

    total_cases = len(backtest_results)
    abstain_rate = 0.0
    coverage_rate = None
    if total_cases > 0:
        abstain_rate = (abstain_count + unknown_count) / total_cases
        coverage_rate = (hit_count + miss_count) / total_cases

    return {
        "brier_avg": _avg_or_none(brier_values),
        "log_avg": _avg_or_none(log_values),
        "calibration_error": (
            calibration_error_sum / calibration_weight_sum
            if calibration_weight_sum > 0
            else None
        ),
        "coverage_rate": coverage_rate,
        "trend_acc": _avg_or_none(trend_values),
        "crps_avg": _avg_or_none(crps_values),
        "abstain_rate": abstain_rate,
    }


def _append_metric(values: List[float], scoring: Dict[str, Any], key: str) -> None:
    if key in scoring and scoring[key] is not None:
        values.append(float(scoring[key]))


def _avg_or_none(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)
