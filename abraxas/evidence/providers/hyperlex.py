"""Hyperlex Evidence Provider (LEXICAL_SEMANTIC) — consumes sibling instrument per SIBLING_REPOS."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
from abraxas.evidence.contract import CandidateOutput, EvidenceEnvelope, EvidenceType
from abraxas.evidence.provider import EvidenceProvider
from abraxas.evidence.hyperlex_instrument import (
    instrument_enabled, adapt_observation, HyperlexAuthorityError
)

class HyperlexEvidenceProvider(EvidenceProvider):
    @property
    def engine_name(self) -> str: return "hyperlex"
    @property
    def engine_version(self) -> str: return "hyperlex.lexical.v1"
    @property
    def supported_evidence_types(self) -> List[EvidenceType]:
        return [EvidenceType.LEXICAL_SEMANTIC]

    def get_model_identity(self) -> str:
        return "hyperlex-instrument-v1" if instrument_enabled() else "hyperlex.planned-disabled"

    def produce_evidence(self, request_id: str, claim: str, context: Dict[str, Any],
                         budget: Optional[Dict[str, Any]] = None) -> EvidenceEnvelope:
        if not instrument_enabled():
            return EvidenceEnvelope(
                engine="hyperlex", engine_version=self.engine_version,
                model_identity=self.get_model_identity(), request_id=request_id, claim=claim,
                candidate_outputs=[], evidence_type=EvidenceType.LEXICAL_SEMANTIC,
                confidence=0.0, uncertainty=1.0,
                provenance={"status": "instrument_disabled", "source": "hyperlex.planned"}
            )
        # TODO in later slice: call real sibling via instrument (for now adapt stub observation)
        # Real call would be: obs = sibling_hyperlex.observe(claim, context); ...
        try:
            # Placeholder observation shape from sibling DESIGN; replace with real sibling call
            obs = {"observation_id": request_id, "input_hash": claim[:16],
                   "evidence": {"present": True, "score": 0.75, "abstain": False},
                   "candidates": [{"concept_id": "lex-1", "score": 0.75, "axis": "lexical", "advisory": True}],
                   "authority": {"kind": "advisory"}}
            adapted = adapt_observation(obs)
            return EvidenceEnvelope(
                engine="hyperlex", engine_version=self.engine_version,
                model_identity=self.get_model_identity(), request_id=request_id, claim=claim,
                candidate_outputs=[CandidateOutput(answer=str(adapted.get("candidates", [{}])[0].get("concept_id", "lex")),
                                                   confidence=adapted.get("evidence", {}).get("score", 0.7),
                                                   reasoning_trace="hyperlex instrument", relation_steps=[])],
                evidence_type=EvidenceType.LEXICAL_SEMANTIC,
                confidence=adapted.get("evidence", {}).get("score", 0.7),
                uncertainty=1.0 - adapted.get("evidence", {}).get("score", 0.7),
                provenance={"source": "hyperlex_instrument", "adapted": True, **adapted.get("provenance", {})}
            )
        except HyperlexAuthorityError as e:
            return EvidenceEnvelope(confidence=0.0, uncertainty=1.0, provenance={"error": str(e)})

def create_hyperlex_adapter() -> EvidenceProvider:
    return HyperlexEvidenceProvider()