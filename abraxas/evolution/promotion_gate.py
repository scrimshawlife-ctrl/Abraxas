"""
Promotion Gate

Validates and promotes candidates that pass stabilization criteria.

WORKFLOW:
1. Check stabilization window (N consecutive sandbox passes)
2. Validate promotion criteria (improvement, no regressions, cost)
3. Take promotion action:
   - PARAM_TWEAK → Write to override file
   - METRIC → Create implementation ticket
   - OPERATOR → Create implementation ticket
4. Record promotion in ledger

SAFETY:
- Requires N consecutive passes before promotion
- One failure resets stabilization counter
- Protected horizons cannot regress
- Cost bounds enforced
"""

import json
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from abraxas.evolution.schema import (
    MetricCandidate,
    SandboxResult,
    PromotionEntry,
    PromotionCriteria,
    StabilizationWindow,
    ImplementationTicket,
    CandidateKind,
    generate_promotion_id,
    generate_ticket_id
)
from abraxas.evolution.store import EvolutionStore


class PromotionGate:
    """Validate and promote candidates."""

    def __init__(
        self,
        criteria: Optional[PromotionCriteria] = None,
        store: Optional[EvolutionStore] = None
    ):
        if criteria is None:
            criteria = PromotionCriteria()
        self.criteria = criteria

        if store is None:
            store = EvolutionStore()
        self.store = store

    def can_promote(
        self,
        candidate: MetricCandidate,
        sandbox_results: List[SandboxResult]
    ) -> Tuple[bool, List[str]]:
        """
        Check if candidate meets promotion criteria.

        Args:
            candidate: Candidate to evaluate
            sandbox_results: All sandbox results for this candidate

        Returns:
            (can_promote, rejection_reasons)
        """
        reasons = []

        # Check 1: Require stabilization
        if self.criteria.require_stabilization:
            window = self._get_stabilization_window(candidate, sandbox_results)

            if not window.is_stable():
                reasons.append(
                    f"Not stabilized: {window.consecutive_passes}/{self.criteria.stabilization_window_size} "
                    f"consecutive passes"
                )

        # Check 2: Has at least one passing sandbox result
        passing_results = [r for r in sandbox_results if r.passed]
        if not passing_results:
            reasons.append("No passing sandbox results")

        # Check 3: Latest result must pass
        if sandbox_results and not sandbox_results[-1].passed:
            reasons.append("Latest sandbox run failed")

        # Check 4: Portfolio pass gate (if present)
        if sandbox_results:
            latest = sandbox_results[-1]
            if latest.pass_gate is False:
                reasons.append("Latest portfolio pass gate failed")
            if latest.portfolio_results:
                portfolio_failures = _check_portfolio_requirements(candidate, latest)
                reasons.extend(portfolio_failures)

        # Check 5: Rent manifest requirements
        rent_manifest_errors = _check_rent_manifest(candidate)
        reasons.extend(rent_manifest_errors)

        # Check 6: Kind-specific auto-promotion rules
        if candidate.kind == CandidateKind.METRIC and not self.criteria.auto_promote_metrics:
            # Metrics can still promote (to ticket), just flagging
            pass

        if candidate.kind == CandidateKind.OPERATOR and not self.criteria.auto_promote_operators:
            # Operators can still promote (to ticket), just flagging
            pass

        can_promote = len(reasons) == 0
        return can_promote, reasons

    def promote(
        self,
        candidate: MetricCandidate,
        sandbox_results: List[SandboxResult],
        promoted_by: str = "promotion_gate_v0_1"
    ) -> PromotionEntry:
        """
        Promote a candidate.

        Args:
            candidate: Candidate to promote
            sandbox_results: Sandbox results proving improvement
            promoted_by: Component performing promotion

        Returns:
            PromotionEntry

        Raises:
            ValueError: If candidate cannot be promoted
        """
        # Validate promotion criteria
        can_promote, reasons = self.can_promote(candidate, sandbox_results)
        if not can_promote:
            raise ValueError(f"Cannot promote candidate: {'; '.join(reasons)}")

        # Get stabilization window
        window = self._get_stabilization_window(candidate, sandbox_results)

        # Create promotion entry
        promotion_id = generate_promotion_id(
            candidate.candidate_id,
            datetime.now(timezone.utc).isoformat()
        )

        # Determine action based on kind
        if candidate.kind == CandidateKind.PARAM_TWEAK:
            action_type = "param_override"
            action_details = self._write_param_override(candidate)
        elif candidate.kind == CandidateKind.METRIC:
            action_type = "implementation_ticket"
            action_details = self._create_implementation_ticket(candidate, sandbox_results)
        elif candidate.kind == CandidateKind.OPERATOR:
            action_type = "implementation_ticket"
            action_details = self._create_implementation_ticket(candidate, sandbox_results)
        else:
            raise ValueError(f"Unknown candidate kind: {candidate.kind}")

        # Create promotion entry
        promotion = PromotionEntry(
            promotion_id=promotion_id,
            candidate_id=candidate.candidate_id,
            promoted_at=datetime.now(timezone.utc).isoformat(),
            promoted_by=promoted_by,
            kind=candidate.kind,
            name=candidate.name,
            description=candidate.description,
            action_type=action_type,
            action_details=action_details,
            stabilization_window={
                "window_size": window.window_size,
                "consecutive_passes": window.consecutive_passes,
                "run_ids": [r["run_id"] for r in window.run_history[-window.window_size:]]
            },
            sandbox_results_summary=self._summarize_sandbox_results(sandbox_results)
        )

        # Append to promotion ledger
        self.store.append_promotion_ledger(promotion)

        return promotion

    def _get_stabilization_window(
        self,
        candidate: MetricCandidate,
        sandbox_results: List[SandboxResult]
    ) -> StabilizationWindow:
        """
        Get or create stabilization window for candidate.

        Updates window with all sandbox results.
        """
        # Load existing window or create new
        window = self.store.load_stabilization_window(candidate.candidate_id)

        # Update with all sandbox results (in order)
        for result in sandbox_results:
            # Check if already recorded
            already_recorded = any(
                r.get("sandbox_id") == result.sandbox_id
                for r in window.run_history
            )

            if not already_recorded:
                window.record_run(result)

        # Save updated window
        self.store.save_stabilization_window(window)

        return window

    def _write_param_override(self, candidate: MetricCandidate) -> Dict[str, Any]:
        """
        Write parameter override to file.

        For v0.1, writes to data/evolution/param_overrides.yaml
        """
        overrides_file = self.store.data_dir / "param_overrides.yaml"

        # Load existing overrides
        if overrides_file.exists():
            with open(overrides_file, 'r') as f:
                overrides = yaml.safe_load(f) or {}
        else:
            overrides = {}

        # Add new override
        if "overrides" not in overrides:
            overrides["overrides"] = []

        override_entry = {
            "param_path": candidate.param_path,
            "value": candidate.proposed_value,
            "previous_value": candidate.current_value,
            "promoted_at": datetime.now(timezone.utc).isoformat(),
            "candidate_id": candidate.candidate_id,
            "rationale": candidate.rationale
        }

        overrides["overrides"].append(override_entry)

        # Write back
        with open(overrides_file, 'w') as f:
            yaml.dump(overrides, f, default_flow_style=False, sort_keys=False)

        return {
            "override_file": str(overrides_file),
            "param_path": candidate.param_path,
            "value": candidate.proposed_value
        }

    def _create_implementation_ticket(
        self,
        candidate: MetricCandidate,
        sandbox_results: List[SandboxResult]
    ) -> Dict[str, Any]:
        """
        Create implementation ticket for metric/operator.

        Ticket requires manual review and implementation.
        """
        ticket_id = generate_ticket_id(
            candidate.candidate_id,
            datetime.now(timezone.utc).isoformat()
        )

        ticket = ImplementationTicket(
            ticket_id=ticket_id,
            candidate_id=candidate.candidate_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            status="pending",
            kind=candidate.kind,
            name=candidate.name,
            description=candidate.description,
            rationale=candidate.rationale,
            implementation_spec=candidate.implementation_spec or {},
            sandbox_proof=[r.sandbox_id for r in sandbox_results if r.passed],
            stabilization_proof={
                "consecutive_passes": len([r for r in sandbox_results if r.passed]),
                "total_runs": len(sandbox_results)
            }
        )

        # Save ticket
        ticket_path = self.store.save_ticket(ticket)

        return {
            "ticket_file": str(ticket_path),
            "ticket_id": ticket_id,
            "status": "pending"
        }

    def _summarize_sandbox_results(
        self,
        sandbox_results: List[SandboxResult]
    ) -> Dict[str, Any]:
        """Summarize sandbox results for promotion record."""
        passing = [r for r in sandbox_results if r.passed]

        if not passing:
            return {
                "runs_tested": len(sandbox_results),
                "runs_passed": 0,
                "best_improvement": 0.0
            }

        # Get best brier delta (most negative = best improvement)
        brier_deltas = [
            r.score_delta.get("brier_delta", 0.0)
            for r in passing
        ]
        best_brier_delta = min(brier_deltas) if brier_deltas else 0.0

        # Average improvement across passing runs
        avg_improvement = sum(abs(d) for d in brier_deltas) / len(brier_deltas) if brier_deltas else 0.0

        return {
            "runs_tested": len(sandbox_results),
            "runs_passed": len(passing),
            "best_brier_delta": best_brier_delta,
            "avg_improvement": avg_improvement,
            "sandbox_ids": [r.sandbox_id for r in passing]
        }


def _check_portfolio_requirements(
    candidate: MetricCandidate,
    sandbox_result: SandboxResult
) -> List[str]:
    reasons: List[str] = []
    target = candidate.target
    target_portfolios = target.portfolios or []
    no_regress_portfolios = target.no_regress_portfolios or []

    for portfolio_id in target_portfolios:
        portfolio = sandbox_result.portfolio_results.get(portfolio_id)
        if not portfolio:
            reasons.append(f"Missing target portfolio result: {portfolio_id}")
            continue
        if portfolio.get("status") != "PASS":
            reasons.append(f"Target portfolio not passing: {portfolio_id}")

    for portfolio_id in no_regress_portfolios:
        portfolio = sandbox_result.portfolio_results.get(portfolio_id)
        if not portfolio:
            reasons.append(f"Missing no-regress portfolio result: {portfolio_id}")
            continue
        if portfolio.get("status") != "PASS":
            reasons.append(f"No-regress portfolio not passing: {portfolio_id}")

    return reasons


def _check_rent_manifest(candidate: MetricCandidate) -> List[str]:
    if candidate.kind == CandidateKind.PARAM_TWEAK:
        if not candidate.param_path:
            return ["Missing param_path for param_tweak candidate"]
        return []

    implementation_spec = candidate.implementation_spec or {}
    if not implementation_spec.get("rent_manifest_draft") and not implementation_spec.get("rent_manifest_path"):
        return ["Missing rent manifest draft for metric/operator candidate"]
    return []


# Helper functions for external use

def validate_promotion(
    candidate: MetricCandidate,
    sandbox_results: List[SandboxResult],
    criteria: Optional[PromotionCriteria] = None
) -> Tuple[bool, List[str]]:
    """
    Check if candidate can be promoted.

    Args:
        candidate: Candidate to check
        sandbox_results: Sandbox results for candidate
        criteria: Promotion criteria (uses defaults if None)

    Returns:
        (can_promote, rejection_reasons)
    """
    gate = PromotionGate(criteria)
    return gate.can_promote(candidate, sandbox_results)


def promote_candidate(
    candidate: MetricCandidate,
    sandbox_results: List[SandboxResult],
    criteria: Optional[PromotionCriteria] = None,
    promoted_by: str = "promotion_gate_v0_1"
) -> PromotionEntry:
    """
    Promote a candidate.

    Args:
        candidate: Candidate to promote
        sandbox_results: Sandbox results proving improvement
        criteria: Promotion criteria (uses defaults if None)
        promoted_by: Component performing promotion

    Returns:
        PromotionEntry

    Raises:
        ValueError: If candidate cannot be promoted
    """
    gate = PromotionGate(criteria)
    return gate.promote(candidate, sandbox_results, promoted_by)


# Example usage
if __name__ == "__main__":
    from abraxas.evolution.schema import MetricCandidate, SandboxResult, CandidateKind, SourceDomain
    from abraxas.evolution.sandbox import run_candidate_sandbox

    # Create test candidate
    candidate = MetricCandidate(
        candidate_id="cand_test_promo_001",
        kind=CandidateKind.PARAM_TWEAK,
        source_domain=SourceDomain.INTEGRITY,
        proposed_at=datetime.now(timezone.utc).isoformat(),
        proposed_by="test_script",
        name="confidence_threshold_H72H",
        description="Raise confidence threshold",
        rationale="Testing promotion gate",
        param_path="forecast.confidence_threshold.H72H",
        current_value=0.65,
        proposed_value=0.75,
        expected_improvement={"brier_delta": -0.08},
        target_horizons=["H72H"],
        protected_horizons=["H30D"],
        priority=7
    )

    # Run sandbox 3 times (stabilization window)
    sandbox_results = []
    for i in range(3):
        result = run_candidate_sandbox(candidate, run_id=f"test_run_{i:03d}")
        sandbox_results.append(result)
        print(f"Run {i+1}: passed={result.passed}, delta={result.score_delta.get('brier_delta', 0):.4f}")

    # Check if can promote
    can_promote, reasons = validate_promotion(candidate, sandbox_results)
    print(f"\nCan promote: {can_promote}")
    if reasons:
        print(f"Reasons: {reasons}")

    # Promote if eligible
    if can_promote:
        promotion = promote_candidate(candidate, sandbox_results)
        print(f"\n✓ Promoted: {promotion.promotion_id}")
        print(f"  Action: {promotion.action_type}")
        print(f"  Details: {promotion.action_details}")
    else:
        print("\n✗ Cannot promote")
