"""
Evidence Provider Interface — all reasoning engines must implement this.

This defines the contract for producing canonical EvidenceEnvelope objects.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from abraxas.evidence.contract import (
    EvidenceEnvelope,
    EvidenceType,
    CandidateOutput,
    RelationStep,
    create_athanor_envelope
)


class EvidenceProvider(ABC):
    """Base interface for all evidence providers."""
    
    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Unique identifier for this provider (e.g. 'athanor', 'hyperlex')."""
        pass
    
    @property
    @abstractmethod
    def engine_version(self) -> str:
        """Version of this provider implementation."""
        pass
    
    @property
    @abstractmethod
    def supported_evidence_types(self) -> List[EvidenceType]:
        """Evidence types this provider can produce."""
        pass
    
    @abstractmethod
    def produce_evidence(
        self,
        request_id: str,
        claim: str,
        context: Dict[str, Any],
        budget: Optional[Dict[str, Any]] = None
    ) -> EvidenceEnvelope:
        """
        Produce canonical evidence for the given claim.
        
        Args:
            request_id: Unique request identifier for provenance
            claim: The claim/question to produce evidence for
            context: Additional context (premises, domain, depth, etc.)
            budget: Optional compute budget constraints
            
        Returns:
            Canonical EvidenceEnvelope
        """
        pass
    
    @abstractmethod
    def get_model_identity(self) -> str:
        """Return the model/checkpoint identity for provenance."""
        pass


class MockEvidenceProvider(EvidenceProvider):
    """Mock provider for cross-provider testing."""
    
    @property
    def engine_name(self) -> str:
        return "mock"
    
    @property
    def engine_version(self) -> str:
        return "test-1.0"
    
    @property
    def supported_evidence_types(self) -> List[EvidenceType]:
        return [EvidenceType.FACTUAL, EvidenceType.LEXICAL_SEMANTIC]
    
    def get_model_identity(self) -> str:
        return "mock-model-v1"
    
    def produce_evidence(
        self,
        request_id: str,
        claim: str,
        context: Dict[str, Any],
        budget: Optional[Dict[str, Any]] = None
    ) -> EvidenceEnvelope:
        """Produce deterministic mock evidence."""
        from abraxas.evidence.contract import CandidateOutput
        
        candidates = [
            CandidateOutput(
                answer="Yes",
                confidence=0.85,
                reasoning_trace=f"Mock reasoning for: {claim}",
                relation_steps=[]
            ),
            CandidateOutput(
                answer="No",
                confidence=0.15,
                reasoning_trace=f"Alternative mock reasoning",
                relation_steps=[]
            )
        ]
        
        return EvidenceEnvelope(
            engine=self.engine_name,
            engine_version=self.engine_version,
            model_identity=self.get_model_identity(),
            request_id=request_id,
            claim=claim,
            candidate_outputs=candidates,
            evidence_type=EvidenceType.FACTUAL,
            confidence=0.85,
            uncertainty=0.15,
            provenance={"source": "mock", "test": True}
        )


def create_athanor_adapter(
    inference_engine: Callable,
    engine_name: str = "athanor",
    engine_version: str = "1.0"
) -> EvidenceProvider:
    """
    Factory to create an Athanor adapter that wraps an inference callable.
    
    The inference_engine must accept (claim, context) and return a dict with:
    - candidates: List[CandidateOutput] or raw responses
    - model_identity: str
    - relations: List[str]
    - reasoning_steps: List[RelationStep]
    - provenance: Dict[str, Any]
    """
    
    class AthanorAdapter(EvidenceProvider):
        @property
        def engine_name(self) -> str:
            return engine_name
        
        @property
        def engine_version(self) -> str:
            return engine_version
        
        @property
        def supported_evidence_types(self) -> List[EvidenceType]:
            return [EvidenceType.RELATIONAL_REASONING, EvidenceType.COUNTERFACTUAL]
        
        def get_model_identity(self) -> str:
            return "lora-out-transfer-001-t1/checkpoint-48"
        
        def produce_evidence(
            self,
            request_id: str,
            claim: str,
            context: Dict[str, Any],
            budget: Optional[Dict[str, Any]] = None
        ) -> EvidenceEnvelope:
            # Call the inference engine
            result = inference_engine(claim, context)
            
            # Convert to canonical envelope
            return create_athanor_envelope(
                claim=claim,
                candidates=result.get("candidates", []),
                model_identity=result.get("model_identity", self.get_model_identity()),
                request_id=request_id,
                relations=result.get("relations", []),
                reasoning_steps=result.get("reasoning_steps", []),
                confidence=result.get("confidence", 0.0),
                uncertainty=result.get("uncertainty", 0.0),
                provenance=result.get("provenance", {})
            )
    
    return AthanorAdapter()


# Registry for providers
class ProviderRegistry:
    """Registry for evidence providers."""
    
    def __init__(self):
        self._providers: Dict[str, EvidenceProvider] = {}
    
    def register(self, provider: EvidenceProvider) -> None:
        self._providers[provider.engine_name] = provider
    
    def get(self, engine_name: str) -> Optional[EvidenceProvider]:
        return self._providers.get(engine_name)
    
    def all(self) -> List[EvidenceProvider]:
        return list(self._providers.values())
    
    def names(self) -> List[str]:
        return list(self._providers.keys())


# Global registry instance
provider_registry = ProviderRegistry()