"""Rent metrics and objective function for performance tuning.

Performance Tuning Plane v0.1 - Evidence-based optimization objectives.
"""

from __future__ import annotations

from dataclasses import dataclass

from abraxas.perf.ledger import read_perf_events


@dataclass(frozen=True)
class RentMetrics:
    """Rent payment metrics extracted from perf ledger."""

    avg_compression_ratio_by_source: dict[str, float]
    p95_duration_ms_by_op: dict[str, float]
    cache_hit_rate_by_source: dict[str, float]
    network_calls_by_source: dict[str, int]
    decodo_calls_by_reason: dict[str, int]
    storage_growth_rate: float  # bytes/day
    total_bytes_saved: int


@dataclass(frozen=True)
class TuningObjective:
    """Tuning objective with weights (maximize or minimize)."""

    # Maximize metrics (higher is better)
    compression_ratio: float  # Weight for compression ratio
    cache_hit_rate: float  # Weight for cache hit rate

    # Minimize metrics (lower is better)
    duration_ms: float  # Weight for operation duration
    network_calls: float  # Weight for network calls
    decodo_calls: float  # Weight for Decodo calls
    storage_growth: float  # Weight for storage growth rate


# Default objective weights (constants)
DEFAULT_OBJECTIVE = TuningObjective(
    compression_ratio=1.0,
    cache_hit_rate=0.5,
    duration_ms=0.3,
    network_calls=0.8,
    decodo_calls=2.0,  # Heavily penalize Decodo calls
    storage_growth=0.4,
)


def compute_rent_metrics(
    *,
    window_hours: int = 168,  # 7 days
    op_name: str | None = None,
) -> RentMetrics:
    """Compute rent metrics from perf ledger.

    Args:
        window_hours: Time window in hours (default: 168 = 7 days)
        op_name: Optional operation name filter

    Returns:
        RentMetrics with computed statistics
    """
    events = read_perf_events(op_name=op_name)

    # Compute per-source compression ratios
    compression_by_source: dict[str, list[float]] = {}
    for event in events:
        if event.compression_ratio and event.source_id:
            if event.source_id not in compression_by_source:
                compression_by_source[event.source_id] = []
            compression_by_source[event.source_id].append(event.compression_ratio)

    avg_compression_ratio_by_source = {
        source: sum(ratios) / len(ratios)
        for source, ratios in compression_by_source.items()
    }

    # Compute p95 duration by operation
    duration_by_op: dict[str, list[float]] = {}
    for event in events:
        if event.op_name not in duration_by_op:
            duration_by_op[event.op_name] = []
        duration_by_op[event.op_name].append(event.duration_ms)

    p95_duration_ms_by_op = {}
    for op, durations in duration_by_op.items():
        sorted_durations = sorted(durations)
        p95_index = int(len(sorted_durations) * 0.95)
        p95_duration_ms_by_op[op] = sorted_durations[p95_index] if sorted_durations else 0.0

    # Compute cache hit rate by source
    cache_hits_by_source: dict[str, int] = {}
    cache_misses_by_source: dict[str, int] = {}
    for event in events:
        if event.source_id:
            if event.cache_hit:
                cache_hits_by_source[event.source_id] = (
                    cache_hits_by_source.get(event.source_id, 0) + 1
                )
            else:
                cache_misses_by_source[event.source_id] = (
                    cache_misses_by_source.get(event.source_id, 0) + 1
                )

    cache_hit_rate_by_source = {}
    for source in set(cache_hits_by_source.keys()) | set(cache_misses_by_source.keys()):
        hits = cache_hits_by_source.get(source, 0)
        misses = cache_misses_by_source.get(source, 0)
        total = hits + misses
        cache_hit_rate_by_source[source] = hits / total if total > 0 else 0.0

    # Count network calls by source
    network_calls_by_source = {}
    for event in events:
        if event.source_id and not event.cache_hit:
            network_calls_by_source[event.source_id] = (
                network_calls_by_source.get(event.source_id, 0) + 1
            )

    # Count Decodo calls by reason
    decodo_calls_by_reason = {}
    for event in events:
        if event.decodo_used and event.reason_code:
            decodo_calls_by_reason[event.reason_code] = (
                decodo_calls_by_reason.get(event.reason_code, 0) + 1
            )

    # Estimate storage growth rate
    total_bytes_written = sum(e.bytes_out for e in events)
    storage_growth_rate = total_bytes_written / (window_hours / 24) if window_hours > 0 else 0.0

    # Total bytes saved (compression)
    total_bytes_saved = sum(e.bytes_in - e.bytes_out for e in events)

    return RentMetrics(
        avg_compression_ratio_by_source=avg_compression_ratio_by_source,
        p95_duration_ms_by_op=p95_duration_ms_by_op,
        cache_hit_rate_by_source=cache_hit_rate_by_source,
        network_calls_by_source=network_calls_by_source,
        decodo_calls_by_reason=decodo_calls_by_reason,
        storage_growth_rate=storage_growth_rate,
        total_bytes_saved=total_bytes_saved,
    )


def compute_objective(
    metrics: RentMetrics,
    objective: TuningObjective = DEFAULT_OBJECTIVE,
) -> float:
    """Compute objective function value from rent metrics.

    Objective = maximize(compression_ratio, cache_hit_rate) -
                minimize(duration_ms, network_calls, decodo_calls, storage_growth)

    Args:
        metrics: RentMetrics to evaluate
        objective: TuningObjective with weights

    Returns:
        Objective value (higher is better)
    """
    # Maximize metrics (positive contribution)
    avg_compression = (
        sum(metrics.avg_compression_ratio_by_source.values())
        / len(metrics.avg_compression_ratio_by_source)
        if metrics.avg_compression_ratio_by_source
        else 1.0
    )
    avg_cache_hit = (
        sum(metrics.cache_hit_rate_by_source.values()) / len(metrics.cache_hit_rate_by_source)
        if metrics.cache_hit_rate_by_source
        else 0.0
    )

    maximize_term = (
        objective.compression_ratio * avg_compression + objective.cache_hit_rate * avg_cache_hit
    )

    # Minimize metrics (negative contribution)
    avg_duration = (
        sum(metrics.p95_duration_ms_by_op.values()) / len(metrics.p95_duration_ms_by_op)
        if metrics.p95_duration_ms_by_op
        else 0.0
    )
    total_network_calls = sum(metrics.network_calls_by_source.values())
    total_decodo_calls = sum(metrics.decodo_calls_by_reason.values())

    minimize_term = (
        objective.duration_ms * avg_duration
        + objective.network_calls * total_network_calls
        + objective.decodo_calls * total_decodo_calls
        + objective.storage_growth * metrics.storage_growth_rate
    )

    # Normalize to reasonable scale (duration in seconds, not ms)
    minimize_term_normalized = minimize_term / 1000.0

    return maximize_term - minimize_term_normalized
