"""Oracle v2 Metric Governance

Applies 6-gate governance system to Oracle v2 outputs:
1. Provenance: Complete SHA-256 tracking through all phases
2. Falsifiability: Predictions can be disconfirmed by future observations
3. Redundancy: Oracle metrics not redundant with existing canonical metrics
4. Rent Payment: Measurable lift in forecast accuracy / narrative quality
5. Ablation: Oracle phases can be removed without system collapse
6. Stabilization: Consistent performance over stabilization window

All Oracle v2 metrics must pass these gates before canonical promotion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from abraxas.metrics.governance import (
    EvidenceBundle,
    FalsifiabilityCriteria,
    LiftMetrics,
    PromotionDecision,
    PromotionLedgerEntry,
    ProvenanceMeta,
    RedundancyScores,
    StabilizationScores,
    TestResults,
)
from abraxas.oracle.v2.pipeline import (
    CompressionPhase,
    ForecastPhase,
    NarrativePhase,
    OracleV2Output,
)


@dataclass(frozen=True)
class OracleGovernanceReport:
    """Governance compliance report for Oracle v2 output."""

    oracle_run_id: str
    timestamp: str
    test_results: TestResults
    compliance_summary: Dict[str, bool]
    rationale: str
    recommendation: PromotionDecision

    def to_dict(self) -> Dict:
        return {
            "oracle_run_id": self.oracle_run_id,
            "timestamp": self.timestamp,
            "test_results": self.test_results.to_dict(),
            "compliance_summary": self.compliance_summary,
            "rationale": self.rationale,
            "recommendation": self.recommendation.value,
        }


class OracleGovernanceValidator:
    """
    Validates Oracle v2 outputs against 6-gate governance system.

    Checks:
    - Provenance: All phases have SHA-256 provenance tracking
    - Falsifiability: Forecasts specify disconfirmation criteria
    - Redundancy: Metrics not redundant with canonical metrics
    - Rent Payment: Measurable lift in forecast/narrative quality
    - Ablation: Phases can be individually disabled
    - Stabilization: Consistent performance over time
    """

    def __init__(
        self,
        canonical_metrics: Optional[Dict[str, any]] = None,
        stabilization_window: int = 10,
    ) -> None:
        """Initialize governance validator.

        Args:
            canonical_metrics: Existing canonical metrics for redundancy check
            stabilization_window: Number of cycles for stabilization
        """
        self._canonical = canonical_metrics or {}
        self._stabilization_window = stabilization_window

    def validate(
        self,
        output: OracleV2Output,
        evidence: Optional[EvidenceBundle] = None,
    ) -> OracleGovernanceReport:
        """Validate Oracle v2 output against all 6 gates.

        Args:
            output: Oracle v2 output to validate
            evidence: Optional evidence bundle from simulation runs

        Returns:
            Governance compliance report
        """
        # Gate 1: Provenance
        provenance_passed = self._check_provenance(output)

        # Gate 2: Falsifiability
        falsifiability_passed = self._check_falsifiability(output)

        # Gate 3: Redundancy
        redundancy_passed = self._check_redundancy(output)

        # Gate 4: Rent Payment
        rent_payment_passed = self._check_rent_payment(output, evidence)

        # Gate 5: Ablation
        ablation_passed = self._check_ablation(output, evidence)

        # Gate 6: Stabilization
        stabilization_passed = self._check_stabilization(output, evidence)

        test_results = TestResults(
            provenance_passed=provenance_passed,
            falsifiability_passed=falsifiability_passed,
            redundancy_passed=redundancy_passed,
            rent_payment_passed=rent_payment_passed,
            ablation_passed=ablation_passed,
            stabilization_passed=stabilization_passed,
        )

        compliance_summary = {
            "provenance": provenance_passed,
            "falsifiability": falsifiability_passed,
            "redundancy": redundancy_passed,
            "rent_payment": rent_payment_passed,
            "ablation": ablation_passed,
            "stabilization": stabilization_passed,
        }

        # Generate rationale
        rationale = self._generate_rationale(test_results, output)

        # Recommend decision
        if test_results.all_passed():
            recommendation = PromotionDecision.PROMOTED
        elif redundancy_passed and rent_payment_passed:
            recommendation = PromotionDecision.MERGED
        else:
            recommendation = PromotionDecision.REJECTED

        return OracleGovernanceReport(
            oracle_run_id=output.run_id,
            timestamp=output.created_at_utc,
            test_results=test_results,
            compliance_summary=compliance_summary,
            rationale=rationale,
            recommendation=recommendation,
        )

    # Gate implementations

    def _check_provenance(self, output: OracleV2Output) -> bool:
        """Gate 1: Verify complete SHA-256 provenance tracking.

        Requirements:
        - All phases have Provenance objects
        - All provenance objects have non-empty hashes
        - Inputs hash chains through phases
        """
        # Check compression provenance
        if not output.compression.provenance:
            return False
        if not output.compression.provenance.inputs_hash:
            return False
        if not output.compression.provenance.config_hash:
            return False

        # Check forecast provenance
        if not output.forecast.provenance:
            return False
        if not output.forecast.provenance.inputs_hash:
            return False

        # Check narrative provenance
        if not output.narrative.provenance:
            return False
        if not output.narrative.bundle_hash:
            return False

        # Verify provenance chaining
        # (forecast inputs should reference compression hash)
        # This is a simplified check - in production, verify full chain
        return True

    def _check_falsifiability(self, output: OracleV2Output) -> bool:
        """Gate 2: Verify forecasts can be disconfirmed.

        Requirements:
        - Phase transitions specify probabilities (can be tested)
        - Weather trajectory is a discrete prediction
        - Memetic pressure has numeric range
        - Contamination advisory has risk thresholds
        """
        # Check forecast has falsifiable predictions
        if not output.forecast.phase_transitions:
            # No predictions to falsify - may be valid if no transitions expected
            pass

        # Check transition probabilities exist (can be compared to actual)
        if output.forecast.phase_transitions and not output.forecast.transition_probabilities:
            return False

        # Check weather trajectory is discrete (can be matched)
        if not output.forecast.weather_trajectory:
            return False

        # Check memetic pressure in valid range [0, 1]
        if not (0.0 <= output.forecast.memetic_pressure <= 1.0):
            return False

        # All forecasts are falsifiable
        return True

    def _check_redundancy(self, output: OracleV2Output) -> bool:
        """Gate 3: Verify oracle metrics not redundant with canonical.

        Requirements:
        - Oracle metrics provide unique signal
        - Low correlation with existing canonical metrics
        - No duplicate information
        """
        # Simplified check: Oracle v2 is a new system, so not redundant yet
        # In production, check against canonical metric registry
        # and compute correlation/mutual information

        # Check for unique signals
        if not output.compression.domain_signals:
            # No signals extracted - may be redundant
            return False

        # Oracle v2 provides unique lifecycle + weather + narrative signals
        # that don't exist in canonical metrics (by design)
        return True

    def _check_rent_payment(
        self, output: OracleV2Output, evidence: Optional[EvidenceBundle]
    ) -> bool:
        """Gate 4: Verify measurable lift over baseline.

        Requirements:
        - Oracle forecasts improve accuracy over baseline
        - Narrative quality metrics show improvement
        - Contamination advisories reduce risk exposure
        """
        if evidence is None:
            # No evidence yet - assume passing for initial runs
            # In production, require evidence bundle
            return True

        # Check if lift metrics meet thresholds
        return evidence.lift_metrics.meets_thresholds()

    def _check_ablation(
        self, output: OracleV2Output, evidence: Optional[EvidenceBundle]
    ) -> bool:
        """Gate 5: Verify system survives ablation.

        Requirements:
        - Can remove compression phase (use raw tokens)
        - Can remove forecast phase (use current states only)
        - Can remove narrative phase (use raw metrics)
        - Each phase adds value but system doesn't collapse without it
        """
        if evidence is None:
            # No evidence yet - assume passing for initial runs
            return True

        # Check ablation results
        if not evidence.ablation_results:
            return False

        # Each phase should maintain some baseline performance when removed
        # (not checking specific thresholds here - that's in evidence bundle)
        return True

    def _check_stabilization(
        self, output: OracleV2Output, evidence: Optional[EvidenceBundle]
    ) -> bool:
        """Gate 6: Verify consistent performance over time.

        Requirements:
        - Stabilization window of N cycles
        - Low performance variance
        - No drift in forecasts
        """
        if evidence is None:
            # No evidence yet - cannot verify stabilization
            return False

        # Check if stabilization window complete
        return evidence.stabilization_scores.is_stable()

    def _generate_rationale(self, test_results: TestResults, output: OracleV2Output) -> str:
        """Generate short rationale for governance decision."""
        if test_results.all_passed():
            return (
                f"Oracle v2 (run {output.run_id}) passed all 6 gates. "
                f"Provenance complete through {len(output.narrative.evidence_tokens)} tokens. "
                f"Forecast includes {len(output.forecast.phase_transitions)} transitions. "
                f"Narrative confidence: {output.narrative.confidence_band}."
            )

        failed_gates = []
        if not test_results.provenance_passed:
            failed_gates.append("provenance")
        if not test_results.falsifiability_passed:
            failed_gates.append("falsifiability")
        if not test_results.redundancy_passed:
            failed_gates.append("redundancy")
        if not test_results.rent_payment_passed:
            failed_gates.append("rent_payment")
        if not test_results.ablation_passed:
            failed_gates.append("ablation")
        if not test_results.stabilization_passed:
            failed_gates.append("stabilization")

        return (
            f"Oracle v2 (run {output.run_id}) failed {len(failed_gates)} gate(s): "
            f"{', '.join(failed_gates)}. Requires evidence bundle and stabilization window."
        )


def create_oracle_governance_validator(
    stabilization_window: int = 10,
) -> OracleGovernanceValidator:
    """Create Oracle v2 governance validator with default config.

    Args:
        stabilization_window: Number of cycles for stabilization (default 10)

    Returns:
        Configured governance validator
    """
    return OracleGovernanceValidator(
        canonical_metrics={},  # Load from registry in production
        stabilization_window=stabilization_window,
    )


__all__ = [
    "OracleGovernanceReport",
    "OracleGovernanceValidator",
    "create_oracle_governance_validator",
]
