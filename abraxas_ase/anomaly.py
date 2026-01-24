from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .scoring import stable_round


@dataclass(frozen=True)
class AnomalyRecord:
    metric_name: str
    date: str
    value: float
    baseline: float
    delta: float
    score: float
    severity: str


def _median(values: List[float]) -> float:
    if not values:
        return 0.0
    return float(statistics.median(values))


def compute_delta(series: List[Tuple[str, float]], window: int) -> List[Tuple[str, float, float]]:
    out = []
    values = [v for _, v in series]
    for idx, (date, value) in enumerate(series):
        start = max(0, idx - window)
        baseline_slice = values[start:idx]
        baseline = sum(baseline_slice) / len(baseline_slice) if baseline_slice else 0.0
        delta = value - baseline
        out.append((date, baseline, delta))
    return out


def compute_robust_z(series: List[Tuple[str, float]], window: int) -> List[Tuple[str, float, float]]:
    out = []
    values = [v for _, v in series]
    for idx, (date, value) in enumerate(series):
        start = max(0, idx - window)
        baseline_slice = values[start:idx]
        med = _median(baseline_slice)
        abs_dev = [abs(v - med) for v in baseline_slice]
        mad = _median(abs_dev) if abs_dev else 0.0
        score = (value - med) / (mad if mad > 0 else 1.0)
        out.append((date, med, score))
    return out


def score_anomalies(
    metric_name: str,
    series: List[Tuple[str, float]],
    window: int,
) -> List[AnomalyRecord]:
    deltas = compute_delta(series, window)
    zscores = compute_robust_z(series, window)
    out: List[AnomalyRecord] = []
    for (date, baseline, delta), (_, _, score) in zip(deltas, zscores):
        value = next(v for d, v in series if d == date)
        abs_score = abs(score)
        if abs_score >= 4:
            severity = "high"
        elif abs_score >= 2:
            severity = "medium"
        else:
            severity = "low"
        out.append(AnomalyRecord(
            metric_name=metric_name,
            date=date,
            value=stable_round(value),
            baseline=stable_round(baseline),
            delta=stable_round(delta),
            score=stable_round(score),
            severity=severity,
        ))
    return out


def build_anomalies(metrics: Dict[str, List[Tuple[str, float]]], window: int) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for metric_name in sorted(metrics.keys()):
        series = metrics[metric_name]
        records = score_anomalies(metric_name, series, window)
        out.extend([r.__dict__ for r in records])
    return out
