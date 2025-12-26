"""
Tests for score aggregation shape.
"""

from datetime import datetime, timezone

from abraxas.backtest.schema import BacktestResult, BacktestStatus, Confidence
from abraxas.scoreboard.aggregate import aggregate_scores_for_cases


def test_score_aggregate_shape():
    results = [
        BacktestResult(
            case_id="case_1",
            status=BacktestStatus.HIT,
            score=1.0,
            confidence=Confidence.HIGH,
            forecast_scoring={
                "brier": 0.2,
                "log": 0.4,
                "trend_acc": 0.8,
                "crps": 0.3,
                "calibration_bins": [
                    {"predicted_p_avg": 0.7, "observed_frequency": 0.6, "n": 2}
                ],
            },
            evaluated_at=datetime.now(timezone.utc),
        ),
        BacktestResult(
            case_id="case_2",
            status=BacktestStatus.MISS,
            score=0.0,
            confidence=Confidence.MED,
            forecast_scoring={
                "brier": 0.4,
                "log": 0.6,
                "trend_acc": 0.6,
                "crps": 0.5,
                "calibration_bins": [
                    {"predicted_p_avg": 0.2, "observed_frequency": 0.3, "n": 1}
                ],
            },
            evaluated_at=datetime.now(timezone.utc),
        ),
    ]

    aggregated = aggregate_scores_for_cases(results)

    assert set(aggregated.keys()) == {
        "brier_avg",
        "log_avg",
        "calibration_error",
        "coverage_rate",
        "trend_acc",
        "crps_avg",
        "abstain_rate",
    }
    assert aggregated["brier_avg"] == 0.3
    assert aggregated["log_avg"] == 0.5
    assert aggregated["trend_acc"] == 0.7
    assert aggregated["crps_avg"] == 0.4
    assert aggregated["coverage_rate"] == 1.0
    assert aggregated["abstain_rate"] == 0.0
    assert round(aggregated["calibration_error"], 3) == 0.1
