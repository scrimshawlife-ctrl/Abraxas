"""
Proposal Generator for Active Learning Loops.

Deterministic generation of bounded proposals from failure analyses.
Exactly ONE proposal per failure.
"""

import json
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from abraxas.learning.schema import (
    ExpectedDelta,
    FailureAnalysis,
    Proposal,
    ProposalType,
    ValidationPlan,
)
from abraxas.core.provenance import hash_canonical_json


class ProposalGenerator:
    """
    Deterministic proposal generator.

    Rules:
    1. If unmet_trigger: consider threshold relaxation
    2. If signal_gaps.missing_events: consider window extension
    3. If integrity_conditions.max_ssi high: consider integrity filter
    4. If temporal_gaps large: consider tau adjustment

    Select ONE proposal with highest expected improvement.
    """

    def __init__(
        self,
        proposals_dir: str | Path = "data/sandbox/proposals",
        ledger_path: str | Path = "out/learning_ledgers/proposals.jsonl",
    ):
        """
        Initialize proposal generator.

        Args:
            proposals_dir: Directory for proposal artifacts
            ledger_path: Proposal ledger path
        """
        self.proposals_dir = Path(proposals_dir)
        self.ledger_path = Path(ledger_path)

        self.proposals_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def generate(
        self, failure: FailureAnalysis, strategy: str = "bounded"
    ) -> Proposal:
        """
        Generate exactly ONE proposal from failure analysis.

        Args:
            failure: Failure analysis artifact
            strategy: Proposal strategy (currently only 'bounded')

        Returns:
            Proposal artifact
        """
        # Generate proposal ID
        proposal_id = self._generate_proposal_id(failure)

        # Select proposal type based on failure analysis
        proposal_type, description, affected_components = self._select_proposal_type(
            failure
        )

        # Estimate expected delta
        expected_delta = self._estimate_expected_delta(failure, proposal_type)

        # Create validation plan
        validation_plan = self._create_validation_plan(failure)

        # Create rent manifest draft if needed
        rent_manifest_draft = None
        if proposal_type in [ProposalType.NEW_METRIC, ProposalType.NEW_OPERATOR]:
            rent_manifest_draft = self._create_rent_manifest_draft(
                proposal_id, proposal_type, failure
            )

        return Proposal(
            proposal_id=proposal_id,
            source_failure_id=failure.failure_id,
            proposal_type=proposal_type,
            change_description=description,
            affected_components=affected_components,
            expected_delta=expected_delta,
            rent_manifest_draft=rent_manifest_draft,
            validation_plan=validation_plan,
        )

    def _generate_proposal_id(self, failure: FailureAnalysis) -> str:
        """Generate unique proposal ID."""
        # Extract case number and timestamp
        case_id = failure.case_id
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        # Extract hypothesis hint
        hypothesis_hint = failure.hypothesis.replace("_", "-")[:30]

        return f"proposal_{case_id}_{hypothesis_hint}_{timestamp}"

    def _select_proposal_type(
        self, failure: FailureAnalysis
    ) -> tuple[ProposalType, str, List[str]]:
        """
        Select proposal type based on failure analysis.

        Returns:
            Tuple of (proposal_type, description, affected_components)
        """
        hypothesis = failure.hypothesis

        # Strategy 1: Threshold adjustment for unmet triggers
        if hypothesis in ["term_prediction_too_aggressive", "trigger_conditions_unmet"]:
            if len(failure.unmet_triggers) > 0:
                trigger = failure.unmet_triggers[0]

                if trigger.kind == "term_seen":
                    expected_count = trigger.expected.get("min_count", 1)
                    actual_count = trigger.actual.get("count", 0)

                    if actual_count == 0:
                        return (
                            ProposalType.THRESHOLD_ADJUSTMENT,
                            f"Relax term_seen trigger - predicted term '{trigger.expected.get('term')}' not observed. "
                            f"Consider adding term variants or extending evaluation window.",
                            [f"backtest_case:{failure.case_id}"],
                        )
                    else:
                        return (
                            ProposalType.THRESHOLD_ADJUSTMENT,
                            f"Relax term_seen min_count from {expected_count} to {actual_count} "
                            f"for term '{trigger.expected.get('term')}'. Analysis shows near-miss.",
                            [f"backtest_case:{failure.case_id}"],
                        )

                elif trigger.kind == "mw_shift":
                    return (
                        ProposalType.THRESHOLD_ADJUSTMENT,
                        f"Relax MW shift threshold - expected {trigger.expected.get('min_shifts')} shifts, "
                        f"observed {trigger.actual.get('shift_count')}.",
                        [f"backtest_case:{failure.case_id}"],
                    )

                elif trigger.kind == "index_threshold":
                    expected_gte = trigger.expected.get("gte")
                    actual_max = trigger.actual.get("max_value", 0)
                    return (
                        ProposalType.THRESHOLD_ADJUSTMENT,
                        f"Relax index threshold for {trigger.expected.get('index')} from {expected_gte} "
                        f"to {actual_max * 0.9:.2f} (90% of observed max).",
                        [f"backtest_case:{failure.case_id}"],
                    )

        # Strategy 2: Window extension for signal gaps
        if hypothesis == "insufficient_signal_count":
            return (
                ProposalType.THRESHOLD_ADJUSTMENT,
                f"Extend evaluation window or relax min_signal_count. "
                f"Missing {failure.signal_gaps.missing_events} events.",
                [f"backtest_case:{failure.case_id}"],
            )

        # Strategy 3: Integrity filter adjustment
        if hypothesis == "integrity_risk_exceeded":
            return (
                ProposalType.THRESHOLD_ADJUSTMENT,
                f"Adjust integrity filtering - max SSI {failure.integrity_conditions.max_ssi:.2f} exceeded threshold. "
                f"Consider raising max_integrity_risk or adding SSI-aware filtering.",
                [f"backtest_case:{failure.case_id}"],
            )

        # Strategy 4: MW dynamics metric (new metric)
        if hypothesis == "mw_dynamics_underestimated":
            return (
                ProposalType.NEW_METRIC,
                f"Create new MW dynamics metric to better capture semantic shifts. "
                f"Current threshold may be too rigid.",
                [f"metrics:mw_dynamics"],
            )

        # Fallback: Generic threshold adjustment
        return (
            ProposalType.THRESHOLD_ADJUSTMENT,
            f"Generic threshold adjustment based on hypothesis: {hypothesis}",
            [f"backtest_case:{failure.case_id}"],
        )

    def _estimate_expected_delta(
        self, failure: FailureAnalysis, proposal_type: ProposalType
    ) -> ExpectedDelta:
        """
        Estimate expected improvement delta.

        Conservative estimates only.
        """
        # Conservative estimate: Fix this one case, might risk one regression
        improved_cases = [failure.case_id]

        # Risk assessment: Cases with similar triggers might regress
        regression_risk = []  # Conservative: assume no regressions for threshold adjustments

        # Estimate pass rate delta
        # Conservative: assume fixing 1 case improves pass rate by 1/total_cases
        # For now, assume modest 0.10 (10%) improvement
        backtest_pass_rate_delta = 0.10

        return ExpectedDelta(
            improved_cases=improved_cases,
            regression_risk=regression_risk,
            backtest_pass_rate_delta=backtest_pass_rate_delta,
        )

    def _create_validation_plan(self, failure: FailureAnalysis) -> ValidationPlan:
        """Create validation plan for sandbox."""
        # Test the failed case plus any related cases
        sandbox_cases = [failure.case_id]

        # Protected cases: cases that must not regress
        # For now, empty (could load from case metadata)
        protected_cases = []

        # Default: 3 stabilization runs
        stabilization_runs = 3

        return ValidationPlan(
            sandbox_cases=sandbox_cases,
            protected_cases=protected_cases,
            stabilization_runs=stabilization_runs,
        )

    def _create_rent_manifest_draft(
        self, proposal_id: str, proposal_type: ProposalType, failure: FailureAnalysis
    ) -> Dict[str, Any]:
        """Create draft rent manifest for new metrics/operators."""
        if proposal_type == ProposalType.NEW_METRIC:
            return {
                "id": f"{proposal_id}_metric",
                "kind": "metric",
                "version": "0.1.0",
                "description": f"Metric proposed from failure {failure.failure_id}",
                "rent_claim": {
                    "complexity": {"loc": 50, "cognitive": 3},
                    "thresholds": {
                        "backtest_pass_rate_min": 0.7,
                        "evidence_coverage_min": 0.6,
                    },
                },
                "proof": {
                    "backtest_cases": [failure.case_id],
                    "emergence_evidence": f"out/reports/{failure.failure_id}.json",
                },
            }
        elif proposal_type == ProposalType.NEW_OPERATOR:
            return {
                "id": f"{proposal_id}_operator",
                "kind": "operator",
                "version": "0.1.0",
                "description": f"Operator proposed from failure {failure.failure_id}",
                "rent_claim": {
                    "complexity": {"loc": 100, "cognitive": 5},
                    "thresholds": {
                        "backtest_pass_rate_min": 0.7,
                        "evidence_coverage_min": 0.6,
                    },
                },
                "proof": {
                    "backtest_cases": [failure.case_id],
                    "emergence_evidence": f"out/reports/{failure.failure_id}.json",
                },
            }
        else:
            return {}

    def write_proposal(self, proposal: Proposal) -> Path:
        """
        Write proposal to disk as YAML.

        Args:
            proposal: Proposal artifact

        Returns:
            Path to proposal file
        """
        proposal_dir = self.proposals_dir / proposal.proposal_id
        proposal_dir.mkdir(parents=True, exist_ok=True)

        proposal_path = proposal_dir / "proposal.yaml"

        # Convert to dict and write YAML
        proposal_dict = proposal.model_dump(exclude_none=True)

        with open(proposal_path, "w") as f:
            yaml.dump(proposal_dict, f, sort_keys=True, default_flow_style=False)

        return proposal_path

    def append_to_ledger(self, proposal: Proposal) -> str:
        """
        Append proposal to ledger.

        Args:
            proposal: Proposal artifact

        Returns:
            SHA256 hash of ledger entry
        """
        # Get last hash
        prev_hash = self._get_last_hash()

        # Create ledger entry
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "proposal_generated",
            "proposal_id": proposal.proposal_id,
            "source_failure_id": proposal.source_failure_id,
            "proposal_type": proposal.proposal_type.value,
            "expected_pass_rate_delta": proposal.expected_delta.backtest_pass_rate_delta,
            "prev_hash": prev_hash,
        }

        # Hash entry
        step_hash = hash_canonical_json(entry)
        entry["step_hash"] = step_hash

        # Append to ledger
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")

        return step_hash

    def _get_last_hash(self) -> str:
        """Get hash of last ledger entry."""
        if not self.ledger_path.exists():
            return "genesis"

        with open(self.ledger_path, "r") as f:
            lines = f.readlines()
            if not lines:
                return "genesis"

            last_entry = json.loads(lines[-1])
            return last_entry.get("step_hash", "genesis")


def generate_proposal(
    failure: FailureAnalysis,
    proposals_dir: str | Path = "data/sandbox/proposals",
    ledger_path: str | Path = "out/learning_ledgers/proposals.jsonl",
) -> Proposal:
    """
    Generate proposal from failure analysis and write artifacts.

    Convenience function.

    Args:
        failure: Failure analysis
        proposals_dir: Proposals directory
        ledger_path: Proposal ledger path

    Returns:
        Proposal artifact
    """
    generator = ProposalGenerator(proposals_dir=proposals_dir, ledger_path=ledger_path)
    proposal = generator.generate(failure)
    generator.write_proposal(proposal)
    generator.append_to_ledger(proposal)
    return proposal
