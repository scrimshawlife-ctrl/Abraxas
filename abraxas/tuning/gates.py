"""Rent gates for performance tuning promotion.

Performance Tuning Plane v0.1 - Evidence-based promotion gates.
"""

from __future__ import annotations

from dataclasses import dataclass

from abraxas.tuning.objectives import RentMetrics


@dataclass(frozen=True)
class RentGateVerdict:
    """Verdict from rent gate evaluation."""

    passed: bool
    gate_results: dict[str, bool]
    rationale: str
    metrics_before: RentMetrics
    metrics_after: RentMetrics


# Rent gate thresholds (constants)
COMPRESSION_RATIO_MIN_IMPROVEMENT = 0.05  # 5% improvement
DURATION_MAX_REGRESSION = 0.10  # Max 10% slowdown
CACHE_HIT_RATE_NO_REGRESSION = True  # Cannot get worse
NETWORK_CALLS_NO_REGRESSION = True  # Cannot get worse
DECODO_CALLS_NO_REGRESSION = True  # Cannot get worse


def check_rent_gates(
    metrics_before: RentMetrics,
    metrics_after: RentMetrics,
) -> RentGateVerdict:
    """Check rent gates for tuning promotion.

    Gates that must pass:
    1. Compression ratio improved >= 5% OR storage growth reduced >= 10%
    2. Duration (p95) not worse than 10%
    3. Cache hit rate not worse
    4. Network calls not worse
    5. Decodo calls not worse (or reduced)

    Args:
        metrics_before: Rent metrics before tuning
        metrics_after: Rent metrics after tuning

    Returns:
        RentGateVerdict with pass/fail and detailed results
    """
    gate_results = {}
    reasons = []

    # Gate 1: Compression ratio or storage growth improvement
    avg_compression_before = (
        sum(metrics_before.avg_compression_ratio_by_source.values())
        / len(metrics_before.avg_compression_ratio_by_source)
        if metrics_before.avg_compression_ratio_by_source
        else 1.0
    )
    avg_compression_after = (
        sum(metrics_after.avg_compression_ratio_by_source.values())
        / len(metrics_after.avg_compression_ratio_by_source)
        if metrics_after.avg_compression_ratio_by_source
        else 1.0
    )

    compression_improvement = (avg_compression_after - avg_compression_before) / avg_compression_before
    storage_growth_reduction = (
        metrics_before.storage_growth_rate - metrics_after.storage_growth_rate
    ) / metrics_before.storage_growth_rate if metrics_before.storage_growth_rate > 0 else 0.0

    gate_1 = (
        compression_improvement >= COMPRESSION_RATIO_MIN_IMPROVEMENT
        or storage_growth_reduction >= 0.10
    )
    gate_results["compression_or_storage_gate"] = gate_1
    if gate_1:
        reasons.append(
            f" Compression improved {compression_improvement:.1%} or storage growth reduced {storage_growth_reduction:.1%}"
        )
    else:
        reasons.append(
            f" Compression improvement {compression_improvement:.1%} < {COMPRESSION_RATIO_MIN_IMPROVEMENT:.1%} "
            f"and storage growth reduction {storage_growth_reduction:.1%} < 10%"
        )

    # Gate 2: Duration not worse than 10%
    avg_duration_before = (
        sum(metrics_before.p95_duration_ms_by_op.values())
        / len(metrics_before.p95_duration_ms_by_op)
        if metrics_before.p95_duration_ms_by_op
        else 0.0
    )
    avg_duration_after = (
        sum(metrics_after.p95_duration_ms_by_op.values())
        / len(metrics_after.p95_duration_ms_by_op)
        if metrics_after.p95_duration_ms_by_op
        else 0.0
    )

    duration_regression = (
        (avg_duration_after - avg_duration_before) / avg_duration_before
        if avg_duration_before > 0
        else 0.0
    )
    gate_2 = duration_regression <= DURATION_MAX_REGRESSION
    gate_results["duration_gate"] = gate_2
    if gate_2:
        reasons.append(f" Duration regression {duration_regression:.1%} <= {DURATION_MAX_REGRESSION:.1%}")
    else:
        reasons.append(
            f" Duration regression {duration_regression:.1%} > {DURATION_MAX_REGRESSION:.1%}"
        )

    # Gate 3: Cache hit rate not worse
    avg_cache_hit_before = (
        sum(metrics_before.cache_hit_rate_by_source.values())
        / len(metrics_before.cache_hit_rate_by_source)
        if metrics_before.cache_hit_rate_by_source
        else 0.0
    )
    avg_cache_hit_after = (
        sum(metrics_after.cache_hit_rate_by_source.values())
        / len(metrics_after.cache_hit_rate_by_source)
        if metrics_after.cache_hit_rate_by_source
        else 0.0
    )

    gate_3 = avg_cache_hit_after >= avg_cache_hit_before
    gate_results["cache_hit_rate_gate"] = gate_3
    if gate_3:
        reasons.append(f" Cache hit rate maintained ({avg_cache_hit_after:.1%} >= {avg_cache_hit_before:.1%})")
    else:
        reasons.append(
            f" Cache hit rate degraded ({avg_cache_hit_after:.1%} < {avg_cache_hit_before:.1%})"
        )

    # Gate 4: Network calls not worse
    total_network_before = sum(metrics_before.network_calls_by_source.values())
    total_network_after = sum(metrics_after.network_calls_by_source.values())

    gate_4 = total_network_after <= total_network_before
    gate_results["network_calls_gate"] = gate_4
    if gate_4:
        reasons.append(f" Network calls maintained ({total_network_after} <= {total_network_before})")
    else:
        reasons.append(
            f" Network calls increased ({total_network_after} > {total_network_before})"
        )

    # Gate 5: Decodo calls not worse
    total_decodo_before = sum(metrics_before.decodo_calls_by_reason.values())
    total_decodo_after = sum(metrics_after.decodo_calls_by_reason.values())

    gate_5 = total_decodo_after <= total_decodo_before
    gate_results["decodo_calls_gate"] = gate_5
    if gate_5:
        reasons.append(f" Decodo calls maintained ({total_decodo_after} <= {total_decodo_before})")
    else:
        reasons.append(f" Decodo calls increased ({total_decodo_after} > {total_decodo_before})")

    # Overall verdict
    all_passed = all(gate_results.values())
    rationale = "\n".join(reasons)

    return RentGateVerdict(
        passed=all_passed,
        gate_results=gate_results,
        rationale=rationale,
        metrics_before=metrics_before,
        metrics_after=metrics_after,
    )
