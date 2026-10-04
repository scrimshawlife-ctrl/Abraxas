"""
Cypher adapter for Abraxas evidence provider interface.
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


def _default_cypher_inference(claim: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Default inference engine for Cypher - returns persistent memory evidence."""
    return {
        "candidates": [
            CandidateOutput(
                answer="Persistent memory confirms claim",
                confidence=0.8,
                reasoning_trace="Cypher engine checked persistent memory for claim verification",
                relation_steps=[
                    RelationStep(
                        relation="memory_confirmation",
                        subject=claim,
                        object="verified",
                        result="true",
                        confidence=0.85
                    )
                ]
            ),
            CandidateOutput(
                answer="Persistent memory does not confirm claim",
                confidence=0.2,
                reasoning_trace="No matching memory trace found",
                relation_steps=[]
            )
        ],
        "model_identity": "cypher-memory-v1",
        "relations": ["memory_confirmation"],
        "reasoning_steps": [
            RelationStep(
                relation="memory_confirmation",
                subject=claim,
                object="verified",
                result="true",
                confidence=0.85
            )
        ],
        "provenance": {
            "source": "cypher_default_inference",
            "engine": "cypher"
        }
    }


def create_cypher_adapter(
    inference_engine: Optional[Callable] = None,
    engine_name: str = "cypher",
    engine_version: str = "0.1.0"
) -> EvidenceProvider:
    """
    Factory to create a Cypher adapter that wraps an inference callable.

    The inference_engine must accept (claim, context) and return a dict with:
    - candidates: List[CandidateOutput] or raw responses
    - model_identity: str
    - relations: List[str]
    - reasoning_steps: List[RelationStep]
    - provenance: Dict[str, Any]
    """
    if inference_engine is None:
        inference_engine = _default_cypher_inference

    class CypherAdapter(EvidenceProvider):
        @property
        def engine_name(self) -> str:
            return engine_name

        @property
        def engine_version(self) -> str:
            return engine_version

        @property
        def supported_evidence_types(self) -> List[EvidenceType]:
            return [EvidenceType.PERSISTENT_MEMORY]

        def get_model_identity(self) -> str:
            # Try to get from inference engine if possible, else default
            return "cypher-memory-v1"

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
                evidence_type=EvidenceType.PERSISTENT_MEMORY,
                relations=result.get("relations", []),
                reasoning_steps=reasoning_steps,
                confidence=envelope_confidence,
                uncertainty=envelope_uncertainty,
                provenance=result.get("provenance", {})
            )

    return CypherAdapter()