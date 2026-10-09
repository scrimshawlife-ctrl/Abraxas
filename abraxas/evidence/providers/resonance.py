"""Resonance Evidence Provider (phase detectors) — minimal planned stub."""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from abraxas.evidence.contract import CandidateOutput, EvidenceEnvelope, EvidenceType
from abraxas.evidence.provider import EvidenceProvider

class ResonanceEvidenceProvider(EvidenceProvider):
    """Minimal stub for resonance (phase detectors)."""

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
        return "resonance.planned-stub"

    def produce_evidence(
        self,
        request_id: str,
        claim: str,
        context: Dict[str, Any],
        budget: Optional[Dict[str, Any]] = None
    ) -> EvidenceEnvelope:
        """Stub implementation for planned engine."""
        return EvidenceEnvelope(
            engine="resonance",
            engine_version=self.engine_version,
            model_identity=self.get_model_identity(),
            request_id=request_id,
            claim=claim,
            candidate_outputs=[
                CandidateOutput(
                    answer="planned stub for resonance phase analysis",
                    confidence=0.0,
                    reasoning_trace="This is a minimal stub; uses abraxas/phase/* layer.",
                    relation_steps=[]
                )
            ],
            evidence_type=EvidenceType.RESONANCE_ANALYSIS,
            reasoning_steps=[],
            relations=[],
            confidence=0.0,
            uncertainty=1.0,
            decision_margin=0.0,
            entropy=1.0,
            provenance={"source": "resonance.planned-stub", "status": "planned"},
        )

def create_resonance_adapter() -> EvidenceProvider:
    return ResonanceEvidenceProvider()