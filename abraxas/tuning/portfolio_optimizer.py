"""Deterministic portfolio optimizer for cross-module tuning.

Universal Tuning Plane v0.4 - Portfolio-wide optimization with bounded search.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from abraxas.tuning.portfolio_ir import (
    PortfolioTuningIR,
    PortfolioProvenance,
    create_default_portfolio_ir,
)
from abraxas.tuning.portfolio_objectives import (
    PortfolioMetrics,
    PortfolioObjectiveWeights,
    compute_portfolio_objective,
    extract_portfolio_metrics_from_ubv,
    DEFAULT_WEIGHTS,
)
from abraxas.tuning.ubv import UniversalBudgetVector


@dataclass(frozen=True)
class PortfolioProposal:
    """Portfolio tuning proposal with predicted improvements."""

    ir: PortfolioTuningIR
    baseline_objective: float
    proposed_objective: float
    predicted_improvement: float  # Positive = better
    predicted_ubv_deltas: dict[str, float]  # Predicted changes per UBV dimension
    constraint_satisfaction_proof: dict[str, bool]  # Which constraints are satisfied
    risk_score: float  # 0.0 (low risk) to 1.0 (high risk)
    rationale: str


def propose_portfolio_tuning(
    *,
    ubv_measured: UniversalBudgetVector,
    baseline_ir: PortfolioTuningIR | None = None,
    weights: PortfolioObjectiveWeights = DEFAULT_WEIGHTS,
    run_id: str = "PORTFOLIO_OPTIMIZER",
    search_strategy: str = "grid_search",
) -> PortfolioProposal:
    """Propose portfolio tuning based on measured UBV.

    Uses deterministic optimization to search across all module knobs.

    Args:
        ubv_measured: Measured Universal Budget Vector
        baseline_ir: Current portfolio IR (defaults to default IR)
        weights: Objective weights
        run_id: Run identifier for provenance
        search_strategy: "grid_search" (only strategy for now)

    Returns:
        PortfolioProposal with candidate IR and predictions
    """
    # Extract baseline metrics from UBV
    baseline_metrics = extract_portfolio_metrics_from_ubv(ubv_measured)
    baseline_objective_value = compute_portfolio_objective(baseline_metrics, weights)

    # Use default IR as baseline if none provided
    if baseline_ir is None:
        baseline_ir = create_default_portfolio_ir(ubv_measured)

    # Deterministic grid search
    if search_strategy == "grid_search":
        candidate_ir, candidate_objective_value, predicted_deltas, constraints, risk_score, rationale = (
            _portfolio_grid_search(baseline_ir, ubv_measured, baseline_metrics, weights)
        )
    else:
        raise ValueError(f"Unknown search strategy: {search_strategy}")

    # Add provenance
    import hashlib
    import json

    ubv_dict = ubv_measured.to_dict()
    ubv_json = json.dumps(ubv_dict, sort_keys=True)
    ubv_hash = hashlib.sha256(ubv_json.encode()).hexdigest()

    candidate_ir.provenance = PortfolioProvenance(
        author="portfolio_optimizer",
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        derived_from_runs=[run_id],
        ledger_hashes=ubv_measured.ledger_hashes,
        baseline_ubv_hash=ubv_hash,
    )

    predicted_improvement = candidate_objective_value - baseline_objective_value

    return PortfolioProposal(
        ir=candidate_ir,
        baseline_objective=baseline_objective_value,
        proposed_objective=candidate_objective_value,
        predicted_improvement=predicted_improvement,
        predicted_ubv_deltas=predicted_deltas,
        constraint_satisfaction_proof=constraints,
        risk_score=risk_score,
        rationale=rationale,
    )


def _portfolio_grid_search(
    baseline_ir: PortfolioTuningIR,
    ubv: UniversalBudgetVector,
    baseline_metrics: PortfolioMetrics,
    weights: PortfolioObjectiveWeights,
) -> tuple[PortfolioTuningIR, float, dict[str, float], dict[str, bool], float, str]:
    """Grid search across portfolio knobs.

    Bounded search over module knobs in deterministic order.

    Args:
        baseline_ir: Starting portfolio IR
        ubv: Universal Budget Vector
        baseline_metrics: Baseline portfolio metrics
        weights: Objective weights

    Returns:
        Tuple of (best_ir, best_objective, predicted_deltas, constraints, risk_score, rationale)
    """
    best_ir = baseline_ir.model_copy(deep=True)
    best_objective = compute_portfolio_objective(baseline_metrics, weights)
    best_config = "baseline"
    improvements = []

    # Perf module knobs: zstd levels
    for hot_level in [1, 2, 3]:
        for cold_level in [3, 6, 9]:
            candidate_ir = baseline_ir.model_copy(deep=True)
            candidate_ir.module_knobs.perf.zstd_level_hot = hot_level
            candidate_ir.module_knobs.perf.zstd_level_cold = cold_level

            # Predict objective change (heuristic)
            # Lower hot = faster, higher cold = better compression
            predicted_objective = (
                best_objective + (3 - hot_level) * 0.05 + (cold_level - 3) * 0.03
            )

            if predicted_objective > best_objective:
                best_objective = predicted_objective
                best_ir = candidate_ir
                best_config = f"perf:hot={hot_level},cold={cold_level}"
                improvements.append(f"perf.zstd_hot={hot_level},cold={cold_level}")

    # Acquisition module knobs: batch window
    for window in ["daily", "weekly"]:
        candidate_ir = best_ir.model_copy(deep=True)
        candidate_ir.module_knobs.acquisition.batch_window_preferred = [window]

        # Predict: daily = more frequent (higher cost), weekly = less frequent (lower cost)
        cost_delta = -0.02 if window == "weekly" else 0.02
        predicted_objective = best_objective + cost_delta

        if predicted_objective > best_objective:
            best_objective = predicted_objective
            best_ir = candidate_ir
            best_config = f"acq:batch={window}"
            improvements.append(f"acquisition.batch={window}")

    # Pipeline module knobs: lazy load
    for lazy_load in [True, False]:
        candidate_ir = best_ir.model_copy(deep=True)
        candidate_ir.module_knobs.pipeline.lazy_load_packets = lazy_load

        # Predict: lazy = lower memory usage
        memory_delta = 0.01 if lazy_load else -0.01
        predicted_objective = best_objective + memory_delta

        if predicted_objective > best_objective:
            best_objective = predicted_objective
            best_ir = candidate_ir
            best_config = f"pipeline:lazy={lazy_load}"
            improvements.append(f"pipeline.lazy={lazy_load}")

    # Atlas module knobs: export granularity
    for granularity in ["weekly", "monthly"]:
        candidate_ir = best_ir.model_copy(deep=True)
        candidate_ir.module_knobs.atlas.export_granularity = granularity

        # Predict: monthly = less frequent (lower cost)
        cost_delta = 0.01 if granularity == "monthly" else 0.0
        predicted_objective = best_objective + cost_delta

        if predicted_objective > best_objective:
            best_objective = predicted_objective
            best_ir = candidate_ir
            best_config = f"atlas:granularity={granularity}"
            improvements.append(f"atlas.granularity={granularity}")

    # Predict UBV deltas (heuristic)
    predicted_deltas = {
        "cpu_ms": -5.0,  # Small improvement expected
        "latency_p95_ms": -10.0,  # Small latency improvement
        "storage_growth_bytes": -1000.0,  # Better compression
        "network_calls": 0.0,  # No change expected
        "decodo_calls": 0.0,  # No change expected
    }

    # Constraint satisfaction proof
    violations = ubv.budget_violations()
    constraints = {
        "no_hard_violations": not any("hard limit" in v for v in violations),
        "budget_satisfied": len(violations) == 0,
        "determinism_maintained": True,  # Grid search is deterministic
    }

    # Risk score based on number of changes
    risk_score = min(len(improvements) * 0.1, 0.8)

    rationale = (
        f"Portfolio grid search: {', '.join(improvements)}" if improvements else "No changes"
    )

    return best_ir, best_objective, predicted_deltas, constraints, risk_score, rationale
