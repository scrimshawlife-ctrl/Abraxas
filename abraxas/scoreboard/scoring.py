"""
Scoring Functions

Deterministic scoring metrics for probabilistic forecasts.
"""

import math
from typing import Dict, List, Tuple


def brier_score(p: float, y: int) -> float:
    """
    Compute Brier score for a single forecast.

    Formula: (p - y)²
    where:
    - p = predicted probability [0, 1]
    - y = observed outcome (1 if occurred, 0 if not)

    Range: [0, 1], lower is better
    Perfect forecast: 0.0
    Worst forecast: 1.0

    Args:
        p: Predicted probability
        y: Observed outcome (0 or 1)

    Returns:
        Brier score
    """
    return (p - y) ** 2


def log_score(p: float, y: int, eps: float = 1e-12) -> float:
    """
    Compute log score for a single forecast.

    Formula: -log(p) if y=1, -log(1-p) if y=0
    where:
    - p = predicted probability [0, 1]
    - y = observed outcome (1 if occurred, 0 if not)

    Range: [0, ∞], lower is better
    Perfect forecast (p=1 when y=1): 0.0
    Terrible forecast (p→0 when y=1): ∞

    Args:
        p: Predicted probability
        y: Observed outcome (0 or 1)
        eps: Small epsilon to avoid log(0)

    Returns:
        Log score
    """
    # Clamp p to [eps, 1-eps] to avoid log(0)
    p_safe = max(eps, min(1 - eps, p))

    if y == 1:
        # Observed: use probability of observed outcome
        return -math.log(p_safe)
    else:
        # Not observed: use probability of NOT occurring
        return -math.log(1 - p_safe)


def update_calibration_bins(
    bins: Dict[str, Dict],
    p: float,
    y: int,
    bin_width: float = 0.1,
) -> Dict[str, Dict]:
    """
    Update calibration bins with new forecast.

    Bins group forecasts by predicted probability range:
    - 0-10%, 10-20%, ..., 90-100%

    For each bin, track:
    - predicted_p_sum: sum of predicted probabilities
    - observed_sum: sum of observed outcomes
    - n: count of forecasts

    Args:
        bins: Current calibration bins dict
        p: Predicted probability for new forecast
        y: Observed outcome (0 or 1)
        bin_width: Width of each bin (default 0.1 = 10%)

    Returns:
        Updated bins dict
    """
    # Determine which bin this forecast belongs to
    bin_idx = int(p / bin_width)
    bin_idx = min(bin_idx, int(1.0 / bin_width) - 1)  # Cap at max bin

    bin_start = bin_idx * bin_width
    bin_end = (bin_idx + 1) * bin_width
    bin_label = f"{int(bin_start*100)}-{int(bin_end*100)}%"

    # Initialize bin if needed
    if bin_label not in bins:
        bins[bin_label] = {
            "predicted_p_sum": 0.0,
            "observed_sum": 0,
            "n": 0,
        }

    # Update bin
    bins[bin_label]["predicted_p_sum"] += p
    bins[bin_label]["observed_sum"] += y
    bins[bin_label]["n"] += 1

    return bins


def compute_calibration_error(bins: Dict[str, Dict]) -> float:
    """
    Compute overall calibration error across bins.

    For each bin, error = |predicted_avg - observed_frequency|
    Overall error = weighted average by bin count.

    Args:
        bins: Calibration bins dict

    Returns:
        Overall calibration error [0, 1]
    """
    total_error = 0.0
    total_n = 0

    for bin_label, bin_data in bins.items():
        if bin_data["n"] == 0:
            continue

        predicted_avg = bin_data["predicted_p_sum"] / bin_data["n"]
        observed_freq = bin_data["observed_sum"] / bin_data["n"]

        error = abs(predicted_avg - observed_freq)
        total_error += error * bin_data["n"]
        total_n += bin_data["n"]

    if total_n == 0:
        return 0.0

    return total_error / total_n


def format_calibration_bins(bins: Dict[str, Dict]) -> List[Dict]:
    """
    Format calibration bins for display.

    Args:
        bins: Calibration bins dict

    Returns:
        List of formatted bin dicts
    """
    formatted = []

    for bin_label, bin_data in sorted(bins.items()):
        if bin_data["n"] == 0:
            continue

        predicted_avg = bin_data["predicted_p_sum"] / bin_data["n"]
        observed_freq = bin_data["observed_sum"] / bin_data["n"]

        formatted.append(
            {
                "bin_label": bin_label,
                "predicted_p_avg": round(predicted_avg, 3),
                "observed_frequency": round(observed_freq, 3),
                "n": bin_data["n"],
                "calibration_error": round(abs(predicted_avg - observed_freq), 3),
            }
        )

    return formatted
