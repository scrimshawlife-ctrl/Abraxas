from datetime import timezone
"""
Abraxas Evidence Arbiter — engine-independent arbitration of evidence.

The arbiter evaluates EvidenceEnvelope objects and determines:
ACCEPT, VERIFY, RECOMPUTE, ESCALATE, ABSTAIN
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from abraxas.evidence.contract import EvidenceEnvelope, Decision


class ArbitrationPolicy(ABC):
    """Configurable policy for evidence arbitration."""
    
    @abstractmethod
    def evaluate(self, envelope: EvidenceEnvelope) -> Decision:
        """Evaluate a single evidence envelope."""
        pass
    
    @abstractmethod
    def evaluate_batch(self, envelopes: List[EvidenceEnvelope]) -> Decision:
        """Evaluate multiple evidence envelopes for the same claim."""
        pass


class DefaultArbitrationPolicy(ArbitrationPolicy):
    """Default arbitration policy with configurable thresholds."""
    
    def __init__(
        self,
        accept_confidence: float = 0.85,
        verify_confidence: float = 0.60,
        recompute_confidence: float = 0.40,
        max_uncertainty: float = 0.30,
        min_decision_margin: float = 0.15,
        max_entropy: float = 0.70,
        contradiction_penalty: float = 0.5
    ):
        self.accept_confidence = accept_confidence
        self.verify_confidence = verify_confidence
        self.recompute_confidence = recompute_confidence
        self.max_uncertainty = max_uncertainty
        self.min_decision_margin = min_decision_margin
        self.max_entropy = max_entropy
        self.contradiction_penalty = contradiction_penalty
    
    def evaluate(self, envelope: EvidenceEnvelope) -> Decision:
        # High confidence, low uncertainty, good margin -> ACCEPT
        if (envelope.confidence >= self.accept_confidence and
            envelope.uncertainty <= self.max_uncertainty and
            envelope.decision_margin >= self.min_decision_margin and
            envelope.entropy <= self.max_entropy):
            return Decision.ACCEPT
        
        # Contradictory evidence -> ESCALATE
        if self._has_contradiction(envelope):
            return Decision.ESCALATE
        
        # Medium confidence -> VERIFY
        if envelope.confidence >= self.verify_confidence:
            return Decision.VERIFY
        
        # Low confidence but potentially recoverable -> RECOMPUTE
        if envelope.confidence >= self.recompute_confidence:
            return Decision.RECOMPUTE
        
        # Too uncertain -> ABSTAIN
        return Decision.ABSTAIN
    
    def evaluate_batch(self, envelopes: List[EvidenceEnvelope]) -> Decision:
        if not envelopes:
            return Decision.ABSTAIN
        
        # Check for cross-engine agreement
        agreements = self._check_cross_engine_agreement(envelopes)
        
        # If strong agreement, potentially ACCEPT even with lower individual confidence
        if agreements >= 0.8:
            avg_confidence = sum(e.confidence for e in envelopes) / len(envelopes)
            if avg_confidence >= self.verify_confidence:
                return Decision.ACCEPT
        
        # Otherwise use highest confidence envelope
        best = max(envelopes, key=lambda e: e.confidence)
        return self.evaluate(best)
    
    def _has_contradiction(self, envelope: EvidenceEnvelope) -> bool:
        """Check for internal contradictions in evidence."""
        answers = [c.answer for c in envelope.candidate_outputs]
        # If both Yes and No present with significant confidence
        yes_conf = max((c.confidence for c in envelope.candidate_outputs if c.answer == "Yes"), default=0)
        no_conf = max((c.confidence for c in envelope.candidate_outputs if c.answer == "No"), default=0)
        return yes_conf > 0.3 and no_conf > 0.3
    
    def _check_cross_engine_agreement(self, envelopes: List[EvidenceEnvelope]) -> float:
        """Check agreement across different engines."""
        if len(envelopes) < 2:
            return 1.0
        
        # Simple agreement: fraction of engines with same top answer
        top_answers = [e.candidate_outputs[0].answer for e in envelopes if e.candidate_outputs]
        if not top_answers:
            return 0.0
        most_common = max(set(top_answers), key=top_answers.count)
        return top_answers.count(most_common) / len(top_answers)


class EvidenceArbiter:
    """Main arbiter for evaluating evidence and making decisions."""
    
    def __init__(self, policy: ArbitrationPolicy = None):
        self.policy = policy or DefaultArbitrationPolicy()
        self._verifiers: Dict[str, Any] = {}  # evidence_type -> verifier
    
    def register_verifier(self, evidence_type: str, verifier: Any) -> None:
        """Register a verifier for a specific evidence type."""
        self._verifiers[evidence_type] = verifier
    
    def arbitrate(self, envelope: EvidenceEnvelope) -> Decision:
        """Arbitrate a single evidence envelope."""
        # First pass: policy evaluation
        decision = self.policy.evaluate(envelope)
        
        # If VERIFY, run appropriate verifier
        if decision == Decision.VERIFY:
            verifier = self._verifiers.get(envelope.evidence_type.value)
            if verifier:
                verification_result = verifier.verify(envelope)
                if verification_result.get("passed", False):
                    return Decision.ACCEPT
                elif verification_result.get("escalate", False):
                    return Decision.ESCALATE
        
        return decision
    
    def arbitrate_batch(self, envelopes: List[EvidenceEnvelope]) -> Decision:
        """Arbitrate multiple envelopes for the same claim."""
        return self.policy.evaluate_batch(envelopes)
    
    def get_verifier(self, evidence_type: str) -> Optional[Any]:
        return self._verifiers.get(evidence_type)


@dataclass
class ArbitrationResult:
    """Result of arbitration with full trace."""
    decision: Decision
    envelope: EvidenceEnvelope
    policy_trace: Dict[str, Any] = field(default_factory=dict)
    verification_trace: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())