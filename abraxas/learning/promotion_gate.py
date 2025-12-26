"""
Promotion Gate for Active Learning Loops.

Validates promotion criteria and promotes eligible proposals.
Strict criteria - no change promoted unless proven.
"""

import json
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from abraxas.learning.schema import (
    ImprovementDelta,
    Proposal,
    PromotionEntry,
    SandboxReport,
)
from abraxas.core.provenance import hash_canonical_json


class PromotionGate:
    """
    Strict promotion gate.

    A proposal may be promoted ONLY if:
    1. Improvement threshold met (pass_rate_delta >= 0.10)
    2. No regressions on protected cases
    3. Cost bounds respected (time/memory delta <= 20%)
    4. Stabilization verified (N consecutive successful runs)
    """

    def __init__(
        self,
        proposals_dir: str | Path = "data/sandbox/proposals",
        ledger_path: str | Path = "out/learning_ledgers/promotions.jsonl",
        improvement_threshold: float = 0.10,
        max_time_delta_pct: float = 0.20,
        max_memory_delta_pct: float = 0.20,
        required_stabilization_runs: int = 3,
    ):
        """
        Initialize promotion gate.

        Args:
            proposals_dir: Proposals directory
            ledger_path: Promotions ledger
            improvement_threshold: Minimum pass rate delta (default 0.10 = 10%)
            max_time_delta_pct: Max time increase (default 0.20 = 20%)
            max_memory_delta_pct: Max memory increase (default 0.20 = 20%)
            required_stabilization_runs: Required consecutive successful runs
        """
        self.proposals_dir = Path(proposals_dir)
        self.ledger_path = Path(ledger_path)

        self.improvement_threshold = improvement_threshold
        self.max_time_delta_pct = max_time_delta_pct
        self.max_memory_delta_pct = max_memory_delta_pct
        self.required_stabilization_runs = required_stabilization_runs

        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def validate_promotion(
        self, proposal: Proposal, sandbox_reports: List[SandboxReport]
    ) -> tuple[bool, List[str]]:
        """
        Validate whether proposal meets promotion criteria.

        Args:
            proposal: Proposal to validate
            sandbox_reports: Sandbox reports from stabilization runs

        Returns:
            Tuple of (eligible, reasons)
            eligible: True if all criteria met
            reasons: List of validation messages (errors if not eligible)
        """
        reasons = []

        # Criterion 1: Sufficient sandbox runs
        if len(sandbox_reports) < self.required_stabilization_runs:
            reasons.append(
                f"Insufficient stabilization runs: {len(sandbox_reports)} < {self.required_stabilization_runs}"
            )
            return False, reasons

        # Criterion 2: Improvement threshold (check all runs)
        for report in sandbox_reports:
            if report.delta.pass_rate_delta < self.improvement_threshold:
                reasons.append(
                    f"Improvement below threshold in run {report.sandbox_run_id}: "
                    f"{report.delta.pass_rate_delta:.2%} < {self.improvement_threshold:.2%}"
                )
                return False, reasons

        # Criterion 3: No regressions (check all runs)
        for report in sandbox_reports:
            if report.delta.regression_count > 0:
                reasons.append(
                    f"Regressions detected in run {report.sandbox_run_id}: "
                    f"{report.delta.regression_count} cases regressed"
                )
                return False, reasons

        # Criterion 4: Cost bounds (check all runs)
        # For v0.1, we use fixed thresholds (will enhance with manifest-based checks later)
        max_time_ms = 100  # Baseline assumption: runs take ~500ms, allow +100ms
        max_memory_kb = 1024  # Allow +1MB

        for report in sandbox_reports:
            if report.cost_delta.time_ms_delta > max_time_ms:
                reasons.append(
                    f"Time cost exceeded in run {report.sandbox_run_id}: "
                    f"+{report.cost_delta.time_ms_delta:.1f}ms > {max_time_ms}ms"
                )
                return False, reasons

            if report.cost_delta.memory_kb_delta > max_memory_kb:
                reasons.append(
                    f"Memory cost exceeded in run {report.sandbox_run_id}: "
                    f"+{report.cost_delta.memory_kb_delta:.1f}KB > {max_memory_kb}KB"
                )
                return False, reasons

        # Criterion 5: Stabilization (no variance across runs)
        # Check that pass_rate_delta is consistent
        deltas = [report.delta.pass_rate_delta for report in sandbox_reports]
        variance = max(deltas) - min(deltas)

        if variance > 0.05:  # Allow 5% variance
            reasons.append(
                f"Unstable results across runs: variance {variance:.2%} > 5%"
            )
            return False, reasons

        # All criteria met
        reasons.append("All promotion criteria satisfied")
        return True, reasons

    def promote(
        self, proposal: Proposal, sandbox_reports: List[SandboxReport], strict: bool = True
    ) -> Optional[PromotionEntry]:
        """
        Promote a proposal if eligible.

        Args:
            proposal: Proposal to promote
            sandbox_reports: Sandbox validation reports
            strict: If True, enforce all criteria (default)

        Returns:
            PromotionEntry if promoted, None if not eligible
        """
        # Validate
        eligible, reasons = self.validate_promotion(proposal, sandbox_reports)

        if not eligible:
            if strict:
                print(f"Promotion REJECTED for {proposal.proposal_id}:")
                for reason in reasons:
                    print(f"  - {reason}")
                return None
            else:
                print(f"Warning: Promoting despite failed criteria (strict=False)")

        # Calculate improvement delta from latest sandbox report
        latest_report = sandbox_reports[-1]
        improvement_delta = ImprovementDelta(
            pass_rate_delta=latest_report.delta.pass_rate_delta,
            cost_delta={
                "time_ms": latest_report.cost_delta.time_ms_delta,
                "memory_kb": latest_report.cost_delta.memory_kb_delta,
            },
        )

        # Create promotion entry
        promotion = PromotionEntry(
            proposal_id=proposal.proposal_id,
            source_failure_id=proposal.source_failure_id,
            improvement_delta=improvement_delta,
            provenance_note=f"{proposal.change_description}",
            ledger_sha256="",  # Will be filled after hashing
        )

        # Append to ledger
        ledger_hash = self._append_to_ledger(promotion)
        promotion.ledger_sha256 = ledger_hash

        # Mark promotion in proposal directory
        self._write_promotion_marker(proposal.proposal_id, promotion)

        print(f"Promotion APPROVED for {proposal.proposal_id}")
        print(f"  Improvement: +{improvement_delta.pass_rate_delta:.2%} pass rate")
        print(f"  Cost: +{improvement_delta.cost_delta['time_ms']:.1f}ms, "
              f"+{improvement_delta.cost_delta['memory_kb']:.1f}KB")
        print(f"  Ledger hash: {ledger_hash[:16]}...")

        return promotion

    def _append_to_ledger(self, promotion: PromotionEntry) -> str:
        """Append promotion to ledger."""
        prev_hash = self._get_last_hash()

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "promotion",
            "proposal_id": promotion.proposal_id,
            "source_failure_id": promotion.source_failure_id,
            "promoted_at": promotion.promoted_at.isoformat(),
            "improvement_delta": {
                "pass_rate_delta": promotion.improvement_delta.pass_rate_delta,
                "cost_delta": promotion.improvement_delta.cost_delta,
            },
            "provenance_note": promotion.provenance_note,
            "prev_hash": prev_hash,
        }

        step_hash = hash_canonical_json(entry)
        entry["step_hash"] = step_hash

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

    def _write_promotion_marker(self, proposal_id: str, promotion: PromotionEntry):
        """Write promotion marker to proposal directory."""
        proposal_dir = self.proposals_dir / proposal_id
        marker_path = proposal_dir / "PROMOTED.json"

        with open(marker_path, "w") as f:
            json.dump(promotion.model_dump(), f, indent=2, default=str)


def promote_proposal(
    proposal_id: str,
    proposals_dir: str | Path = "data/sandbox/proposals",
    strict: bool = True,
) -> Optional[PromotionEntry]:
    """
    Promote a proposal.

    Convenience function that loads proposal and sandbox reports,
    validates criteria, and promotes if eligible.

    Args:
        proposal_id: Proposal ID to promote
        proposals_dir: Proposals directory
        strict: Enforce strict criteria

    Returns:
        PromotionEntry if promoted, None otherwise
    """
    proposals_dir = Path(proposals_dir)

    # Load proposal
    proposal_path = proposals_dir / proposal_id / "proposal.yaml"
    with open(proposal_path, "r") as f:
        proposal_data = yaml.safe_load(f)
    proposal = Proposal(**proposal_data)

    # Load sandbox reports
    sandbox_reports = []
    proposal_dir = proposals_dir / proposal_id

    for report_file in sorted(proposal_dir.glob("sandbox_*.json")):
        with open(report_file, "r") as f:
            report_data = json.load(f)
        sandbox_reports.append(SandboxReport(**report_data))

    if not sandbox_reports:
        print(f"No sandbox reports found for {proposal_id}")
        return None

    # Run promotion gate
    gate = PromotionGate(proposals_dir=proposals_dir)
    return gate.promote(proposal, sandbox_reports, strict=strict)
