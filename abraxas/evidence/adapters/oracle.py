"""
Oracle adapter for Abraxas evidence provider interface.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Callable

from abraxas.evidence.contract import (
    EvidenceEnvelope,
    EvidenceType,
    CandidateOutput,
    RelationStep,
)
from abraxas.evidence.provider import EvidenceProvider


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

    When no inference_engine is supplied the **model-agnostic adapter** is used, so this engine is usable
    without a bespoke custom model: configure an OpenAI-compatible endpoint via `ABX_INFERENCE_BASE_URL` /
    `ABX_INFERENCE_MODEL`, or run the deterministic offline path. Engine-specific custom inference is a future
    capability ("custom inference coming soon" in the UI).

    This replaced `_default_oracle_inference`, which manufactured a `coherence_score` from word counts
    (`+= 0.1  # Sweet spot for coherence`) and published it as the envelope's confidence -- a word-count
    heuristic presenting itself as a narrative-synthesis model's assessment. Nothing about a claim's wording
    is evidence of a model's reading.
    """
    from abraxas.evidence.adapters.model_agnostic import (
        create_model_agnostic_inference,
        identity_of,
        to_candidate_outputs,
    )

    if inference_engine is None:
        inference_engine = create_model_agnostic_inference()

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
            # Report the identity of the path that actually ran, rather than naming a model.
            return identity_of(inference_engine)

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
            #
            # The model-agnostic adapter yields plain readings; the evidence contract requires
            # CandidateOutput. One shared converter does that, so the shape cannot drift per engine.
            candidates = to_candidate_outputs(result.get("candidates", []))

            # `source` names the engine; the adapter's own keys (inference path, input digest) come with the
            # result and are merged on top, so provenance always states both who read the claim and HOW.
            provenance = {"source": self.engine_name, **result.get("provenance", {})}

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
                provenance=provenance
            )

    return OracleAdapter()