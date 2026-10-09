"""Aether Evidence Provider (multimodal) — minimal planned stub that refuses per design."""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from abraxas.evidence.contract import CandidateOutput, EvidenceEnvelope, EvidenceType
from abraxas.evidence.provider import EvidenceProvider

class AetherEvidenceProvider(EvidenceProvider):
    """Minimal stub for aether (multimodal) that raises per manifest design."""

    @property
    def engine_name(self) -> str:
        return "aether"

    @property
    def engine_version(self) -> str:
        return "aether.multimodal.v0"

    @property
    def supported_evidence_types(self) -> List[EvidenceType]:
        return [EvidenceType.MULTIMODAL_INTEGRATION]

    def get_model_identity(self) -> str:
        return "aether.planned-stub"

    def produce_evidence(
        self,
        request_id: str,
        claim: str,
        context: Dict[str, Any],
        budget: Optional[Dict[str, Any]] = None
    ) -> EvidenceEnvelope:
        """Minimal stub for aether (multimodal) that returns planned envelope (not raising)."""
        return EvidenceEnvelope(
            engine="aether",
            engine_version=self.engine_version,
            model_identity=self.get_model_identity(),
            request_id=request_id,
            claim=claim,
            candidate_outputs=[
                CandidateOutput(
                    answer="planned stub for aether multimodal",
                    confidence=0.8,
                    reasoning_trace="This is a minimal stub; full implementation pending.",
                    relation_steps=[]
                )
            ],
            evidence_type=EvidenceType.MULTIMODAL_INTEGRATION,
            reasoning_steps=[],
            relations=[],
            confidence=0.8,
            uncertainty=0.2,
            decision_margin=0.0,
            entropy=1.0,
            provenance={"source": "aether.planned-stub", "status": "planned"},
        )

def create_aether_adapter() -> EvidenceProvider:
    return AetherEvidenceProvider()