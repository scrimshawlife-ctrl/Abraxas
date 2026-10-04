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


def _default_oracle_inference(claim: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced inference engine for Oracle - returns context-aware narrative synthesis."""
    # Analyze claim characteristics for more sophisticated synthesis
    claim_lower = claim.lower()
    words = claim.split()
    word_count = len(words)
    
    # Determine narrative tone based on claim characteristics
    if any(word in claim_lower for word in ["why", "how", "explain", "reason"]):
        tone = "explanatory"
        coherence_indicators = ["logical", "systematic", "well-reasoned"]
        incoherence_indicators = ["illogical", "inconsistent", "poorly reasoned"]
    elif any(word in claim_lower for word in ["what", "who", "when", "where"]):
        tone = "descriptive"
        coherence_indicators = ["accurate", "precise", "detailed"]
        incoherence_indicators = ["vague", "ambiguous", "inaccurate"]
    elif any(word in claim_lower for word in ["should", "must", "ought", "need"]):
        tone = "prescriptive"
        coherence_indicators = ["justified", "reasonable", "well-founded"]
        incoherence_indicators = ["unjustified", "arbitrary", "unfounded"]
    else:
        tone = "analytical"
        coherence_indicators = ["coherent", "consistent", "well-structured"]
        incoherence_indicators = ["incoherent", "inconsistent", "poorly structured"]
    
    # Calculate coherence score based on claim features
    coherence_score = 0.5  # Base score
    
    # Adjust based on claim length (very short or very long claims might be less coherent)
    if 5 <= word_count <= 25:
        coherence_score += 0.1  # Sweet spot for coherence
    elif word_count > 25:
        coherence_score -= 0.05  # Very long claims might be overly complex
    # Very short claims (<5) keep base score
    
    # Adjust based on specificity indicators
    if any(indicator in claim_lower for indicator in ["specifically", "particularly", "exactly"]):
        coherence_score += 0.15
    if any(indicator in claim_lower for indicator in ["maybe", "perhaps", "possibly", "might"]):
        coherence_score -= 0.1
    
    # Boost for well-formed questions
    if claim.strip().endswith("?"):
        coherence_score += 0.1
    
    # Ensure score stays in reasonable bounds
    coherence_score = max(0.1, min(0.9, coherence_score))
    
    # Determine if we lean toward coherence or incoherence
    is_coherent = coherence_score > 0.5
    
    # Generate appropriate answer and confidence
    if is_coherent:
        answer = f"Narrative synthesis indicates {tone} coherence"
        confidence = coherence_score
        reasoning_trace = f"Oracle engine performed {tone} narrative synthesis on claim with {word_count} words"
        coherence_result = "high"
    else:
        answer = f"Narrative synthesis indicates {tone} incoherence"
        confidence = 1.0 - coherence_score
        reasoning_trace = f"Oracle engine identified potential {tone} issues in claim with {word_count} words"
        coherence_result = "low"
    
    # Enhanced relation steps with more detailed analysis
    relation_steps = [
        RelationStep(
            relation=f"narrative_{tone}_analysis",
            subject=claim,
            object="analysis_complete",
            result=coherence_result,
            confidence=confidence,
            metadata={
                "tone": tone,
                "word_count": word_count,
                "coherence_score": coherence_score,
                "analysis_type": "narrative_synthesis"
            }
        ),
        RelationStep(
            relation="contextual_assessment",
            subject="claim_analysis",
            object="context_relevance",
            result="evaluated",
            confidence=0.8,
            metadata={
                "context_provided": bool(context),
                "context_keys": list(context.keys()) if context else []
            }
        )
    ]
    
    # Enhanced reasoning steps
    reasoning_steps = [
        RelationStep(
            relation=f"narrative_{tone}_analysis",
            subject=claim,
            object="coherence_evaluation",
            result=coherence_result,
            confidence=confidence
        )
    ]
    
    # Add contextual reasoning if context is provided
    if context:
        reasoning_steps.append(
            RelationStep(
                relation="context_integration",
                subject="external_factors",
                object="claim_interpretation",
                result="considered",
                confidence=0.75,
                metadata={"context_elements": len(context)}
            )
        )
    
    return {
        "candidates": [
            CandidateOutput(
                answer=answer,
                confidence=confidence,
                reasoning_trace=reasoning_trace,
                relation_steps=relation_steps
            ),
            CandidateOutput(
                answer=f"Alternative narrative interpretation ({'coherent' if not is_coherent else 'incoherent'})",
                confidence=1.0 - confidence,
                reasoning_trace="Alternative narrative path considering different interpretive frameworks",
                relation_steps=[]
            )
        ],
        "model_identity": "oracle-model-v2-enhanced",
        "relations": [f"narrative_{tone}_analysis", "contextual_assessment"],
        "reasoning_steps": reasoning_steps,
        "provenance": {
            "source": "oracle_enhanced_inference",
            "engine": "oracle",
            "enhancement_version": "2.0",
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
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