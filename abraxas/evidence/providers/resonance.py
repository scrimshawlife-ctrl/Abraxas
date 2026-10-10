"""Resonance Evidence Provider — composes abraxas.phase detectors.

Real implementation using PhaseAlignmentDetector and CouplingDetector
from abraxas.phase for cross-domain resonance analysis.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from abraxas.evidence.contract import CandidateOutput, EvidenceEnvelope, EvidenceType
from abraxas.evidence.provider import EvidenceProvider
from abraxas.phase import (
    PhaseAlignmentDetector,
    CouplingDetector,
    create_phase_detector,
    create_coupling_detector,
)


class ResonanceEvidenceProvider(EvidenceProvider):
    """Resonance provider composing phase alignment and coupling detectors.

    Accepts domain_states, drift_signals, and resonance_signals in context
    and produces RESONANCE_ANALYSIS evidence.
    """

    def __init__(
        self,
        phase_detector: Optional[PhaseAlignmentDetector] = None,
        coupling_detector: Optional[CouplingDetector] = None,
    ) -> None:
        """Initialize with phase and coupling detectors.

        Args:
            phase_detector: PhaseAlignmentDetector (default created if None).
            coupling_detector: CouplingDetector (default created if None).
        """
        self._phase_detector = phase_detector or create_phase_detector()
        self._coupling_detector = coupling_detector or create_coupling_detector()

    @property
    def engine_name(self) -> str:
        return "resonance"

    @property
    def engine_version(self) -> str:
        return "resonance.phase.v0"

    @property
    def supported_evidence_types(self) -> List[EvidenceType]:
        return [EvidenceType.RESONANCE_ANALYSIS]

    def get_model_identity(self) -> str:
        return "resonance.phase.v0"

    def produce_evidence(
        self,
        request_id: str,
        claim: str,
        context: Dict[str, Any],
        budget: Optional[Dict[str, Any]] = None,
    ) -> EvidenceEnvelope:
        """Produce resonance evidence from phase alignment and coupling detection.

        Context keys used:
            domain_states: Dict[str, Dict[str, str]] — domain → {token → phase}
            drift_signals: Dict[str, float] — domain → drift_strength
            resonance_signals: Dict[str, float] — domain → resonance_strength
        """
        domain_states = context.get("domain_states", {})
        drift_signals = context.get("drift_signals", {})
        resonance_signals = context.get("resonance_signals", {})

        # Phase alignment detection
        alignments = self._phase_detector.detect_alignments(
            domain_states=domain_states,
            run_id=request_id,
        )
        num_alignments = len(alignments)

        # Build aligned domains list from alignments for coupling context
        aligned_domains: List[str] = []
        for a in alignments:
            aligned_domains.extend(list(a.domains))

        # Coupling detection (only when both signal dicts are populated)
        couplings = self._coupling_detector.detect_couplings(
            drift_signals=drift_signals,
            resonance_signals=resonance_signals,
            aligned_domains=aligned_domains if aligned_domains else None,
            run_id=request_id,
        )
        num_couplings = len(couplings)

        # Compute confidence from detected signals
        if num_alignments > 0 and num_couplings > 0:
            confidence = 0.85
            summary = (
                f"Detected {num_alignments} phase alignment(s) and "
                f"{num_couplings} coupling(s) across domains"
            )
        elif num_alignments > 0:
            confidence = 0.7
            summary = f"Detected {num_alignments} phase alignment(s); no drift-resonance coupling"
        elif num_couplings > 0:
            confidence = 0.6
            summary = f"Detected {num_couplings} coupling(s); no phase alignments"
        else:
            confidence = 0.3
            summary = "No phase alignments or couplings detected"

        # Collect coupling cascade risks for the trace
        cascade_risks = [c.cascade_risk for c in couplings]
        cascade_summary = f"cascade risks: {', '.join(cascade_risks)}" if cascade_risks else "no cascade risks"

        return EvidenceEnvelope(
            engine="resonance",
            engine_version=self.engine_version,
            model_identity=self.get_model_identity(),
            request_id=request_id,
            claim=claim,
            candidate_outputs=[
                CandidateOutput(
                    answer=summary,
                    confidence=confidence,
                    reasoning_trace=(
                        f"Phase alignments: {num_alignments}, "
                        f"couplings: {num_couplings}, "
                        f"{cascade_summary}"
                    ),
                    relation_steps=[],
                )
            ],
            evidence_type=EvidenceType.RESONANCE_ANALYSIS,
            reasoning_steps=[],
            relations=[],
            confidence=confidence,
            uncertainty=round(1.0 - confidence, 4),
            decision_margin=0.0,
            entropy=1.0,
            provenance={
                "source": "resonance.phase.v0",
                "method": "phase_alignment_and_coupling",
                "phase_alignments_detected": num_alignments,
                "couplings_detected": num_couplings,
                "aligned_phases": list(set(a.aligned_phase for a in alignments)),
                "cascade_risks": cascade_risks if cascade_risks else ["none"],
                "domains_analyzed": len(domain_states),
                "authority": "advisory",
                "semantic_truth": False,
                "influence_policy": "NONE",
                "valid_for_forecast": False,
                "lane": "shadow",
            },
        )


def create_resonance_adapter() -> EvidenceProvider:
    """Factory: create a ResonanceEvidenceProvider with default detectors."""
    return ResonanceEvidenceProvider()