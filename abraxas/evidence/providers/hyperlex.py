"""Hyperlex Evidence Provider (LEXICAL_SEMANTIC) — consumes sibling instrument per SIBLING_REPOS."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
from abraxas.evidence.contract import CandidateOutput, EvidenceEnvelope, EvidenceType
from abraxas.evidence.provider import EvidenceProvider
from abraxas.evidence.hyperlex_instrument import (
    instrument_enabled, adapt_observation, observe_text, HyperlexAuthorityError
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
        # Deepened integration: call real sibling instrument when enabled.
        # observe_text handles import + real hyperlex.instrument.observe when package present.
        try:
            result = observe_text(claim)
            if result.get("ok") and "observation" in result:
                obs = result["observation"]
            else:
                # Graceful: instrument disabled or sibling unavailable — return advisory zero-evidence
                obs = {
                    "observation_id": request_id,
                    "input_hash": claim[:16],
                    "evidence": {"present": False, "score": 0.0, "abstain": True, "reason": result.get("error", "unavailable")},
                    "candidates": [],
                    "authority": {"kind": "advisory"},
                }
            adapted = adapt_observation(obs)
            return EvidenceEnvelope(
                engine="hyperlex", engine_version=self.engine_version,
                model_identity=self.get_model_identity(), request_id=request_id, claim=claim,
                candidate_outputs=[CandidateOutput(answer=str(adapted.get("candidates", [{}])[0].get("concept_id", "lex") if adapted.get("candidates") else "hyperlex-no-candidate"),
                                                   confidence=adapted.get("evidence", {}).get("score", 0.0),
                                                   reasoning_trace="hyperlex instrument", relation_steps=[])],
                evidence_type=EvidenceType.LEXICAL_SEMANTIC,
                confidence=adapted.get("evidence", {}).get("score", 0.0),
                uncertainty=1.0 - adapted.get("evidence", {}).get("score", 0.0),
                provenance={"source": "hyperlex_instrument", "adapted": True, "real_call": result.get("ok", False), **adapted.get("provenance", {})}
            )
        except HyperlexAuthorityError as e:
            return EvidenceEnvelope(confidence=0.0, uncertainty=1.0, provenance={"error": str(e)})

def create_hyperlex_adapter() -> EvidenceProvider:
    return HyperlexEvidenceProvider()