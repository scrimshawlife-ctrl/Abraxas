"""SML Normalizers: Deterministic normalization functions for parameter mapping.

Provides:
- minmax_clip: Linear normalization to [0,1]
- logistic_clip: Sigmoid-like normalization
- piecewise_bucket: Threshold-based bucketing
- evidence_completeness: Confidence scoring based on param coverage
"""

from __future__ import annotations

import math
from typing import List, Optional

from abraxas.sim_mappings.types import ModelParam


def minmax_clip(x: float, lo: float, hi: float) -> float:
    """
    Normalize x to [0,1] using linear min-max scaling with clipping.

    Args:
        x: Input value
        lo: Minimum expected value
        hi: Maximum expected value

    Returns:
        Normalized value in [0,1]
    """
    if hi <= lo:
        return 0.5  # Degenerate case

    normalized = (x - lo) / (hi - lo)
    return max(0.0, min(normalized, 1.0))


def logistic_clip(x: float, k: float = 1.0, x0: float = 0.5) -> float:
    """
    Normalize x using logistic (sigmoid) function.

    Args:
        x: Input value
        k: Steepness parameter (higher = steeper)
        x0: Midpoint (value where output = 0.5)

    Returns:
        Normalized value in [0,1]
    """
    try:
        return 1.0 / (1.0 + math.exp(-k * (x - x0)))
    except OverflowError:
        # Handle extreme values
        return 1.0 if x > x0 else 0.0


def piecewise_bucket(x: float, thresholds: List[float]) -> float:
    """
    Bucket x into discrete levels based on thresholds.

    Args:
        x: Input value
        thresholds: List of threshold values (must be sorted)

    Returns:
        Normalized value in [0,1] corresponding to bucket

    Example:
        thresholds = [0.1, 0.3, 0.7]
        x < 0.1 -> 0.00
        0.1 <= x < 0.3 -> 0.25
        0.3 <= x < 0.7 -> 0.50
        0.7 <= x -> 1.00
    """
    if not thresholds:
        return 0.5

    # Determine bucket
    bucket = 0
    for threshold in thresholds:
        if x >= threshold:
            bucket += 1
        else:
            break

    # Normalize to [0,1]
    num_buckets = len(thresholds) + 1
    return bucket / (num_buckets - 1) if num_buckets > 1 else 0.5


def evidence_completeness(
    params: List[ModelParam],
    key_params: List[str],
    require_numeric: bool = True,
) -> tuple[float, str]:
    """
    Compute evidence completeness score and confidence level.

    Args:
        params: List of model parameters provided
        key_params: List of key parameter names for this model family
        require_numeric: If True, only count params with numeric values

    Returns:
        Tuple of (completeness_score [0,1], confidence_level "LOW"/"MED"/"HIGH")
    """
    if not key_params:
        return 1.0, "HIGH"  # No requirements = always complete

    # Extract provided param names
    provided_names = {p.name for p in params}

    # Filter to numeric if required
    if require_numeric:
        numeric_names = {p.name for p in params if p.value is not None}
        provided_names = provided_names.intersection(numeric_names)

    # Compute coverage
    matched = provided_names.intersection(set(key_params))
    completeness = len(matched) / len(key_params)

    # Determine confidence
    if completeness >= 0.8:
        confidence = "HIGH"
    elif completeness >= 0.4:
        confidence = "MED"
    else:
        confidence = "LOW"

    return completeness, confidence


def safe_mean(values: List[float], default: float = 0.0) -> float:
    """Compute mean of values, or return default if empty."""
    if not values:
        return default
    return sum(values) / len(values)


def safe_max(values: List[float], default: float = 0.0) -> float:
    """Compute max of values, or return default if empty."""
    if not values:
        return default
    return max(values)


def safe_min(values: List[float], default: float = 0.0) -> float:
    """Compute min of values, or return default if empty."""
    if not values:
        return default
    return min(values)
