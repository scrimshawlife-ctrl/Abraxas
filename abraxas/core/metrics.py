"""Metrics computation for OAS validation."""

from __future__ import annotations

import math
from collections import Counter
from typing import Any


def compute_entropy(distribution: list[Any]) -> float:
    """
    Compute Shannon entropy of a distribution.

    Args:
        distribution: List of values (will be counted)

    Returns:
        Entropy in bits
    """
    if not distribution:
        return 0.0

    counts = Counter(distribution)
    total = len(distribution)
    entropy = 0.0

    for count in counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)

    return entropy


def compute_false_classification_rate(
    predictions: list[str | None], ground_truth: list[str | None]
) -> float:
    """
    Compute false classification rate.

    False classifications are when prediction is "unknown" or None but ground truth is known,
    or when prediction doesn't match ground truth.

    Args:
        predictions: List of predicted labels (None or "unknown" means no prediction)
        ground_truth: List of true labels

    Returns:
        Rate of false classifications [0.0, 1.0]
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("Predictions and ground truth must have same length")

    if not predictions:
        return 0.0

    false_count = 0
    for pred, truth in zip(predictions, ground_truth):
        # If truth is unknown, skip (can't evaluate)
        if truth is None or truth == "unknown":
            continue

        # If prediction is wrong or unknown when truth is known
        if pred is None or pred == "unknown" or pred != truth:
            false_count += 1

    # Denominator: only cases where ground truth is known
    evaluable = sum(1 for t in ground_truth if t is not None and t != "unknown")
    if evaluable == 0:
        return 0.0

    return false_count / evaluable


class MetricsCollector:
    """Collects and aggregates metrics during pipeline execution."""

    def __init__(self):
        self.metrics: dict[str, list[float]] = {}

    def record(self, name: str, value: float) -> None:
        """Record a metric value."""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)

    def get_mean(self, name: str) -> float:
        """Get mean of recorded values for a metric."""
        values = self.metrics.get(name, [])
        return sum(values) / len(values) if values else 0.0

    def get_all(self) -> dict[str, float]:
        """Get mean of all metrics."""
        return {name: self.get_mean(name) for name in self.metrics}

    def reset(self) -> None:
        """Clear all metrics."""
        self.metrics.clear()
