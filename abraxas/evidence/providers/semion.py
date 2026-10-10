"""Semion Evidence Provider (SIGN_RELATION) — consumes sibling per SIBLING_REPOS and instrument."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from abraxas.evidence.contract import CandidateOutput, EvidenceEnvelope, EvidenceType, RelationStep
from abraxas.evidence.provider import EvidenceProvider
from abraxas.evidence.semion_instrument import (
    CONTRACT_VERSION,
    ENGINE_VERSION,
    MODEL_IDENTITY,
    SemionAuthorityError,
    adapt_observation,
    classify_via_semion,
    instrument_enabled,
    to_evidence_envelope,
)


class SemionEvidenceProvider(EvidenceProvider):
    @property
    def engine_name(self) -> str:
        return "semion"

    @property
    def engine_version(self) -> str:
        return ENGINE_VERSION

    @property
    def supported_evidence_types(self) -> List[EvidenceType]:
        return [EvidenceType.SIGN_RELATION]

    def get_model_identity(self) -> str:
        return MODEL_IDENTITY if instrument_enabled() else "semion.planned-disabled"

    def produce_evidence(
        self,
        request_id: str,
        claim: str,
        context: Dict[str, Any],
        budget: Optional[Dict[str, Any]] = None,
    ) -> EvidenceEnvelope:
        if not instrument_enabled():
            return EvidenceEnvelope(
                engine="semion",
                engine_version=self.engine_version,
                model_identity=self.get_model_identity(),
                request_id=request_id,
                claim=claim,
                candidate_outputs=[],
                evidence_type=EvidenceType.SIGN_RELATION,
                confidence=0.0,
                uncertainty=1.0,
                provenance={"status": "disabled"},
            )
        # Deepened integration: delegate to instrument's live classify + envelope builder.
        # classify_via_semion imports semion.classify from sibling when ABX_SEMION_INSTRUMENT=1 and package present.
        try:
            atom = {"text": claim, "request_id": request_id, **{k: v for k, v in context.items() if isinstance(k, str)}}
            raw = classify_via_semion(atom)
            env = to_evidence_envelope(raw, request_id=request_id, claim=claim)
            return env
        except SemionAuthorityError as e:
            return EvidenceEnvelope(
                engine="semion",
                engine_version=self.engine_version,
                model_identity=self.get_model_identity(),
                request_id=request_id,
                claim=claim,
                candidate_outputs=[],
                evidence_type=EvidenceType.SIGN_RELATION,
                confidence=0.0,
                uncertainty=1.0,
                provenance={"error": str(e), "status": "authority_violation"},
            )
        except Exception as e:
            # ImportError, classify failure, etc. -> zero evidence envelope (shadow lane)
            return EvidenceEnvelope(
                engine="semion",
                engine_version=self.engine_version,
                model_identity=self.get_model_identity(),
                request_id=request_id,
                claim=claim,
                candidate_outputs=[],
                evidence_type=EvidenceType.SIGN_RELATION,
                confidence=0.0,
                uncertainty=1.0,
                provenance={"error": str(e), "status": "classify_failed"},
            )


def create_semion_adapter() -> EvidenceProvider:
    """Factory for manifest."""
    return SemionEvidenceProvider()