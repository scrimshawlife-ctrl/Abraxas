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
        """Stub that raises as per manifest."""
        raise NotImplementedError("Aether deliberately refuses per manifest")

def create_aether_adapter() -> EvidenceProvider:
    return AetherEvidenceProvider()