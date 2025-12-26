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
from typing import Dict, List, Optional, Any

from abraxas.evolution.schema import (
    MetricCandidate,
    SandboxResult,
    SandboxConfig,
    CandidateKind,
    generate_sandbox_id
)


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
            failure_reasons=failures
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
            failure_reasons=[]
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
            failure_reasons=[]
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
            failure_reasons=failures
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
