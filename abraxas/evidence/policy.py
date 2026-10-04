"""
Arbitration Policy & Decision Record — Abraxas decision layer.

This module contains the arbitration policy configuration and the
DecisionRecord that serves as the governing artifact for all Abraxas decisions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from enum import Enum
from abraxas.evidence.contract import Decision, EvidenceEnvelope


@dataclass
class ArbitrationPolicyConfig:
    """Configuration for arbitration policy."""
    
    # Confidence thresholds
    accept_confidence: float = 0.85
    verify_confidence: float = 0.60
    recompute_confidence: float = 0.40
    
    # Quality thresholds
    max_uncertainty: float = 0.30
    min_decision_margin: float = 0.15
    max_entropy: float = 0.70
    
    # Structural thresholds
    min_entity_consistency: float = 0.70
    min_relation_continuity: float = 0.70
    min_composition_order: float = 0.70
    
    # Behavior
    contradiction_escalates: bool = True
    cross_engine_agreement_threshold: float = 0.80
    require_verification_for_depth: int = 6
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "accept_confidence": self.accept_confidence,
            "verify_confidence": self.verify_confidence,
            "recompute_confidence": self.recompute_confidence,
            "max_uncertainty": self.max_uncertainty,
            "min_decision_margin": self.min_decision_margin,
            "max_entropy": self.max_entropy,
            "min_entity_consistency": self.min_entity_consistency,
            "min_relation_continuity": self.min_relation_continuity,
            "min_composition_order": self.min_composition_order,
            "contradiction_escalates": self.contradiction_escalates,
            "cross_engine_agreement_threshold": self.cross_engine_agreement_threshold,
            "require_verification_for_depth": self.require_verification_for_depth,
        }


@dataclass
class DecisionRecord:
    """Governing artifact for Abraxas decisions.
    
    Raw model output is not the decision record.
    This is the canonical record of what was decided and why.
    """
    
    decision_id: str
    request_id: str
    
    evidence_ids: List[str]
    engines_used: List[str]
    
    decision: Decision
    confidence: float
    
    accepted_claims: List[str] = field(default_factory=list)
    rejected_claims: List[str] = field(default_factory=list)
    unresolved_claims: List[str] = field(default_factory=list)
    
    verification_results: List[Dict[str, Any]] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    
    recomputation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    provenance: List[Dict[str, Any]] = field(default_factory=list)
    
    policy_version: str = "1.0"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "evidence_ids": self.evidence_ids,
            "engines_used": self.engines_used,
            "decision": self.decision.value,
            "confidence": self.confidence,
            "accepted_claims": self.accepted_claims,
            "rejected_claims": self.rejected_claims,
            "unresolved_claims": self.unresolved_claims,
            "verification_results": self.verification_results,
            "contradictions": self.contradictions,
            "recomputation_history": self.recomputation_history,
            "provenance": self.provenance,
            "policy_version": self.policy_version,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_arbitration(
        cls,
        request_id: str,
        envelopes: List[EvidenceEnvelope],
        decision: Decision,
        confidence: float,
        verification_results: List[Dict[str, Any]] = None,
        contradictions: List[str] = None,
        policy_version: str = "1.0"
    ) -> 'DecisionRecord':
        """Create a decision record from arbitration results."""
        import uuid
        
        evidence_ids = [e.evidence_id for e in envelopes]
        engines_used = list(set(e.engine for e in envelopes))
        
        accepted = []
        rejected = []
        unresolved = []
        
        for e in envelopes:
            top = e.candidate_outputs[0] if e.candidate_outputs else None
            if top:
                if decision == Decision.ACCEPT:
                    accepted.append(top.answer)
                elif decision == Decision.ABSTAIN:
                    rejected.append(top.answer)
                else:
                    unresolved.append(top.answer)
        
        return cls(
            decision_id=str(uuid.uuid4()),
            request_id=request_id,
            evidence_ids=evidence_ids,
            engines_used=engines_used,
            decision=decision,
            confidence=confidence,
            accepted_claims=accepted,
            rejected_claims=rejected,
            unresolved_claims=unresolved,
            verification_results=verification_results or [],
            contradictions=contradictions or [],
            policy_version=policy_version,
        )


class FailureType(Enum):
    """Explicit failure semantics — do not collapse into generic failure."""
    ENGINE_FAILURE = "ENGINE_FAILURE"
    REPRESENTATION_FAILURE = "REPRESENTATION_FAILURE"
    REASONING_FAILURE = "REASONING_FAILURE"
    DECISION_FAILURE = "DECISION_FAILURE"
    CALIBRATION_FAILURE = "CALIBRATION_FAILURE"
    VERIFICATION_FAILURE = "VERIFICATION_FAILURE"
    CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    POLICY_REJECTION = "POLICY_REJECTION"


class SelectiveComputePolicy:
    """Abraxas-controlled selective compute policy.
    
    The model does not decide how much compute it deserves.
    Abraxas determines the compute budget based on evidence quality.
    """
    
    def __init__(
        self,
        low_risk_max_tokens: int = 256,
        medium_risk_max_tokens: int = 1024,
        high_risk_max_tokens: int = 4096,
        max_retries: int = 2
    ):
        self.low_risk_max_tokens = low_risk_max_tokens
        self.medium_risk_max_tokens = medium_risk_max_tokens
        self.high_risk_max_tokens = high_risk_max_tokens
        self.max_retries = max_retries
    
    def determine_budget(self, envelope: EvidenceEnvelope, decision: Decision) -> Dict[str, Any]:
        """Determine compute budget based on evidence quality and decision."""
        
        if decision == Decision.ACCEPT:
            return {
                "max_tokens": self.low_risk_max_tokens,
                "temperature": 0.0,
                "retry": False,
                "reason": "HIGH_CONFIDENCE_ACCEPT"
            }
        
        elif decision == Decision.VERIFY:
            return {
                "max_tokens": self.medium_risk_max_tokens,
                "temperature": 0.0,
                "retry": True,
                "reason": "VERIFICATION_REQUIRED"
            }
        
        elif decision == Decision.RECOMPUTE:
            return {
                "max_tokens": self.high_risk_max_tokens,
                "temperature": 0.7,
                "retry": True,
                "reason": "RECOMPUTE_WITH_ADDITIONAL_BUDGET"
            }
        
        elif decision == Decision.ESCALATE:
            return {
                "max_tokens": self.high_risk_max_tokens,
                "temperature": 0.0,
                "retry": False,
                "reason": "ESCALATE_TO_HUMAN_OR_ALTERNATE_ENGINE"
            }
        
        else:  # ABSTAIN
            return {
                "max_tokens": 0,
                "temperature": 0.0,
                "retry": False,
                "reason": "INSUFFICIENT_EVIDENCE_ABSTAIN"
            }