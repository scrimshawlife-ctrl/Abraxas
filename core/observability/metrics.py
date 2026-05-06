"""DeterministicMetricSeries.v1

A time-indexed series of named metric values. Timestamp indices must be
monotonically increasing. The series hash is deterministic.
"""
from __future__ import annotations

import hashlib
import json
from typing import List, Optional

from core.models.governance import Authority


_SCHEMA_VERSION = "DeterministicMetricSeries.v1"


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class MetricPoint:
    """A single point in a metric series.

    Fields
    ------
    timestamp_index  Integer index (must be strictly increasing in a series)
    metric_name      Name of the metric
    metric_value     Float value of the metric
    """

    def __init__(
        self,
        *,
        timestamp_index: int,
        metric_name: str,
        metric_value: float,
    ) -> None:
        if timestamp_index < 0:
            raise ValueError("timestamp_index must be non-negative")
        if not metric_name:
            raise ValueError("metric_name must not be empty")
        self.timestamp_index = timestamp_index
        self.metric_name = metric_name
        self.metric_value = float(metric_value)

    def to_dict(self) -> dict:
        return {
            "timestamp_index": self.timestamp_index,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
        }


def _validate_monotonic(points: List[MetricPoint]) -> Optional[str]:
    """Return error message if timestamp_index is not strictly monotonic."""
    if len(points) < 2:
        return None
    for i in range(1, len(points)):
        if points[i].timestamp_index <= points[i - 1].timestamp_index:
            return (
                f"timestamp_index not strictly increasing at position {i}: "
                f"{points[i - 1].timestamp_index} -> {points[i].timestamp_index}"
            )
    return None


def _compute_series_hash(points: List[MetricPoint]) -> str:
    return _sha256(_canonical([p.to_dict() for p in points]))


class DeterministicMetricSeries:
    """A deterministic, time-indexed metric series.

    Fields
    ------
    schema_version          Fixed at "DeterministicMetricSeries.v1"
    series_id               Unique identifier
    metric_family           Family label grouping related metrics
    points                  List of MetricPoint (must be monotonically increasing)
    deterministic_series_hash  SHA-256 over the ordered point list
    authority               Locked Authority token
    status                  "valid" | "non_monotonic" | "empty" | "failed"
    """

    schema_version: str = _SCHEMA_VERSION

    def __init__(
        self,
        *,
        series_id: str,
        metric_family: str,
        points: List[MetricPoint],
        authority: Authority,
        status: Optional[str] = None,
    ) -> None:
        if not authority.is_locked():
            raise ValueError("authority must be locked")
        if not series_id:
            raise ValueError("series_id must not be empty")
        if not metric_family:
            raise ValueError("metric_family must not be empty")

        self.schema_version = _SCHEMA_VERSION
        self.series_id = series_id
        self.metric_family = metric_family
        self.points = list(points)
        self.authority = authority
        self.deterministic_series_hash = _compute_series_hash(points)

        if status is not None:
            self.status = status
        elif not points:
            self.status = "empty"
        else:
            err = _validate_monotonic(points)
            self.status = "non_monotonic" if err else "valid"

    def is_valid(self) -> bool:
        return self.status == "valid"

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "series_id": self.series_id,
            "metric_family": self.metric_family,
            "points": [p.to_dict() for p in self.points],
            "deterministic_series_hash": self.deterministic_series_hash,
            "authority": self.authority.to_dict(),
            "status": self.status,
        }


def build_metric_series(
    *,
    series_id: str,
    metric_family: str,
    points: List[MetricPoint],
    authority: Optional[Authority] = None,
) -> DeterministicMetricSeries:
    """Factory for DeterministicMetricSeries."""
    if authority is None:
        authority = Authority.locked()
    return DeterministicMetricSeries(
        series_id=series_id,
        metric_family=metric_family,
        points=points,
        authority=authority,
    )
