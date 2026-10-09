"""Hyperlex Evidence Provider for LEXICAL_SEMANTIC (planned minimal stub)."""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from abraxas.evidence.contract import CandidateOutput, EvidenceEnvelope, EvidenceType
from abraxas.evidence.provider import EvidenceProvider


class HyperlexEvidenceProvider(EvidenceProvider):
    """Minimal stub for hyperlex (LEXICAL_SEMANTIC)."""

    @property
    def engine_name(self) -> str:
        return "hyperlex"

    @property
    def engine_version(self) -> str:
        return "hyperlex.lexical.v0"

    @property
    def supported_evidence_types(self) -> List[EvidenceType]:
        return [EvidenceType.LEXICAL_SEMANTIC]

    def get_model_identity(self) -> str:
        return "hyperlex.planned-stub"

    def produce_evidence(
        self,
        request_id: str,
        claim: str,
        context: Dict[str, Any],
        budget: Optional[Dict[str, Any]] = None
    ) -> EvidenceEnvelope:
        """Stub implementation."""
        return EvidenceEnvelope(
            engine="hyperlex",
            engine_version=self.engine_version,
            model_identity=self.get_model_identity(),
            request_id=request_id,
            claim=claim,
            candidate_outputs=[
                CandidateOutput(
                    answer="planned stub for hyperlex lexical semantic",
                    confidence=0.8,
                    reasoning_trace="This is a minimal stub.",
                    relation_steps=[]
                )
            ],
            evidence_type=EvidenceType.LEXICAL_SEMANTIC,
            reasoning_steps=[],
            relations=[],
            confidence=0.8,
            uncertainty=0.2,
            decision_margin=0.0,
            entropy=1.0,
            provenance={"source": "hyperlex.planned-stub", "status": "planned"},
        )

def create_hyperlex_adapter() -> EvidenceProvider:
    """Factory for manifest."""
    return HyperlexEvidenceProvider()