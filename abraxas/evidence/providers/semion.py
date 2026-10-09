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
    instrument_enabled,
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
        # Real: obs = semion.classify(claim, context) from sibling Semion repo
        # Placeholder observation shape from ARCHITECTURE / semion_q1_fixtures
        try:
            obs = {
                "authority": {
                    "kind": "advisory",
                    "source": "semion",
                    "semantic_truth": False,
                    "may_authorize": False,
                    "may_mutate_governing_state": False,
                    "role": "OBSERVATION",
                },
                "observation_id": request_id,
                "sign_class": "qualisign-rheme-icon",
                "sign_class_valid": True,
                "sign_class_errors": [],
                "interpretant_coherence": 1.0,
                "representamen_object_alignment": 1.0,
                "relation_steps": [
                    {
                        "relation": "resembles",
                        "subject": "sign_a",
                        "object": "sign_b",
                        "result": "similar",
                        "confidence": 0.9,
                        "metadata": {},
                    }
                ],
                "peircean_analysis": {
                    "existence": "qualisign",
                    "thirdness": "rheme",
                    "relation": "icon",
                    "valid_combination": True,
                    "coherence_score": 0.95,
                },
                "provenance": {
                    "instrument_version": "SEMION_SIGN_RELATION_V1",
                    "contract_version": "semion.sign.v1",
                },
            }
            adapted = adapt_observation(obs)

            peircean = adapted.get("peircean_analysis") or {}
            confidence = float(peircean.get("coherence_score") or 0.0)

            steps = [
                RelationStep(
                    relation=str(step.get("relation")),
                    subject=str(step.get("subject")),
                    object=str(step.get("object")),
                    result=str(step.get("result")),
                    confidence=float(step.get("confidence") or 0.0),
                    metadata=dict(step.get("metadata") or {}),
                )
                for step in adapted.get("relation_steps") or []
            ]

            return EvidenceEnvelope(
                engine="semion",
                engine_version=self.engine_version,
                model_identity=self.get_model_identity(),
                request_id=request_id,
                claim=claim,
                candidate_outputs=[
                    CandidateOutput(
                        answer=str(adapted.get("sign_class", "sign")),
                        confidence=confidence,
                        reasoning_trace="semion instrument: " + str(adapted.get("sign_class", "")),
                        relation_steps=steps,
                    )
                ],
                evidence_type=EvidenceType.SIGN_RELATION,
                reasoning_steps=[],
                relations=[str(step.get("relation")) for step in adapted.get("relation_steps") or []],
                confidence=confidence,
                uncertainty=1.0 - confidence,
                decision_margin=0.0,
                entropy=0.0,
                provenance={
                    "source": "semion_instrument",
                    "contract": CONTRACT_VERSION,
                    "lane": adapted.get("lane"),
                    "influence_policy": adapted.get("influence_policy"),
                    "sign_class": adapted.get("sign_class"),
                    "sign_class_valid": adapted.get("sign_class_valid"),
                    "status": adapted.get("status"),
                },
            )
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
                provenance={"error": str(e)},
            )


def create_semion_adapter() -> EvidenceProvider:
    """Factory for manifest."""
    return SemionEvidenceProvider()