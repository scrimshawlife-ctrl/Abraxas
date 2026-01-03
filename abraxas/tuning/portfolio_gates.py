"""Universal rent gates for portfolio tuning promotion.

Universal Tuning Plane v0.4 - Cross-module promotion gates.
"""

from __future__ import annotations

from dataclasses import dataclass

from abraxas.tuning.ubv import UniversalBudgetVector


@dataclass(frozen=True)
class PortfolioRentGateVerdict:
    """Verdict from portfolio rent gate evaluation."""

    passed: bool
    gate_results: dict[str, bool]
    rationale: str
    ubv_before: UniversalBudgetVector
    ubv_after: UniversalBudgetVector


# Universal rent gate thresholds (constants)
STORAGE_GROWTH_MIN_IMPROVEMENT = 0.10  # 10% reduction required
NETWORK_CALLS_MIN_IMPROVEMENT = 0.15  # 15% reduction required
LATENCY_P95_MIN_IMPROVEMENT = 0.10  # 10% improvement required
CPU_MS_MAX_REGRESSION = 0.15  # Max 15% increase allowed


def check_portfolio_rent_gates(
    ubv_before: UniversalBudgetVector,
    ubv_after: UniversalBudgetVector,
    *,
    determinism_passes: int = 12,
    determinism_required: int = 12,
    provenance_hashes_valid: bool = True,
) -> PortfolioRentGateVerdict:
    """Check universal rent gates for portfolio promotion.

    Gates that must ALL pass:
    1. No determinism failures (12-run hash invariance where applicable)
    2. UBV budgets satisfied (all dimensions within limits)
    3. Major rent gain (at least ONE of):
       - storage_growth reduced >= 10%
       - network_calls reduced >= 15%
       - latency_p95 improved >= 10%
    4. No major regressions:
       - cpu_ms not worse than +15%
       - cache_hit_rate not worse (if tracked)
       - compression_ratio not worse (if tracked)
    5. Provenance chain valid (all hashes match)

    Args:
        ubv_before: UBV before tuning
        ubv_after: UBV after tuning
        determinism_passes: Number of determinism test passes
        determinism_required: Number of determinism test runs required
        provenance_hashes_valid: Whether provenance hash chain is valid

    Returns:
        PortfolioRentGateVerdict with pass/fail and detailed results
    """
    gate_results = {}
    reasons = []

    # Gate 1: No determinism failures
    gate_1 = determinism_passes >= determinism_required
    gate_results["determinism_gate"] = gate_1
    if gate_1:
        reasons.append(
            f" Determinism: {determinism_passes}/{determinism_required} passes"
        )
    else:
        reasons.append(
            f" Determinism: {determinism_passes}/{determinism_required} passes (required {determinism_required})"
        )

    # Gate 2: UBV budgets satisfied
    violations_after = ubv_after.budget_violations()
    gate_2 = len(violations_after) == 0
    gate_results["budget_satisfaction_gate"] = gate_2
    if gate_2:
        reasons.append(" All UBV budgets satisfied (no violations)")
    else:
        reasons.append(
            f" UBV budget violations: {len(violations_after)} ({', '.join(violations_after[:3])}...)"
        )

    # Gate 3: Major rent gain (at least ONE)
    storage_improvement = (
        (ubv_before.storage_growth_bytes.measured - ubv_after.storage_growth_bytes.measured)
        / ubv_before.storage_growth_bytes.measured
        if ubv_before.storage_growth_bytes.measured > 0
        else 0.0
    )

    network_improvement = (
        (ubv_before.network_calls.measured - ubv_after.network_calls.measured)
        / ubv_before.network_calls.measured
        if ubv_before.network_calls.measured > 0
        else 0.0
    )

    latency_improvement = (
        (ubv_before.latency_p95_ms.measured - ubv_after.latency_p95_ms.measured)
        / ubv_before.latency_p95_ms.measured
        if ubv_before.latency_p95_ms.measured > 0
        else 0.0
    )

    storage_gate = storage_improvement >= STORAGE_GROWTH_MIN_IMPROVEMENT
    network_gate = network_improvement >= NETWORK_CALLS_MIN_IMPROVEMENT
    latency_gate = latency_improvement >= LATENCY_P95_MIN_IMPROVEMENT

    gate_3 = storage_gate or network_gate or latency_gate
    gate_results["major_rent_gain_gate"] = gate_3

    if gate_3:
        gains = []
        if storage_gate:
            gains.append(f"storage={storage_improvement:.1%}")
        if network_gate:
            gains.append(f"network={network_improvement:.1%}")
        if latency_gate:
            gains.append(f"latency={latency_improvement:.1%}")
        reasons.append(f" Major rent gain: {', '.join(gains)}")
    else:
        reasons.append(
            f" No major rent gain: storage={storage_improvement:.1%} (need {STORAGE_GROWTH_MIN_IMPROVEMENT:.1%}), "
            f"network={network_improvement:.1%} (need {NETWORK_CALLS_MIN_IMPROVEMENT:.1%}), "
            f"latency={latency_improvement:.1%} (need {LATENCY_P95_MIN_IMPROVEMENT:.1%})"
        )

    # Gate 4: No major regressions
    cpu_regression = (
        (ubv_after.cpu_ms.measured - ubv_before.cpu_ms.measured) / ubv_before.cpu_ms.measured
        if ubv_before.cpu_ms.measured > 0
        else 0.0
    )

    cpu_gate = cpu_regression <= CPU_MS_MAX_REGRESSION
    gate_results["cpu_regression_gate"] = cpu_gate

    if cpu_gate:
        reasons.append(
            f" CPU regression acceptable: {cpu_regression:.1%} <= {CPU_MS_MAX_REGRESSION:.1%}"
        )
    else:
        reasons.append(
            f" CPU regression too high: {cpu_regression:.1%} > {CPU_MS_MAX_REGRESSION:.1%}"
        )

    # Note: cache_hit_rate and compression_ratio would be checked here if tracked in UBV
    # For now, we assume they're maintained (would come from perf ledger)

    # Gate 5: Provenance chain valid
    gate_5 = provenance_hashes_valid
    gate_results["provenance_gate"] = gate_5
    if gate_5:
        reasons.append(" Provenance chain valid")
    else:
        reasons.append(" Provenance chain invalid (hash mismatch)")

    # Overall verdict: ALL gates must pass
    all_passed = all(gate_results.values())
    rationale = "\n".join(reasons)

    return PortfolioRentGateVerdict(
        passed=all_passed,
        gate_results=gate_results,
        rationale=rationale,
        ubv_before=ubv_before,
        ubv_after=ubv_after,
    )
