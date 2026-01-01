"""OAS Canonizer: makes final adoption decisions for operator candidates."""

from __future__ import annotations

from datetime import datetime, timezone

from abraxas.core.provenance import ProvenanceBundle, ProvenanceRef, hash_canonical_json
from abraxas.core.registry import OperatorRegistry
from abraxas.oasis.ledger import OASLedger
from abraxas.oasis.models import (
    CanonDecision,
    OperatorCandidate,
    OperatorStatus,
    StabilizationState,
    ValidationReport,
)


class OASCanonizer:
    """
    Makes canonization decisions for operator candidates.

    Applies adoption gates: validation, stabilization, complexity, non-poisoning.
    """

    def __init__(
        self,
        registry: OperatorRegistry | None = None,
        ledger_path: str | None = None,
        max_time_regression_pct: float = 10.0,
    ):
        """
        Initialize canonizer.

        Args:
            registry: Operator registry to update
            ledger_path: Path to OAS ledger
            max_time_regression_pct: Max allowed time regression percentage
        """
        self.registry = registry or OperatorRegistry()
        self.ledger = OASLedger(ledger_path)
        self.max_time_regression_pct = max_time_regression_pct

    def canonize(
        self,
        candidate: OperatorCandidate,
        report: ValidationReport,
        stabilization: StabilizationState,
    ) -> CanonDecision:
        """
        Make canonization decision for a candidate.

        Applies all adoption gates and returns decision.
        """
        # Gate 1: Validation must pass
        if not report.passed:
            return self._reject(
                candidate,
                "Validation failed",
                report.metrics_after,
            )

        # Gate 2: Stabilization must be stable
        if not stabilization.stable:
            return self._reject(
                candidate,
                f"Not stable: {stabilization.cycles_completed}/{stabilization.cycles_required} cycles",
                report.metrics_after,
            )

        # Gate 3: Complexity gate (simplified - check if metrics justify complexity)
        if not self._complexity_gate(report):
            return self._reject(
                candidate,
                "Complexity not justified by metrics improvement",
                report.metrics_after,
            )

        # Gate 4: Non-poisoning gate
        if not self._non_poisoning_gate(candidate):
            return self._reject(
                candidate,
                "Failed non-poisoning check",
                report.metrics_after,
            )

        # All gates passed - adopt!
        return self._adopt(candidate, report, stabilization)

    def _adopt(
        self,
        candidate: OperatorCandidate,
        report: ValidationReport,
        stabilization: StabilizationState,
    ) -> CanonDecision:
        """Adopt candidate as canonical."""
        # Update candidate status
        candidate.status = OperatorStatus.CANONICAL

        # Register in registry
        self.registry.register(
            operator_id=candidate.operator_id,
            version=candidate.version,
            status=OperatorStatus.CANONICAL.value,
            data=candidate.model_dump(),
        )

        # Write to ledger
        ledger_entry = {
            "type": "adoption",
            "candidate": candidate.model_dump(),
            "report": report.model_dump(),
            "stabilization": stabilization.model_dump(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        ledger_ref = self.ledger.append(ledger_entry)

        # Create decision
        provenance = ProvenanceBundle(
            inputs=[
                ProvenanceRef(
                    scheme="candidate",
                    path=candidate.operator_id,
                    sha256=hash_canonical_json(candidate.model_dump()),
                )
            ],
            transforms=["canonization", "adoption"],
            metrics=report.deltas,
            created_by="oasis_canonizer",
        )

        decision = CanonDecision(
            adopted=True,
            reason="All adoption gates passed",
            operator_id=candidate.operator_id,
            version=candidate.version,
            ledger_ref=ledger_ref,
            metrics_delta=report.deltas,
            provenance=provenance,
        )

        return decision

    def _reject(
        self, candidate: OperatorCandidate, reason: str, metrics: dict[str, float]
    ) -> CanonDecision:
        """Reject candidate."""
        # Write rejection to ledger
        ledger_entry = {
            "type": "rejection",
            "candidate_id": candidate.operator_id,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        ledger_ref = self.ledger.append(ledger_entry)

        provenance = ProvenanceBundle(
            inputs=[
                ProvenanceRef(
                    scheme="candidate",
                    path=candidate.operator_id,
                    sha256=hash_canonical_json(candidate.model_dump()),
                )
            ],
            transforms=["canonization", "rejection"],
            metrics=metrics,
            created_by="oasis_canonizer",
        )

        decision = CanonDecision(
            adopted=False,
            reason=reason,
            operator_id=candidate.operator_id,
            version=candidate.version,
            ledger_ref=ledger_ref,
            metrics_delta={},
            provenance=provenance,
        )

        return decision

    def _complexity_gate(self, report: ValidationReport) -> bool:
        """
        Check if added complexity is justified.

        Complexity must reduce applied metrics (entropy, false classification).
        """
        # Check that key metrics improved
        entropy_delta = report.deltas.get("entropy", 0.0)
        false_rate_delta = report.deltas.get("false_classification_rate", 0.0)

        # Both should be negative (improvement)
        return entropy_delta < 0 or false_rate_delta < 0

    def _non_poisoning_gate(self, candidate: OperatorCandidate) -> bool:
        """
        Check for poisoning patterns (slurs, harassment).

        This is a simplified check with a hook interface for production use.
        """
        # Simple heuristic: reject if triggers contain obvious problematic patterns
        problematic_patterns = [
            "slur",
            "harass",
            "hate",
            "attack",
            # In production, this would be a comprehensive classifier
        ]

        for trigger in candidate.triggers:
            trigger_lower = trigger.lower()
            for pattern in problematic_patterns:
                if pattern in trigger_lower:
                    return False

        # No slur signals present (stub)
        return True
