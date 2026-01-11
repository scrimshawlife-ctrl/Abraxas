"""Deterministic optimizer for performance tuning.

Performance Tuning Plane v0.1 - Grid search / coordinate descent for tuning proposals.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from abraxas.tuning.objectives import (
    RentMetrics,
    TuningObjective,
    compute_objective,
    compute_rent_metrics,
    DEFAULT_OBJECTIVE,
)
from abraxas.tuning.perf_ir import PerfTuningIR, create_default_ir
from abraxas.tuning.schema import TuningProvenance


@dataclass(frozen=True)
class TuningProposal:
    """Tuning proposal with predicted improvements."""

    ir: PerfTuningIR
    baseline_objective: float
    proposed_objective: float
    predicted_improvement: float  # Positive = better
    risk_score: float  # 0.0 (low risk) to 1.0 (high risk)
    rationale: str


def propose_tuning(
    *,
    baseline_ir: PerfTuningIR | None = None,
    window_hours: int = 168,
    objective: TuningObjective = DEFAULT_OBJECTIVE,
    run_id: str = "OPTIMIZER",
    search_strategy: str = "greedy_coordinate_descent",
) -> TuningProposal:
    """Propose performance tuning based on perf ledger evidence.

    Uses deterministic optimization to search for better tuning configurations.

    Args:
        baseline_ir: Current tuning IR (defaults to default IR)
        window_hours: Window for computing rent metrics (default: 168 = 7 days)
        objective: TuningObjective with weights
        run_id: Run identifier for provenance
        search_strategy: "grid_search" or "greedy_coordinate_descent"

    Returns:
        TuningProposal with candidate IR and predicted improvements
    """
    # Compute baseline metrics
    baseline_metrics = compute_rent_metrics(window_hours=window_hours)
    baseline_objective_value = compute_objective(baseline_metrics, objective)

    # Use default IR as baseline if none provided
    if baseline_ir is None:
        baseline_ir = create_default_ir()

    # Deterministic search based on strategy
    if search_strategy == "greedy_coordinate_descent":
        candidate_ir, candidate_objective_value, risk_score, rationale = (
            _greedy_coordinate_descent(baseline_ir, baseline_metrics, objective)
        )
    elif search_strategy == "grid_search":
        candidate_ir, candidate_objective_value, risk_score, rationale = _grid_search(
            baseline_ir, baseline_metrics, objective
        )
    else:
        raise ValueError(f"Unknown search strategy: {search_strategy}")

    # Add provenance
    candidate_ir.provenance = TuningProvenance(
        author="autotune",
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        derived_from_runs=[run_id],
        ledger_hashes=[],  # Could add ledger file hash here
    )

    predicted_improvement = candidate_objective_value - baseline_objective_value

    return TuningProposal(
        ir=candidate_ir,
        baseline_objective=baseline_objective_value,
        proposed_objective=candidate_objective_value,
        predicted_improvement=predicted_improvement,
        risk_score=risk_score,
        rationale=rationale,
    )


def _greedy_coordinate_descent(
    baseline_ir: PerfTuningIR,
    metrics: RentMetrics,
    objective: TuningObjective,
) -> tuple[PerfTuningIR, float, float, str]:
    """Greedy coordinate descent search.

    Iterates through knobs in fixed order, selecting best improvement per knob.

    Args:
        baseline_ir: Starting IR
        metrics: Current rent metrics
        objective: Objective function

    Returns:
        Tuple of (best_ir, best_objective, risk_score, rationale)
    """
    current_ir = baseline_ir.model_copy(deep=True)
    current_objective = compute_objective(metrics, objective)

    improvements = []

    # Knob 1: zstd_level_hot (try 1, 2, 3)
    best_level_hot = current_ir.knobs.zstd_level_hot
    for level in [1, 2, 3]:
        candidate_ir = current_ir.model_copy(deep=True)
        candidate_ir.knobs.zstd_level_hot = level
        # Predict objective (heuristic: lower level = faster, lower ratio)
        predicted_objective = current_objective + (best_level_hot - level) * 0.1
        if predicted_objective > current_objective:
            current_objective = predicted_objective
            best_level_hot = level
            improvements.append(f"zstd_level_hot={level}")

    current_ir.knobs.zstd_level_hot = best_level_hot

    # Knob 2: zstd_level_cold (try 3, 6, 9)
    best_level_cold = current_ir.knobs.zstd_level_cold
    for level in [3, 6, 9]:
        candidate_ir = current_ir.model_copy(deep=True)
        candidate_ir.knobs.zstd_level_cold = level
        # Predict objective (heuristic: higher level = better ratio, slower)
        predicted_objective = current_objective + (level - best_level_cold) * 0.05
        if predicted_objective > current_objective:
            current_objective = predicted_objective
            best_level_cold = level
            improvements.append(f"zstd_level_cold={level}")

    current_ir.knobs.zstd_level_cold = best_level_cold

    # Knob 3: dict_enabled (try True, False)
    if not current_ir.knobs.dict_enabled and len(metrics.avg_compression_ratio_by_source) > 0:
        # If dict is disabled and we have repetitive data, enable it
        avg_ratio = sum(metrics.avg_compression_ratio_by_source.values()) / len(
            metrics.avg_compression_ratio_by_source
        )
        if avg_ratio > 2.0:  # Good compression suggests dict would help
            current_ir.knobs.dict_enabled = True
            current_objective += 0.2
            improvements.append("dict_enabled=True")

    # Risk score: more changes = higher risk
    risk_score = min(len(improvements) * 0.15, 1.0)

    rationale = (
        f"Greedy coordinate descent: {', '.join(improvements)}" if improvements else "No changes"
    )

    return current_ir, current_objective, risk_score, rationale


def _grid_search(
    baseline_ir: PerfTuningIR,
    metrics: RentMetrics,
    objective: TuningObjective,
) -> tuple[PerfTuningIR, float, float, str]:
    """Grid search over bounded knob space.

    Evaluates all combinations of a small grid.

    Args:
        baseline_ir: Starting IR
        metrics: Current rent metrics
        objective: Objective function

    Returns:
        Tuple of (best_ir, best_objective, risk_score, rationale)
    """
    best_ir = baseline_ir.model_copy(deep=True)
    best_objective = compute_objective(metrics, objective)
    best_config = "baseline"

    # Grid: zstd_level_hot in [1, 2, 3], zstd_level_cold in [3, 6, 9]
    for hot_level in [1, 2, 3]:
        for cold_level in [3, 6, 9]:
            candidate_ir = baseline_ir.model_copy(deep=True)
            candidate_ir.knobs.zstd_level_hot = hot_level
            candidate_ir.knobs.zstd_level_cold = cold_level

            # Heuristic objective prediction
            predicted_objective = (
                best_objective + (3 - hot_level) * 0.1 + (cold_level - 3) * 0.05
            )

            if predicted_objective > best_objective:
                best_objective = predicted_objective
                best_ir = candidate_ir
                best_config = f"hot={hot_level},cold={cold_level}"

    # Risk score based on deviation from baseline
    baseline_config = (
        baseline_ir.knobs.zstd_level_hot,
        baseline_ir.knobs.zstd_level_cold,
    )
    best_config_tuple = (best_ir.knobs.zstd_level_hot, best_ir.knobs.zstd_level_cold)
    risk_score = (
        0.5 if best_config_tuple != baseline_config else 0.0
    )  # Higher risk if changed

    rationale = f"Grid search: selected {best_config}"

    return best_ir, best_objective, risk_score, rationale
