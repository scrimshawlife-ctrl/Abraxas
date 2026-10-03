"""
Verifier Interface — all verifiers must implement this.

Verifiers examine evidence for internal consistency, structural validity,
and domain-specific correctness. They do not independently solve the
original reasoning problem.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType


class Verifier(ABC):
    """Base interface for all evidence verifiers."""
    
    @property
    @abstractmethod
    def evidence_type(self) -> EvidenceType:
        """The evidence type this verifier handles."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name."""
        pass
    
    @abstractmethod
    def verify(self, envelope: EvidenceEnvelope) -> Dict[str, Any]:
        """
        Verify the evidence envelope.
        
        Returns:
            Dict with at minimum:
            - "passed": bool
            - "escalate": bool
            - "details": Dict[str, Any]
        """
        pass


class RelationalVerifier(Verifier):
    """Verifies structural consistency of relational reasoning evidence."""
    
    @property
    def evidence_type(self) -> EvidenceType:
        return EvidenceType.RELATIONAL_REASONING
    
    @property
    def name(self) -> str:
        return "RelationalConsistencyVerifier"
    
    def verify(self, envelope: EvidenceEnvelope) -> Dict[str, Any]:
        """Check relational consistency of evidence."""
        details = {
            "entity_consistency": 0.0,
            "relation_continuity": 0.0,
            "composition_order": 0.0,
            "counterfactual_consistency": 0.0,
            "contradictions": [],
            "unsupported_transitions": [],
        }
        
        # Check entity consistency across reasoning steps
        entity_consistency = self._check_entity_consistency(envelope)
        details["entity_consistency"] = entity_consistency
        
        # Check relation continuity (chains are properly linked)
        relation_continuity = self._check_relation_continuity(envelope)
        details["relation_continuity"] = relation_continuity
        
        # Check composition order
        composition_order = self._check_composition_order(envelope)
        details["composition_order"] = composition_order
        
        # Check counterfactual consistency
        counterfactual_consistency = self._check_counterfactual_consistency(envelope)
        details["counterfactual_consistency"] = counterfactual_consistency
        
        # Overall pass threshold
        passed = (
            entity_consistency >= 0.7 and
            relation_continuity >= 0.7 and
            composition_order >= 0.7 and
            counterfactual_consistency >= 0.7 and
            len(details["contradictions"]) == 0
        )
        
        # Escalate if severe issues
        escalate = (
            entity_consistency < 0.4 or
            relation_continuity < 0.4 or
            len(details["contradictions"]) > 0
        )
        
        return {
            "passed": passed,
            "escalate": escalate,
            "details": details
        }
    
    def _check_entity_consistency(self, envelope: EvidenceEnvelope) -> float:
        """Check if entities are used consistently throughout reasoning."""
        all_entities = set()
        step_entities = []
        
        for step in envelope.reasoning_steps:
            entities = {step.subject, step.object}
            if step.result:
                entities.add(step.result)
            step_entities.append(entities)
            all_entities.update(entities)
        
        # Check overlap between consecutive steps
        if len(step_entities) < 2:
            return 1.0
        
        overlaps = 0
        for i in range(len(step_entities) - 1):
            if step_entities[i] & step_entities[i + 1]:
                overlaps += 1
        
        return overlaps / (len(step_entities) - 1)
    
    def _check_relation_continuity(self, envelope: EvidenceEnvelope) -> float:
        """Check if relation steps form valid chains."""
        if len(envelope.reasoning_steps) < 2:
            return 1.0
        
        valid_transitions = 0
        for i in range(len(envelope.reasoning_steps) - 1):
            curr = envelope.reasoning_steps[i]
            next_step = envelope.reasoning_steps[i + 1]
            
            # Check if output of current connects to input of next
            if curr.result and (next_step.subject == curr.result or 
                                next_step.object == curr.result):
                valid_transitions += 1
        
        return valid_transitions / (len(envelope.reasoning_steps) - 1)
    
    def _check_composition_order(self, envelope: EvidenceEnvelope) -> float:
        """Verify the composition follows expected relational order."""
        # For transitive relations, we expect chain structure
        # This is a simplified check
        if len(envelope.reasoning_steps) < 2:
            return 1.0
        
        # Check if all steps use the same relation (for transitive chains)
        relations = {step.relation for step in envelope.reasoning_steps}
        if len(relations) == 1:
            return 1.0  # Single relation chain is expected for transitive reasoning
        
        return 0.8  # Mixed relations are acceptable but less consistent
    
    def _check_counterfactual_consistency(self, envelope: EvidenceEnvelope) -> float:
        """Check if counterfactual reasoning is internally consistent."""
        # Check if claim has counterfactual marker
        claim = envelope.claim.lower()
        is_counterfactual = "not" in claim or "false" in claim or "counterfactual" in claim
        
        if not is_counterfactual:
            return 1.0
        
        # For counterfactuals, check if reasoning acknowledges negation
        has_negation = any(
            "not" in c.reasoning_trace.lower() or 
            "false" in c.reasoning_trace.lower() or
            "¬" in c.reasoning_trace
            for c in envelope.candidate_outputs
        )
        
        return 0.8 if has_negation else 0.5