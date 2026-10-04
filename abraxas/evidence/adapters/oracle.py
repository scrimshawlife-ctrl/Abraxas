"""
Oracle adapter for Abraxas evidence provider interface.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Callable

from abraxas.evidence.contract import (
    EvidenceEnvelope,
    EvidenceType,
    CandidateOutput,
    RelationStep,
)
from abraxas.evidence.provider import EvidenceProvider


def _default_oracle_inference(claim: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Default inference engine for Oracle - returns a fixed narrative synthesis."""
    return {
        "candidates": [
            CandidateOutput(
                answer="Narrative synthesis indicates coherence",
                confidence=0.85,
                reasoning_trace="Oracle engine processed claim through narrative synthesis framework",
                relation_steps=[
                    RelationStep(
                        relation="narrative_coherence",
                        subject=claim,
                        object="coherent",
                        result="high",
                        confidence=0.8
                    )
                ]
            ),
            CandidateOutput(
                answer="Narrative synthesis indicates incoherence",
                confidence=0.15,
                reasoning_trace="Alternative narrative path",
                relation_steps=[]
            )
        ],
        "model_identity": "oracle-model-v1",
        "relations": ["narrative_coherence"],
        "reasoning_steps": [
            RelationStep(
                relation="narrative_coherence",
                subject=claim,
                object="coherent",
                result="high",
                confidence=0.8
            )
        ],
        "provenance": {
            "source": "oracle_default_inference",
            "engine": "oracle"
        }
    }


def create_oracle_adapter(
    inference_engine: Optional[Callable] = None,
    engine_name: str = "oracle",
    engine_version: str = "0.1.0"
) -> EvidenceProvider:
    """
    Factory to create an Oracle adapter that wraps an inference callable.

    The inference_engine must accept (claim, context) and return a dict with:
    - candidates: List[CandidateOutput] or raw responses
    - model_identity: str
    - relations: List[str]
    - reasoning_steps: List[RelationStep]
    - provenance: Dict[str, Any]
    """
    if inference_engine is None:
        inference_engine = _default_oracle_inference

    class OracleAdapter(EvidenceProvider):
        @property
        def engine_name(self) -> str:
            return engine_name

        @property
        def engine_version(self) -> str:
            return engine_version

        @property
        def supported_evidence_types(self) -> List[EvidenceType]:
            return [EvidenceType.NARRATIVE_SYNTHESIS]

        def get_model_identity(self) -> str:
            # Try to get from inference engine if possible, else default
            return "oracle-model-v1"

        def produce_evidence(
            self,
            request_id: str,
            claim: str,
            context: Dict[str, Any],
            budget: Optional[Dict[str, Any]] = None
        ) -> EvidenceEnvelope:
            # Call the inference engine
            result = inference_engine(claim, context)

            # Expect result to be a dict with the following keys:
            #   candidates, model_identity, relations, reasoning_steps, provenance
            candidates = result.get("candidates", [])

            # If candidates are not already CandidateOutput objects, convert them.
            # We assume the inference engine returns CandidateOutput objects.
            # If not, we would need to convert here.

            # Compute envelope confidence from candidates (max of top candidate)
            envelope_confidence = max((c.confidence for c in candidates), default=0.0)
            envelope_uncertainty = 1.0 - envelope_confidence if envelope_confidence > 0 else 1.0

            # Convert raw relation_steps dicts to RelationStep objects
            raw_steps = result.get("reasoning_steps", [])
            reasoning_steps = []
            for step in raw_steps:
                if isinstance(step, dict):
                    reasoning_steps.append(RelationStep(
                        relation=step.get("relation", ""),
                        subject=step.get("subject", ""),
                        object=step.get("object", ""),
                        result=step.get("result"),
                        confidence=step.get("confidence", 1.0),
                        metadata=step.get("metadata", {})
                    ))
                else:
                    reasoning_steps.append(step)

            # Convert to canonical envelope
            return EvidenceEnvelope(
                engine=self.engine_name,
                engine_version=self.engine_version,
                model_identity=result.get("model_identity", self.get_model_identity()),
                request_id=request_id,
                claim=claim,
                candidate_outputs=candidates,
                evidence_type=EvidenceType.NARRATIVE_SYNTHESIS,
                relations=result.get("relations", []),
                reasoning_steps=reasoning_steps,
                confidence=envelope_confidence,
                uncertainty=envelope_uncertainty,
                provenance=result.get("provenance", {})
            )

    return OracleAdapter()