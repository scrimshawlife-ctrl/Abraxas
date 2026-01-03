"""Unified objective function for portfolio tuning.

Universal Tuning Plane v0.4 - Cross-module optimization objectives.
"""

from __future__ import annotations

from dataclasses import dataclass

from abraxas.tuning.ubv import UniversalBudgetVector


@dataclass(frozen=True)
class PortfolioObjectiveWeights:
    """Weights for unified portfolio objective function.

    All weights are constants (logged, not tuned).
    """

    # Efficiency score components (maximize)
    compression_ratio: float = 1.0
    cache_hit_rate: float = 0.8
    dedup_rate: float = 0.6

    # Speed score components (maximize - inverted)
    latency_p95: float = 0.5  # Higher weight = more penalty for high latency
    cpu_ms: float = 0.3  # Higher weight = more penalty for high CPU

    # Stability score components (maximize)
    determinism_pass_rate: float = 2.0  # Critical - heavily weighted
    budget_satisfaction_rate: float = 1.5  # Important
    drift_free_rate: float = 0.7  # Moderate

    # Violation penalty (minimize)
    hard_violation_penalty: float = float("inf")  # Hard violations block promotion
    soft_violation_penalty: float = 10.0  # Soft budget overruns are costly


DEFAULT_WEIGHTS = PortfolioObjectiveWeights()


@dataclass(frozen=True)
class PortfolioMetrics:
    """Aggregated metrics across all subsystems."""

    # Efficiency metrics
    avg_compression_ratio: float
    cache_hit_rate: float
    dedup_rate: float

    # Speed metrics
    latency_p95_ms: float
    avg_cpu_ms: float

    # Stability metrics
    determinism_pass_rate: float
    budget_satisfaction_rate: float
    drift_free_rate: float

    # Violations
    hard_violations: int
    soft_violations: int


def compute_efficiency_score(
    metrics: PortfolioMetrics, weights: PortfolioObjectiveWeights
) -> float:
    """Compute efficiency score (maximize).

    Args:
        metrics: Portfolio metrics
        weights: Objective weights

    Returns:
        Efficiency score (higher is better)
    """
    return (
        weights.compression_ratio * metrics.avg_compression_ratio
        + weights.cache_hit_rate * metrics.cache_hit_rate
        + weights.dedup_rate * metrics.dedup_rate
    )


def compute_speed_score(metrics: PortfolioMetrics, weights: PortfolioObjectiveWeights) -> float:
    """Compute speed score (maximize - inverted).

    Lower latency and CPU = higher score.

    Args:
        metrics: Portfolio metrics
        weights: Objective weights

    Returns:
        Speed score (higher is better)
    """
    # Invert latency and CPU (lower is better, so we use inverse)
    # Add small epsilon to avoid division by zero
    epsilon = 1e-6

    latency_inv = 1.0 / (metrics.latency_p95_ms + epsilon)
    cpu_inv = 1.0 / (metrics.avg_cpu_ms + epsilon)

    # Normalize to reasonable scale (multiply by 1000 to bring to ~1.0 range)
    return weights.latency_p95 * latency_inv * 1000.0 + weights.cpu_ms * cpu_inv * 1000.0


def compute_stability_score(
    metrics: PortfolioMetrics, weights: PortfolioObjectiveWeights
) -> float:
    """Compute stability score (maximize).

    Args:
        metrics: Portfolio metrics
        weights: Objective weights

    Returns:
        Stability score (higher is better)
    """
    return (
        weights.determinism_pass_rate * metrics.determinism_pass_rate
        + weights.budget_satisfaction_rate * metrics.budget_satisfaction_rate
        + weights.drift_free_rate * metrics.drift_free_rate
    )


def compute_violation_penalty(
    metrics: PortfolioMetrics, weights: PortfolioObjectiveWeights
) -> float:
    """Compute violation penalty (minimize).

    Hard violations = - (blocks promotion).
    Soft violations = linear penalty.

    Args:
        metrics: Portfolio metrics
        weights: Objective weights

    Returns:
        Violation penalty (higher penalty = worse)
    """
    if metrics.hard_violations > 0:
        return weights.hard_violation_penalty

    return weights.soft_violation_penalty * metrics.soft_violations


def compute_portfolio_objective(
    metrics: PortfolioMetrics,
    weights: PortfolioObjectiveWeights = DEFAULT_WEIGHTS,
) -> float:
    """Compute unified portfolio objective.

    Objective = efficiency + speed + stability - violations

    Args:
        metrics: Portfolio metrics
        weights: Objective weights

    Returns:
        Objective value (higher is better, -inf for hard violations)
    """
    efficiency = compute_efficiency_score(metrics, weights)
    speed = compute_speed_score(metrics, weights)
    stability = compute_stability_score(metrics, weights)
    penalty = compute_violation_penalty(metrics, weights)

    # Hard violations make objective -inf
    if penalty == float("inf"):
        return float("-inf")

    return efficiency + speed + stability - penalty


def extract_portfolio_metrics_from_ubv(
    ubv: UniversalBudgetVector,
    *,
    determinism_pass_rate: float = 1.0,
    drift_free_rate: float = 1.0,
) -> PortfolioMetrics:
    """Extract PortfolioMetrics from UniversalBudgetVector.

    Note: This is a simplified extraction. In production, we'd pull from
    multiple ledgers (perf, CAS, acquisition, etc.).

    Args:
        ubv: Universal Budget Vector
        determinism_pass_rate: Determinism test pass rate (0.0-1.0)
        drift_free_rate: Drift-free rate (0.0-1.0)

    Returns:
        PortfolioMetrics
    """
    # Extract efficiency metrics (placeholders - in production, compute from ledgers)
    # For now, use default values
    avg_compression_ratio = 2.5  # Placeholder
    cache_hit_rate = 0.8  # Placeholder
    dedup_rate = 0.3  # Placeholder

    # Extract speed metrics from UBV
    latency_p95_ms = ubv.latency_p95_ms.measured
    avg_cpu_ms = ubv.cpu_ms.measured

    # Stability metrics
    # Budget satisfaction: how many dimensions are within budget?
    violations = ubv.budget_violations()
    total_dims = 9  # cpu, io_read, io_write, network_calls, network_bytes, latency, storage, decodo, risk
    hard_violations = sum(1 for v in violations if "exceeds hard limit" in v)
    soft_violations = sum(1 for v in violations if "exceeds budget" in v and "hard limit" not in v)
    satisfied_dims = total_dims - len(violations)
    budget_satisfaction_rate = satisfied_dims / total_dims if total_dims > 0 else 0.0

    return PortfolioMetrics(
        avg_compression_ratio=avg_compression_ratio,
        cache_hit_rate=cache_hit_rate,
        dedup_rate=dedup_rate,
        latency_p95_ms=latency_p95_ms,
        avg_cpu_ms=avg_cpu_ms,
        determinism_pass_rate=determinism_pass_rate,
        budget_satisfaction_rate=budget_satisfaction_rate,
        drift_free_rate=drift_free_rate,
        hard_violations=hard_violations,
        soft_violations=soft_violations,
    )
