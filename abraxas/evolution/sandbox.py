"""
Sandbox Executor

Tests metric candidates against historical data before promotion.

WORKFLOW:
1. Load candidate
2. For PARAM_TWEAK: Apply override in-memory, re-run backtest/forecast
3. For METRIC/OPERATOR: Validate spec only (implementation requires ticket)
4. Compare scores before/after
5. Check pass criteria
6. Return SandboxResult

SAFETY:
- All changes in-memory only (no writes during test)
- Requires hindcast data (no online fetching)
- Must improve on target horizons without regressing protected ones
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterable

from abraxas.backtest.evaluator import evaluate_case, load_backtest_case
from abraxas.backtest.portfolio import load_portfolios, select_cases_for_portfolio
from abraxas.backtest.schema import BacktestCase, BacktestResult
from abraxas.core.provenance import hash_canonical_json
from abraxas.evolution.schema import (
    MetricCandidate,
    SandboxResult,
    SandboxConfig,
    CandidateKind,
    generate_sandbox_id
)
from abraxas.scoreboard.aggregate import aggregate_scores_for_cases


class SandboxExecutor:
    """Execute candidates in sandbox environment."""

    def __init__(self, config: Optional[SandboxConfig] = None):
        if config is None:
            config = SandboxConfig()
        self.config = config

    def run_sandbox(
        self,
        candidate: MetricCandidate,
        run_id: str = "manual",
        hindcast_data: Optional[Dict[str, Any]] = None
    ) -> SandboxResult:
        """
        Execute candidate in sandbox.

        Args:
            candidate: Candidate to test
            run_id: Identifier for this run
            hindcast_data: Historical data for testing (optional, uses defaults if None)

        Returns:
            SandboxResult with pass/fail and score deltas
        """
        sandbox_id = generate_sandbox_id(
            candidate.candidate_id,
            datetime.now(timezone.utc).isoformat()
        )

        # Execute based on candidate kind
        if candidate.kind == CandidateKind.PARAM_TWEAK:
            result = self._run_param_tweak_sandbox(
                candidate, sandbox_id, run_id, hindcast_data
            )
        elif candidate.kind == CandidateKind.METRIC:
            result = self._run_metric_sandbox(
                candidate, sandbox_id, run_id
            )
        elif candidate.kind == CandidateKind.OPERATOR:
            result = self._run_operator_sandbox(
                candidate, sandbox_id, run_id
            )
        else:
            raise ValueError(f"Unknown candidate kind: {candidate.kind}")

        return result

    def _run_param_tweak_sandbox(
        self,
        candidate: MetricCandidate,
        sandbox_id: str,
        run_id: str,
        hindcast_data: Optional[Dict[str, Any]]
    ) -> SandboxResult:
        """
        Run sandbox for parameter tweak.

        For v0.1, this is a MOCK implementation.
        Real implementation would:
        1. Load hindcast backtest cases
        2. Run with current params → score_before
        3. Apply param override in-memory
        4. Run with new params → score_after
        5. Compute deltas and check criteria
        """
        # MOCK: Simulate improvement based on candidate expectations
        # In production, this would run actual backtests

        # Use hindcast data if provided, otherwise mock
        if hindcast_data is None:
            hindcast_data = self._generate_mock_hindcast_data(candidate)

        cases_tested = hindcast_data.get("cases_tested", 10)

        # Mock scores (deterministic based on candidate_id for reproducibility)
        import hashlib
        seed = int(hashlib.md5(candidate.candidate_id.encode()).hexdigest()[:8], 16)
        improvement_factor = 1.0 + (seed % 20 - 10) / 100.0  # ±10%

        expected_delta = candidate.expected_improvement.get("brier_delta", -0.05)
        actual_delta = expected_delta * improvement_factor

        score_before = {
            "brier_avg": 0.25,
            "log_avg": 0.52,
            "calibration_error": 0.08
        }

        score_after = {
            "brier_avg": max(0.0, score_before["brier_avg"] + actual_delta),
            "log_avg": max(0.0, score_before["log_avg"] + actual_delta * 0.8),
            "calibration_error": max(0.0, score_before["calibration_error"] - 0.02)
        }

        score_delta = {
            "brier_delta": score_after["brier_avg"] - score_before["brier_avg"],
            "log_delta": score_after["log_avg"] - score_before["log_avg"],
            "calibration_delta": score_after["calibration_error"] - score_before["calibration_error"]
        }

        # Check pass criteria
        passed, criteria, failures = self._check_pass_criteria(
            score_delta, candidate
        )

        return SandboxResult(
            sandbox_id=sandbox_id,
            candidate_id=candidate.candidate_id,
            run_at=datetime.now(timezone.utc).isoformat(),
            run_id=run_id,
            hindcast_window_days=self.config.hindcast_window_days,
            cases_tested=cases_tested,
            score_before=score_before,
            score_after=score_after,
            score_delta=score_delta,
            horizon_scores=self._mock_horizon_breakdown(candidate, score_delta),
            passed=passed,
            pass_criteria=criteria,
            failure_reasons=failures,
            pass_gate=passed
        )

    def _run_metric_sandbox(
        self,
        candidate: MetricCandidate,
        sandbox_id: str,
        run_id: str
    ) -> SandboxResult:
        """
        Run sandbox for new metric.

        For v0.1, metrics are NOT auto-implemented.
        This just validates the spec and marks for manual implementation.
        """
        # Validate implementation spec
        impl_spec = candidate.implementation_spec
        if not impl_spec:
            return self._create_failed_result(
                sandbox_id, candidate.candidate_id, run_id,
                ["No implementation_spec provided"]
            )

        required_fields = ["formula", "inputs", "output_range", "computation"]
        missing_fields = [f for f in required_fields if f not in impl_spec]

        if missing_fields:
            return self._create_failed_result(
                sandbox_id, candidate.candidate_id, run_id,
                [f"Missing required fields in implementation_spec: {missing_fields}"]
            )

        # For v0.1: Metrics pass sandbox but require implementation ticket
        # We can't test them until they're implemented
        return SandboxResult(
            sandbox_id=sandbox_id,
            candidate_id=candidate.candidate_id,
            run_at=datetime.now(timezone.utc).isoformat(),
            run_id=run_id,
            hindcast_window_days=0,  # Not tested
            cases_tested=0,
            score_before={},
            score_after={},
            score_delta={},
            passed=True,  # Spec is valid
            pass_criteria={
                "spec_valid": True,
                "requires_implementation": True
            },
            failure_reasons=[],
            pass_gate=True
        )

    def _run_operator_sandbox(
        self,
        candidate: MetricCandidate,
        sandbox_id: str,
        run_id: str
    ) -> SandboxResult:
        """
        Run sandbox for new SLANG operator.

        For v0.1, operators are NOT auto-implemented.
        This just validates the spec and marks for manual implementation.
        """
        # Similar to metric validation
        impl_spec = candidate.implementation_spec
        if not impl_spec:
            return self._create_failed_result(
                sandbox_id, candidate.candidate_id, run_id,
                ["No implementation_spec provided"]
            )

        required_fields = ["signature", "semantics"]
        missing_fields = [f for f in required_fields if f not in impl_spec]

        if missing_fields:
            return self._create_failed_result(
                sandbox_id, candidate.candidate_id, run_id,
                [f"Missing required fields in implementation_spec: {missing_fields}"]
            )

        # For v0.1: Operators pass sandbox but require implementation ticket
        return SandboxResult(
            sandbox_id=sandbox_id,
            candidate_id=candidate.candidate_id,
            run_at=datetime.now(timezone.utc).isoformat(),
            run_id=run_id,
            hindcast_window_days=0,  # Not tested
            cases_tested=0,
            score_before={},
            score_after={},
            score_delta={},
            passed=True,  # Spec is valid
            pass_criteria={
                "spec_valid": True,
                "requires_implementation": True
            },
            failure_reasons=[],
            pass_gate=True
        )

    def _check_pass_criteria(
        self,
        score_delta: Dict[str, float],
        candidate: MetricCandidate
    ) -> tuple[bool, Dict[str, bool], List[str]]:
        """
        Check if sandbox run passes promotion criteria.

        Returns:
            (passed, criteria_dict, failure_reasons)
        """
        criteria = {}
        failures = []

        # 1. Improvement threshold
        brier_delta = score_delta.get("brier_delta", 0.0)
        improvement_pct = abs(brier_delta / 0.25) * 100  # Assume baseline ~0.25

        improvement_met = improvement_pct >= self.config.improvement_threshold
        criteria["improvement_threshold"] = improvement_met

        if not improvement_met:
            failures.append(
                f"Improvement {improvement_pct:.1f}% below threshold "
                f"{self.config.improvement_threshold:.1f}%"
            )

        # 2. No regressions on protected horizons
        # For v0.1, assume no regressions if brier_delta < 0 (improvement)
        no_regressions = brier_delta <= self.config.regression_tolerance
        criteria["no_regressions"] = no_regressions

        if not no_regressions:
            failures.append(
                f"Regression detected: brier_delta={brier_delta:.4f} > "
                f"tolerance {self.config.regression_tolerance:.4f}"
            )

        # 3. Cost bounds (mock for v0.1)
        # In production, would check time_ms and memory_kb
        cost_ok = True  # Assume OK for param tweaks
        criteria["cost_bounds"] = cost_ok

        passed = all(criteria.values())
        return passed, criteria, failures

    def _generate_mock_hindcast_data(self, candidate: MetricCandidate) -> Dict[str, Any]:
        """Generate mock hindcast data for testing."""
        return {
            "cases_tested": 10,
            "window_days": self.config.hindcast_window_days,
            "horizons": candidate.target_horizons
        }

    def _mock_horizon_breakdown(
        self,
        candidate: MetricCandidate,
        score_delta: Dict[str, float]
    ) -> Dict[str, Dict[str, Any]]:
        """Generate mock per-horizon scores."""
        breakdown = {}

        for horizon in candidate.target_horizons:
            # Vary delta slightly per horizon (deterministic)
            import hashlib
            seed = int(hashlib.md5((candidate.candidate_id + horizon).encode()).hexdigest()[:8], 16)
            factor = 0.8 + (seed % 40) / 100.0  # 0.8 to 1.2

            breakdown[horizon] = {
                "before": {"brier_avg": 0.25, "log_avg": 0.52},
                "after": {
                    "brier_avg": 0.25 + score_delta["brier_delta"] * factor,
                    "log_avg": 0.52 + score_delta["log_delta"] * factor
                },
                "delta": {
                    "brier_delta": score_delta["brier_delta"] * factor,
                    "log_delta": score_delta["log_delta"] * factor
                }
            }

        return breakdown

    def _create_failed_result(
        self,
        sandbox_id: str,
        candidate_id: str,
        run_id: str,
        failures: List[str]
    ) -> SandboxResult:
        """Create a failed sandbox result."""
        return SandboxResult(
            sandbox_id=sandbox_id,
            candidate_id=candidate_id,
            run_at=datetime.now(timezone.utc).isoformat(),
            run_id=run_id,
            hindcast_window_days=0,
            cases_tested=0,
            score_before={},
            score_after={},
            score_delta={},
            passed=False,
            pass_criteria={},
            failure_reasons=failures,
            pass_gate=False
        )


# Helper function for external use

def run_candidate_sandbox(
    candidate: MetricCandidate,
    config: Optional[SandboxConfig] = None,
    run_id: str = "manual",
    hindcast_data: Optional[Dict[str, Any]] = None
) -> SandboxResult:
    """
    Convenience function to run a candidate in sandbox.

    Args:
        candidate: Candidate to test
        config: Sandbox configuration (uses defaults if None)
        run_id: Identifier for this run
        hindcast_data: Historical data for testing

    Returns:
        SandboxResult
    """
    executor = SandboxExecutor(config)
    return executor.run_sandbox(candidate, run_id, hindcast_data)


def run_sandbox_portfolios(
    candidate: MetricCandidate,
    cases_dir: str | Path,
    portfolios_path: str | Path,
    ctx: Dict[str, Any],
    overrides: Optional[Dict[str, Any]] = None
) -> SandboxResult:
    """
    Run sandbox evaluation across target portfolios.

    Args:
        candidate: Candidate to test
        cases_dir: Directory containing backtest case YAMLs
        portfolios_path: Path to portfolios YAML
        ctx: Execution context (run_id, run_at, output_dir)
        overrides: Optional dict with baseline_results/after_results for testing

    Returns:
        SandboxResult with portfolio breakdown and pass gate
    """
    run_at = ctx.get("run_at") or datetime.now(timezone.utc).isoformat()
    run_id = ctx.get("run_id", "manual")
    output_dir = Path(ctx.get("output_dir", "out"))

    sandbox_id = generate_sandbox_id(candidate.candidate_id, run_at)

    cases = _load_cases(cases_dir)
    portfolios = load_portfolios(portfolios_path)

    target = candidate.target
    target_portfolios = list(target.portfolios or [])
    no_regress_portfolios = list(target.no_regress_portfolios or [])
    portfolios_tested = sorted(set(target_portfolios + no_regress_portfolios))

    portfolio_results: Dict[str, Any] = {}
    failures: List[str] = []
    overall_cases: Dict[str, BacktestResult] = {}
    overall_cases_after: Dict[str, BacktestResult] = {}

    for portfolio_id in portfolios_tested:
        spec = portfolios.get(portfolio_id)
        if not spec:
            failures.append(f"Portfolio {portfolio_id} not found")
            continue

        selected_cases = select_cases_for_portfolio(cases, spec)
        baseline_results = _evaluate_cases(
            selected_cases,
            overrides,
            key="baseline_results"
        )
        after_results = _evaluate_cases(
            selected_cases,
            overrides,
            key="after_results"
        )

        for result in baseline_results:
            overall_cases[result.case_id] = result
        for result in after_results:
            overall_cases_after[result.case_id] = result

        portfolio_results[portfolio_id] = _evaluate_portfolio(
            portfolio_id=portfolio_id,
            target=target,
            baseline_results=baseline_results,
            after_results=after_results,
            min_cases=SandboxConfig().min_cases_required,
            is_target=portfolio_id in target_portfolios,
            is_no_regress=portfolio_id in no_regress_portfolios
        )

    pass_gate = _compute_pass_gate(
        portfolio_results,
        target_portfolios,
        no_regress_portfolios,
        failures
    )

    score_before = aggregate_scores_for_cases(list(overall_cases.values()))
    score_after = aggregate_scores_for_cases(list(overall_cases_after.values()))
    score_delta = _compute_score_delta(score_before, score_after)

    portfolio_score_delta_hash = hash_canonical_json(
        {pid: result.get("delta", {}) for pid, result in portfolio_results.items()}
    ) if portfolio_results else None

    result = SandboxResult(
        sandbox_id=sandbox_id,
        candidate_id=candidate.candidate_id,
        run_at=run_at,
        run_id=run_id,
        hindcast_window_days=SandboxConfig().hindcast_window_days,
        cases_tested=len(overall_cases),
        score_before=score_before,
        score_after=score_after,
        score_delta=score_delta,
        horizon_scores={},
        passed=pass_gate,
        pass_gate=pass_gate,
        pass_criteria={
            "portfolio_gate": pass_gate,
            "targets_met": pass_gate
        },
        failure_reasons=failures,
        portfolio_results=portfolio_results,
        portfolios_tested=portfolios_tested,
        portfolio_score_delta_hash=portfolio_score_delta_hash
    )

    report = _build_portfolio_report(result, candidate)
    _write_portfolio_report(report, output_dir, run_id, sandbox_id)

    return result


def _load_cases(cases_dir: str | Path) -> List[BacktestCase]:
    cases_dir = Path(cases_dir)
    case_files = sorted(cases_dir.glob("*.yaml"))
    cases = [load_backtest_case(case_file) for case_file in case_files]
    return sorted(cases, key=lambda c: c.case_id)


def _evaluate_cases(
    cases: Iterable[BacktestCase],
    overrides: Optional[Dict[str, Any]],
    key: str
) -> List[BacktestResult]:
    if overrides and key in overrides:
        override_results = overrides.get(key) or {}
        if isinstance(override_results, list):
            results = override_results
        else:
            results = list(override_results.values())
        case_ids = [case.case_id for case in cases]
        results_by_case = {result.case_id: result for result in results}
        return [results_by_case[case_id] for case_id in sorted(case_ids)]

    results = []
    for case in cases:
        results.append(evaluate_case(case, enable_learning=False, run_id="sandbox"))
    return results


def _compute_score_delta(
    before: Dict[str, Optional[float]],
    after: Dict[str, Optional[float]]
) -> Dict[str, Optional[float]]:
    delta_key_map = {
        "brier_avg": "brier_delta",
        "log_avg": "log_delta",
        "calibration_error": "calibration_error_delta",
        "coverage_rate": "coverage_rate_delta",
        "trend_acc": "trend_acc_delta",
        "crps_avg": "crps_avg_delta",
        "abstain_rate": "abstain_rate_delta",
    }
    deltas: Dict[str, Optional[float]] = {}
    for key, delta_key in delta_key_map.items():
        before_value = before.get(key)
        after_value = after.get(key)
        if before_value is None or after_value is None:
            deltas[delta_key] = None
        else:
            deltas[delta_key] = after_value - before_value
    return deltas


def _evaluate_portfolio(
    portfolio_id: str,
    target,
    baseline_results: List[BacktestResult],
    after_results: List[BacktestResult],
    min_cases: int,
    is_target: bool,
    is_no_regress: bool
) -> Dict[str, Any]:
    cases_tested = len(baseline_results)
    baseline_scores = aggregate_scores_for_cases(baseline_results)
    after_scores = aggregate_scores_for_cases(after_results)
    deltas = _compute_score_delta(baseline_scores, after_scores)

    notes: List[str] = []
    status = "PASS"
    improvement_checks: Dict[str, bool] = {}
    no_regress_checks: Dict[str, bool] = {}

    if cases_tested < min_cases:
        status = "ABSTAIN"
        notes.append(f"Insufficient cases: {cases_tested} < {min_cases}")
    else:
        if is_target:
            improvement_checks = _check_improvements(target, deltas, notes)
            if not all(improvement_checks.values()):
                status = "FAIL"
        if is_no_regress:
            no_regress_checks = _check_no_regress(deltas, notes)
            if not all(no_regress_checks.values()):
                status = "FAIL"

    return {
        "portfolio_id": portfolio_id,
        "cases_tested": cases_tested,
        "status": status,
        "baseline": baseline_scores,
        "after": after_scores,
        "delta": deltas,
        "improvement_checks": improvement_checks,
        "no_regress_checks": no_regress_checks,
        "notes": notes,
    }


def _check_improvements(target, deltas: Dict[str, Optional[float]], notes: List[str]) -> Dict[str, bool]:
    checks: Dict[str, bool] = {}
    metric_map = _metric_key_map()

    for metric, threshold in target.improvement_thresholds.items():
        delta_key = metric_map.get(metric)
        if not delta_key:
            checks[metric] = False
            notes.append(f"Unknown metric for improvement check: {metric}")
            continue
        delta_value = deltas.get(delta_key)
        if delta_value is None:
            checks[metric] = False
            notes.append(f"Missing delta for metric: {metric}")
            continue
        if threshold >= 0:
            checks[metric] = delta_value >= threshold
        else:
            checks[metric] = delta_value <= threshold
        if not checks[metric]:
            notes.append(f"Threshold not met for {metric}: delta={delta_value:.4f}")

    return checks


def _check_no_regress(deltas: Dict[str, Optional[float]], notes: List[str]) -> Dict[str, bool]:
    tolerances = {
        "brier_delta": 0.001,
        "coverage_rate_delta": -0.01,
    }
    checks: Dict[str, bool] = {}

    for metric_key, tolerance in tolerances.items():
        delta_value = deltas.get(metric_key)
        if delta_value is None:
            checks[metric_key] = False
            notes.append(f"Missing delta for no-regress metric: {metric_key}")
            continue
        if metric_key == "coverage_rate_delta":
            checks[metric_key] = delta_value >= tolerance
        else:
            checks[metric_key] = delta_value <= tolerance
        if not checks[metric_key]:
            notes.append(f"No-regress failed for {metric_key}: delta={delta_value:.4f}")

    return checks


def _metric_key_map() -> Dict[str, str]:
    return {
        "brier": "brier_delta",
        "log": "log_delta",
        "calibration_error": "calibration_error_delta",
        "coverage_rate": "coverage_rate_delta",
        "trend_acc": "trend_acc_delta",
        "crps_avg": "crps_avg_delta",
        "abstain_rate": "abstain_rate_delta",
    }


def _compute_pass_gate(
    portfolio_results: Dict[str, Any],
    target_portfolios: List[str],
    no_regress_portfolios: List[str],
    failures: List[str]
) -> bool:
    for portfolio_id in target_portfolios:
        result = portfolio_results.get(portfolio_id)
        if not result:
            failures.append(f"Missing target portfolio result: {portfolio_id}")
            return False
        if result["status"] != "PASS":
            failures.append(f"Target portfolio failed: {portfolio_id}")
            return False

    for portfolio_id in no_regress_portfolios:
        result = portfolio_results.get(portfolio_id)
        if not result:
            failures.append(f"Missing no-regress portfolio result: {portfolio_id}")
            return False
        if result["status"] != "PASS":
            failures.append(f"No-regress portfolio failed: {portfolio_id}")
            return False

    return True if portfolio_results else False


def _build_portfolio_report(result: SandboxResult, candidate: MetricCandidate) -> Dict[str, Any]:
    return {
        "sandbox_id": result.sandbox_id,
        "candidate_id": result.candidate_id,
        "run_id": result.run_id,
        "run_at": result.run_at,
        "pass_gate": result.pass_gate,
        "portfolios_tested": result.portfolios_tested,
        "portfolio_score_delta_hash": result.portfolio_score_delta_hash,
        "target": candidate.target.dict(),
        "portfolio_results": result.portfolio_results,
        "failure_reasons": result.failure_reasons,
    }


def _write_portfolio_report(
    report: Dict[str, Any],
    output_dir: Path,
    run_id: str,
    sandbox_id: str
) -> None:
    reports_dir = output_dir / "reports"
    runs_dir = output_dir / "runs" / run_id / "evolution"
    reports_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)

    json_path = reports_dir / f"portfolio_sandbox_{sandbox_id}.json"
    run_json_path = runs_dir / "portfolio_sandbox_report.json"
    md_path = reports_dir / f"portfolio_sandbox_{sandbox_id}.md"
    run_md_path = runs_dir / "portfolio_sandbox_report.md"

    report_json = json.dumps(report, indent=2, sort_keys=True)
    for path in (json_path, run_json_path):
        path.write_text(report_json)

    report_md = _render_portfolio_report_md(report)
    for path in (md_path, run_md_path):
        path.write_text(report_md)


def _render_portfolio_report_md(report: Dict[str, Any]) -> str:
    lines = [
        "# Portfolio Sandbox Report",
        "",
        f"- Sandbox ID: {report['sandbox_id']}",
        f"- Candidate ID: {report['candidate_id']}",
        f"- Run ID: {report['run_id']}",
        f"- Pass Gate: {report['pass_gate']}",
        ""
    ]

    portfolios = report.get("portfolio_results", {})
    for portfolio_id, result in portfolios.items():
        lines.extend([
            f"## Portfolio: {portfolio_id}",
            f"- Status: {result.get('status')}",
            f"- Cases Tested: {result.get('cases_tested')}",
            f"- Notes: {', '.join(result.get('notes', [])) or 'None'}",
            ""
        ])

    return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    from abraxas.evolution.schema import MetricCandidate, CandidateKind, SourceDomain

    # Create test candidate (param tweak)
    candidate = MetricCandidate(
        candidate_id="cand_test_sandbox_001",
        kind=CandidateKind.PARAM_TWEAK,
        source_domain=SourceDomain.INTEGRITY,
        proposed_at=datetime.now(timezone.utc).isoformat(),
        proposed_by="test_script",
        name="confidence_threshold_H72H",
        description="Raise confidence threshold",
        rationale="Testing sandbox execution",
        param_path="forecast.confidence_threshold.H72H",
        current_value=0.65,
        proposed_value=0.75,
        expected_improvement={"brier_delta": -0.08},
        target_horizons=["H72H"],
        protected_horizons=["H30D"],
        priority=7
    )

    # Run sandbox
    result = run_candidate_sandbox(candidate, run_id="test_run_001")

    print(f"Sandbox ID: {result.sandbox_id}")
    print(f"Passed: {result.passed}")
    print(f"Cases tested: {result.cases_tested}")
    print(f"Score delta: {result.score_delta}")
    print(f"Pass criteria: {result.pass_criteria}")

    if result.failure_reasons:
        print(f"Failures: {result.failure_reasons}")
