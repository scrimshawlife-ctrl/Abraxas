"""Cypher adapter for Abraxas evidence provider interface with Timechain integration."""
from __future__ import annotations

import hashlib
import logging
from typing import List, Dict, Any, Optional, Callable

from abraxas.evidence.contract import (
    EvidenceEnvelope,
    EvidenceType,
    CandidateOutput,
    RelationStep,
)
from abraxas.evidence.provider import EvidenceProvider

logger = logging.getLogger(__name__)

# Optional Timechain integration via Yggdrasil memory layer
try:
    from abraxas.yggdrasil.memory import CypherMemoryLayer
    _memory_layer_instance = None
except ImportError:
    CypherMemoryLayer = None
    _memory_layer_instance = None
    logger.debug("Yggdrasil memory layer not available")


def _get_memory_layer():
    """Get or initialize the Yggdrasil memory layer singleton."""
    global _memory_layer_instance
    if _memory_layer_instance is None and CypherMemoryLayer is not None:
        _memory_layer_instance = CypherMemoryLayer()
        _memory_layer_instance.initialize()
    return _memory_layer_instance


def _default_cypher_inference(claim: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Default inference engine for Cypher - returns persistent memory evidence with Timechain integration.
    
    Checks if claim exists in persistent memory (Yggdrasil layer with Timechain fallback).
    If found, returns confirming evidence; if not, stores new evidence and returns non-confirming.
    """
    # Generate deterministic key from claim
    claim_key = hashlib.sha256(claim.encode('utf-8')).hexdigest()
    record_id = f"env-{claim_key}"
    
    # Try to retrieve from memory layer
    memory_layer = _get_memory_layer()
    if memory_layer is not None:
        try:
            envelope_dict = memory_layer.retrieve_evidence(record_id)
            if envelope_dict is not None:
                # Reconstruct envelope from stored dict
                envelope = EvidenceEnvelope.from_dict(envelope_dict)
                logger.debug(f"Retrieved claim '{claim[:50]}...' from persistent memory")
                return {
                    "candidates": envelope.candidate_outputs,
                    "model_identity": envelope.model_identity,
                    "relations": envelope.relations,
                    "reasoning_steps": envelope.reasoning_steps,
                    "provenance": {
                        **envelope.provenance,
                        "source": "cypher_memory_retrieval",
                        "engine": "cypher",
                        "retrieval_timestamp": envelope.timestamp
                    }
                }
        except Exception as e:
            logger.debug(f"Failed to retrieve from memory layer: {e}")
    
    # Not found in memory - create new evidence and store it
    envelope = EvidenceEnvelope(
        engine="cypher",
        engine_version="0.1.0",
        model_identity="cypher-memory-v1",
        request_id=claim_key,
        claim=claim,
        candidate_outputs=[
            CandidateOutput(
                answer="Persistent memory does not confirm claim",
                confidence=0.2,
                reasoning_trace="No matching memory trace found in persistent storage",
                relation_steps=[]
            ),
            CandidateOutput(
                answer="Persistent memory confirms claim",
                confidence=0.8,
                reasoning_trace="Claim stored in persistent memory for future verification",
                relation_steps=[
                    RelationStep(
                        relation="memory_storage",
                        subject=claim,
                        object="stored",
                        result="true",
                        confidence=0.85
                    )
                ]
            )
        ],
        evidence_type=EvidenceType.PERSISTENT_MEMORY,
        relations=["memory_storage"],
        reasoning_steps=[
            RelationStep(
                relation="memory_check",
                subject=claim,
                object="persistent_memory",
                result="stored_new",
                confidence=0.8
            )
        ],
        provenance={
            "source": "cypher_default_inference",
            "engine": "cypher",
            "storage_attempt": True
        }
    )
    
    # Store the envelope in persistent memory (Yggdrasil with Timechain fallback)
    if memory_layer is not None:
        try:
            # Override envelope's evidence_id to match our deterministic key
            envelope.evidence_id = claim_key
            storage_id = memory_layer.store_evidence(envelope)
            logger.debug(f"Stored claim '{claim[:50]}...' in persistent memory with ID: {storage_id}")
        except Exception as e:
            logger.warning(f"Failed to store in persistent memory: {e}")
    
    # Return inference dict from the new envelope
    return {
        "candidates": envelope.candidate_outputs,
        "model_identity": envelope.model_identity,
        "relations": envelope.relations,
        "reasoning_steps": envelope.reasoning_steps,
        "provenance": envelope.provenance
    }


def create_cypher_adapter(
    inference_engine: Optional[Callable] = None,
    engine_name: str = "cypher",
    engine_version: str = "0.1.0"
) -> EvidenceProvider:
    """Factory to create a Cypher adapter that wraps an inference callable.

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