"""
Tests for Scoreboard v0.1

Validates Brier score, log score, and calibration bin calculations.
"""

import math
import pytest

from abraxas.scoreboard.scoring import (
    brier_score,
    log_score,
    update_calibration_bins,
    compute_calibration_error,
    format_calibration_bins,
)
from abraxas.scoreboard.ledger import ScoreLedger
from abraxas.scoreboard.types import ScoreResult, CalibrationBin


def test_brier_score_perfect_forecast():
    """Test Brier score for perfect forecasts."""
    # Perfect forecast: p=1, y=1
    assert brier_score(1.0, 1) == 0.0

    # Perfect forecast: p=0, y=0
    assert brier_score(0.0, 0) == 0.0


def test_brier_score_worst_forecast():
    """Test Brier score for worst forecasts."""
    # Worst forecast: p=1, y=0
    assert brier_score(1.0, 0) == 1.0

    # Worst forecast: p=0, y=1
    assert brier_score(0.0, 1) == 1.0


def test_brier_score_moderate_forecast():
    """Test Brier score for moderate forecasts."""
    # Moderate forecast: p=0.7, y=1
    score = brier_score(0.7, 1)
    assert abs(score - 0.09) < 0.01  # (0.7 - 1)² = 0.09

    # Moderate forecast: p=0.3, y=0
    score = brier_score(0.3, 0)
    assert abs(score - 0.09) < 0.01  # (0.3 - 0)² = 0.09


def test_log_score_perfect_forecast():
    """Test log score for perfect forecasts."""
    # Perfect forecast: p=1, y=1
    assert log_score(1.0, 1) == pytest.approx(0.0, abs=0.01)

    # Perfect forecast: p=0, y=0 (with epsilon protection)
    score = log_score(0.0, 0)
    assert score >= 0.0  # Should not be negative


def test_log_score_penalizes_overconfidence():
    """Test that log score heavily penalizes overconfident wrong forecasts."""
    # Confident but wrong: p=0.9, y=0
    score_high_conf = log_score(0.9, 0)

    # Less confident wrong: p=0.6, y=0
    score_low_conf = log_score(0.6, 0)

    # Higher confidence wrong should have higher (worse) score
    assert score_high_conf > score_low_conf


def test_calibration_bins_update():
    """Test updating calibration bins."""
    bins = {}

    # Add forecasts
    forecasts = [
        (0.65, 1),  # 60-70% bin, occurred
        (0.68, 1),  # 60-70% bin, occurred
        (0.62, 0),  # 60-70% bin, did not occur
        (0.85, 1),  # 80-90% bin, occurred
        (0.82, 1),  # 80-90% bin, occurred
        (0.88, 0),  # 80-90% bin, did not occur
    ]

    for p, y in forecasts:
        bins = update_calibration_bins(bins, p, y)

    # Check 60-70% bin
    assert "60-70%" in bins
    assert bins["60-70%"]["n"] == 3
    assert bins["60-70%"]["observed_sum"] == 2  # 2 out of 3 occurred

    # Check 80-90% bin
    assert "80-90%" in bins
    assert bins["80-90%"]["n"] == 3
    assert bins["80-90%"]["observed_sum"] == 2  # 2 out of 3 occurred


def test_calibration_perfect():
    """Test calibration with perfect calibration."""
    bins = {}

    # Add perfectly calibrated forecasts
    # 65% predictions should occur 65% of the time
    for _ in range(65):
        bins = update_calibration_bins(bins, 0.65, 1)  # occurred
    for _ in range(35):
        bins = update_calibration_bins(bins, 0.65, 0)  # did not occur

    formatted = format_calibration_bins(bins)

    assert len(formatted) == 1
    bin_data = formatted[0]

    assert bin_data["bin_label"] == "60-70%"
    assert bin_data["n"] == 100
    assert abs(bin_data["observed_frequency"] - 0.65) < 0.01
    assert bin_data["calibration_error"] < 0.05  # Well-calibrated


def test_calibration_overconfident():
    """Test calibration with overconfident forecasts."""
    bins = {}

    # Add overconfident forecasts
    # 85% predictions but only 60% occur
    for _ in range(6):
        bins = update_calibration_bins(bins, 0.85, 1)  # occurred
    for _ in range(4):
        bins = update_calibration_bins(bins, 0.85, 0)  # did not occur

    formatted = format_calibration_bins(bins)

    bin_data = formatted[0]

    assert bin_data["n"] == 10
    assert abs(bin_data["predicted_p_avg"] - 0.85) < 0.01
    assert abs(bin_data["observed_frequency"] - 0.60) < 0.01
    # Calibration error should be ~0.25
    assert abs(bin_data["calibration_error"] - 0.25) < 0.01


def test_score_ledger_append_and_read(tmp_path):
    """Test appending and reading from score ledger."""
    ledger = ScoreLedger(ledger_path=tmp_path / "scores.jsonl")

    score_result = ScoreResult(
        score_id="score_H72H_001",
        horizon="H72H",
        segment="core",
        narrative="N1_primary",
        brier_avg=0.15,
        log_avg=0.42,
        calibration_bins=[
            CalibrationBin(
                bin_label="60-70%",
                predicted_p_avg=0.65,
                observed_frequency=0.68,
                n=10,
            )
        ],
        coverage={"hit": 8, "miss": 2, "abstain": 0},
        abstain_rate=0.0,
        cases_scored=10,
    )

    # Append to ledger
    step_hash = ledger.append_score(score_result, run_id="test_run_001")

    assert step_hash is not None
    assert len(step_hash) == 64  # SHA256 hex

    # Read back
    entries = ledger.read_all()
    assert len(entries) == 1
    assert entries[0]["score_id"] == "score_H72H_001"
    assert entries[0]["brier_avg"] == 0.15


def test_score_ledger_chain_integrity(tmp_path):
    """Test that score ledger maintains hash chain."""
    ledger = ScoreLedger(ledger_path=tmp_path / "scores.jsonl")

    # Append multiple scores
    for i in range(3):
        score_result = ScoreResult(
            score_id=f"score_{i}",
            horizon="H72H",
            brier_avg=0.1 + i * 0.05,
            log_avg=0.3 + i * 0.1,
            cases_scored=10,
        )
        ledger.append_score(score_result)

    # Verify chain
    entries = ledger.read_all()
    assert len(entries) == 3

    # Check hash chain
    prev_hash = "genesis"
    for entry in entries:
        assert entry["prev_hash"] == prev_hash
        assert "step_hash" in entry
        prev_hash = entry["step_hash"]


def test_multiple_bins_calibration_error():
    """Test calibration error computation across multiple bins."""
    bins = {}

    # Add forecasts across multiple bins
    # 30-40% bin: perfectly calibrated
    for _ in range(35):
        bins = update_calibration_bins(bins, 0.35, 1)
    for _ in range(65):
        bins = update_calibration_bins(bins, 0.35, 0)

    # 70-80% bin: slightly overconfident
    for _ in range(65):
        bins = update_calibration_bins(bins, 0.75, 1)
    for _ in range(35):
        bins = update_calibration_bins(bins, 0.75, 0)

    # Compute overall error
    error = compute_calibration_error(bins)

    # Should be low since one bin is perfect and other is close
    assert error < 0.10


def test_brier_score_range():
    """Test that Brier score is always in [0, 1]."""
    test_cases = [
        (0.0, 0),
        (0.0, 1),
        (0.5, 0),
        (0.5, 1),
        (1.0, 0),
        (1.0, 1),
        (0.3, 0),
        (0.7, 1),
    ]

    for p, y in test_cases:
        score = brier_score(p, y)
        assert 0 <= score <= 1, f"Brier score {score} out of range for p={p}, y={y}"


def test_log_score_non_negative():
    """Test that log score is non-negative."""
    test_cases = [
        (0.5, 1),
        (0.5, 0),
        (0.9, 1),
        (0.1, 0),
        (0.99, 1),
        (0.01, 0),
    ]

    for p, y in test_cases:
        score = log_score(p, y)
        assert score >= 0, f"Log score {score} negative for p={p}, y={y}"
