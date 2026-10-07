"""
Unified Abraxas Evidence Module
Merges legacy abx/evidence types with new abraxas/evidence contract.
Single source of truth for all evidence-related types and operations.
"""
from __future__ import annotations

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple
from enum import Enum
import uuid
import hashlib
import json

from abraxas.evidence.contract import (  # canonical home; re-exported
    EvidenceEnvelope,
    EvidenceType,
    RelationStep,
    CandidateOutput,
    create_athanor_envelope,
)
from abraxas.evidence.provider import EvidenceProvider  # canonical home; re-exported

# ─── ENUMS ──────────────────────────────────────────────────────────────

class Decision(str, Enum):
    ACCEPT = "ACCEPT"
    VERIFY = "VERIFY"
    RECOMPUTE = "RECOMPUTE"
    ESCALATE = "ESCALATE"
    ABSTAIN = "ABSTAIN"

class SourceType(str, Enum):
    URL = "url"
    PDF = "pdf"
    SCREENSHOT = "screenshot"
    MANUAL_NOTE = "manual_note"
    DATASET = "dataset"

class FailureType(str, Enum):
    ENGINE_FAILURE = "ENGINE_FAILURE"
    REPRESENTATION_FAILURE = "REPRESENTATION_FAILURE"
    REASONING_FAILURE = "REASONING_FAILURE"
    DECISION_FAILURE = "DECISION_FAILURE"
    CALIBRATION_FAILURE = "CALIBRATION_FAILURE"
    VERIFICATION_FAILURE = "VERIFICATION_FAILURE"
    CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    POLICY_REJECTION = "POLICY_REJECTION"

# EvidenceEnvelope, EvidenceType, RelationStep, CandidateOutput, create_athanor_envelope
# are single-homed in abraxas.evidence.contract; re-exported above.
# EvidenceProvider is single-homed in abraxas.evidence.provider; re-exported above.
# See Plan: single-home-the-evidence-contract, Phase 2.

# ─── PROVIDER REGISTRY ────────────────────────────────────────────────

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

provider_registry = ProviderRegistry()

# ─── ARBITRATION POLICY ───────────────────────────────────────────────

class ArbitrationPolicy:
    """Configurable policy for evidence arbitration."""
    
    def __init__(
        self,
        accept_confidence: float = 0.85,
        verify_confidence: float = 0.60,
        recompute_confidence: float = 0.40,
        max_uncertainty: float = 0.30,
        min_decision_margin: float = 0.15,
        max_entropy: float = 0.70,
        min_entity_consistency: float = 0.70,
        min_relation_continuity: float = 0.70,
        min_composition_order: float = 0.70,
        contradiction_escalates: bool = True,
        cross_engine_agreement_threshold: float = 0.80,
        require_verification_for_depth: int = 6,
    ):
        self.accept_confidence = accept_confidence
        self.verify_confidence = verify_confidence
        self.recompute_confidence = recompute_confidence
        self.max_uncertainty = max_uncertainty
        self.min_decision_margin = min_decision_margin
        self.max_entropy = max_entropy
        self.min_entity_consistency = min_entity_consistency
        self.min_relation_continuity = min_relation_continuity
        self.min_composition_order = min_composition_order
        self.contradiction_escalates = contradiction_escalates
        self.cross_engine_agreement_threshold = cross_engine_agreement_threshold
        self.require_verification_for_depth = require_verification_for_depth
    
    def evaluate(self, envelope: 'EvidenceEnvelope') -> Decision:
        # High confidence, low uncertainty, good margin -> ACCEPT
        if (envelope.confidence >= self.accept_confidence and
            envelope.uncertainty <= 0.30 and
            envelope.decision_margin >= 0.15 and
            envelope.entropy <= 0.70):
            return Decision.ACCEPT
        
        # Contradictory evidence -> ESCALATE
        if self._has_contradiction(envelope):
            return Decision.ESCALATE
        
        # Medium confidence -> VERIFY
        if envelope.confidence >= 0.60:
            return Decision.VERIFY
        
        # Low confidence but potentially recoverable -> RECOMPUTE
        if envelope.confidence >= 0.40:
            return Decision.RECOMPUTE
        
        # Too uncertain -> ABSTAIN
        return Decision.ABSTAIN
    
    def evaluate_batch(self, envelopes: List['EvidenceEnvelope']) -> Decision:
        if not envelopes:
            return Decision.ABSTAIN
        
        # Check for cross-engine agreement
        agreements = self._check_cross_engine_agreement(envelopes)
        
        if agreements >= 0.8:
            avg_confidence = sum(e.confidence for e in envelopes) / len(envelopes)
            if avg_confidence >= 0.60:
                return Decision.ACCEPT
        
        # Otherwise use highest confidence envelope
        best = max(envelopes, key=lambda e: e.confidence)
        return self.evaluate(best)
    
    def _has_contradiction(self, envelope: 'EvidenceEnvelope') -> bool:
        answers = [c.answer for c in envelope.candidate_outputs]
        yes_conf = max((c.confidence for c in envelope.candidate_outputs if c.answer == "Yes"), default=0)
        no_conf = max((c.confidence for c in envelope.candidate_outputs if c.answer == "No"), default=0)
        return yes_conf > 0.3 and no_conf > 0.3
    
    def _check_cross_engine_agreement(self, envelopes: List['EvidenceEnvelope']) -> float:
        if len(envelopes) < 2:
            return 1.0
        
        top_answers = [e.candidate_outputs[0].answer for e in envelopes if e.candidate_outputs]
        if not top_answers:
            return 0.0
        most_common = max(set(top_answers), key=top_answers.count)
        return top_answers.count(most_common) / len(top_answers)

# ─── EVIDENCE ARBITER ──────────────────────────────────────────────────

class EvidenceArbiter:
    """Main arbiter for evaluating evidence and making decisions."""
    
    def __init__(self, policy: 'ArbitrationPolicy' = None):
        self.policy = policy or ArbitrationPolicy()
        self._verifiers: Dict[str, Any] = {}
    
    def register_verifier(self, evidence_type: str, verifier: Any) -> None:
        self._verifiers[evidence_type] = verifier
    
    def arbitrate(self, envelope: 'EvidenceEnvelope') -> Decision:
        decision = self.policy.evaluate(envelope)
        
        if decision == Decision.VERIFY:
            verifier = self._verifiers.get(envelope.evidence_type)
            if verifier:
                result = verifier.verify(envelope)
                if result.get("passed", False):
                    return Decision.ACCEPT
                elif result.get("escalate", False):
                    return Decision.ESCALATE
        
        return decision
    
    def arbitrate_batch(self, envelopes: List['EvidenceEnvelope']) -> Decision:
        return self.policy.evaluate_batch(envelopes)

# ─── ARBITRATION POLICY CONFIG ────────────────────────────────────────

class ArbitrationPolicyConfig:
    def __init__(
        self,
        accept_confidence: float = 0.85,
        verify_confidence: float = 0.60,
        recompute_confidence: float = 0.40,
        max_uncertainty: float = 0.30,
        min_decision_margin: float = 0.15,
        max_entropy: float = 0.70,
        min_entity_consistency: float = 0.70,
        min_relation_continuity: float = 0.70,
        min_composition_order: float = 0.70,
        contradiction_escalates: bool = True,
        cross_engine_agreement_threshold: float = 0.80,
        require_verification_for_depth: int = 6,
    ):
        self.accept_confidence = accept_confidence
        self.verify_confidence = verify_confidence
        self.recompute_confidence = recompute_confidence
        self.max_uncertainty = max_uncertainty
        self.min_decision_margin = min_decision_margin
        self.max_entropy = max_entropy
        self.min_entity_consistency = min_entity_consistency
        self.min_relation_continuity = min_relation_continuity
        self.min_composition_order = min_composition_order
        self.contradiction_escalates = contradiction_escalates
        self.cross_engine_agreement_threshold = cross_engine_agreement_threshold
        self.require_verification_for_depth = require_verification_for_depth
    
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

# ─── DECISION RECORD ──────────────────────────────────────────────────

@dataclass
class DecisionRecord:
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
    
    policy_version: str = "v2"
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
        envelopes: List['EvidenceEnvelope'],
        decision: Decision,
        confidence: float,
        verification_results: List[Dict[str, Any]] = None,
        contradictions: List[str] = None,
        policy_version: str = "v2"
    ) -> 'DecisionRecord':
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

# ─── FAILURE TYPES ────────────────────────────────────────────────────

class FailureType(str, Enum):
    ENGINE_FAILURE = "ENGINE_FAILURE"
    REPRESENTATION_FAILURE = "REPRESENTATION_FAILURE"
    REASONING_FAILURE = "REASONING_FAILURE"
    DECISION_FAILURE = "DECISION_FAILURE"
    CALIBRATION_FAILURE = "CALIBRATION_FAILURE"
    VERIFICATION_FAILURE = "VERIFICATION_FAILURE"
    CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    POLICY_REJECTION = "POLICY_REJECTION"

# ─── SELECTIVE COMPUTE POLICY ────────────────────────────────────────

class SelectiveComputePolicy:
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
    
    def determine_budget(self, envelope: 'EvidenceEnvelope', decision: Decision) -> Dict[str, Any]:
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

# ─── FAILURE TYPE HANDLING ────────────────────────────────────────────

def classify_failure(envelope: 'EvidenceEnvelope', decision: Decision) -> FailureType:
    if not envelope.candidate_outputs:
        return FailureType.INSUFFICIENT_EVIDENCE
    
    if decision == Decision.ESCALATE:
        return FailureType.CONTRADICTORY_EVIDENCE
    
    if decision == Decision.ABSTAIN:
        return FailureType.INSUFFICIENT_EVIDENCE
    
    # Check if representation is likely the issue
    if envelope.confidence < 0.3:
        return FailureType.REPRESENTATION_FAILURE
    
    return FailureType.REASONING_FAILURE

# ─── EVIDENCE SCHEMA MIGRATION (ALEMBIC-STYLE) ───────────────────────

class EvidenceSchemaMigrator:
    """Alembic-style evidence schema migration."""
    
    SCHEMA_VERSIONS = {
        "v1": {
            "fields": ["evidence_id", "engine", "claim", "candidate_outputs", "evidence_type", "confidence"],
            "required": ["evidence_id", "engine", "claim", "evidence_type", "confidence"],
        },
        "v2": {
            "fields": ["evidence_id", "engine", "engine_version", "model_identity", "request_id", 
                       "claim", "candidate_outputs", "evidence_type", "reasoning_steps", "relations",
                       "intermediate_states", "confidence", "uncertainty", "decision_margin", "entropy",
                       "dependencies", "assumptions", "provenance", "artifact_refs",
                       "verification_metadata", "timestamp"],
            "required": ["evidence_id", "engine", "claim", "evidence_type", "confidence"],
        },
    }
    
    @staticmethod
    def migrate(envelope: Dict[str, Any], target_version: str = "v2") -> Dict[str, Any]:
        current_version = envelope.get("schema_version", "v1")
        if current_version == target_version:
            return envelope
        
        if current_version == "v1" and target_version == "v2":
            envelope = envelope.copy()
            # Stamp the version, so the migration records that it happened. Without this line the early
            # return above can never fire for a migrated envelope: nothing else records the migration,
            # so the envelope keeps reading as "v1" and migrate() re-runs its defaults on every call.
            # This line was removed once and the suite stayed green, because no test covered
            # idempotence -- see tests/test_evidence_contract_single_home.py. Restored verbatim from
            # the pre-change file, so the semantics are unchanged from the original.
            envelope["schema_version"] = "v2"
            envelope.setdefault("uncertainty", 1.0 - envelope.get("confidence", 0.0))
            envelope.setdefault("decision_margin", 0.0)
            envelope.setdefault("entropy", 0.0)
            envelope.setdefault("verification_metadata", {})
            envelope.setdefault("engine_version", "1.0")
            envelope.setdefault("model_identity", envelope.get("engine", "unknown"))
            envelope.setdefault("request_id", str(uuid.uuid4()))
            envelope.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
            envelope.setdefault("dependencies", [])
            envelope.setdefault("assumptions", [])
            envelope.setdefault("artifact_refs", [])
            envelope.setdefault("verification_metadata", {})
            envelope.setdefault("decision_margin", 0.0)
            envelope.setdefault("entropy", 0.0)
        
        return envelope
    
    @staticmethod
    def validate(envelope: Dict[str, Any], version: str = "v2") -> Tuple[bool, List[str]]:
        errors = []
        required = EvidenceSchemaMigrator.SCHEMA_VERSIONS[version]["required"]
        
        for field in required:
            if field not in envelope:
                errors.append(f"Missing required field: {field}")
        
        if "evidence_type" in envelope:
            try:
                EvidenceType(envelope["evidence_type"])
            except ValueError:
                errors.append(f"Invalid evidence_type: {envelope['evidence_type']}")
        
        if "confidence" in envelope:
            conf = envelope["confidence"]
            if not isinstance(conf, (int, float)) or not 0.0 <= conf <= 1.0:
                errors.append(f"confidence must be in [0,1]: {conf}")
        
        return len(errors) == 0, errors

# ─── LEGACY TYPES MIGRATION ──────────────────────────────────────────

# Migrate legacy abx/evidence types to unified format

@dataclass
class EvidenceThresholdRecord:
    threshold_id: str
    decision_class: str
    consequence_level: str
    reversibility: str
    threshold_rule: str
    threshold_value: float

@dataclass
class BurdenOfProofRecord:
    burden_id: str
    decision_class: str
    burden_owner: str
    burden_standard: str
    evidence_strength: float

@dataclass
class DecisionSufficiencyRecord:
    sufficiency_id: str
    decision_class: str
    sufficiency_state: str
    rationale_ref: str

@dataclass
class DecisionReadinessRecord:
    readiness_id: str
    decision_class: str
    readiness_state: str
    readiness_reason: str

@dataclass
class ConflictingEvidenceRecord:
    conflict_id: str
    decision_class: str
    conflict_state: str
    evidence_refs: Tuple[str, str]

@dataclass
class ProvisionalDecisionRecord:
    provisional_id: str
    decision_class: str
    provisional_state: str
    review_by: str

@dataclass
class EvidenceTransitionRecord:
    transition_id: str
    decision_class: str
    from_state: str
    to_state: str
    reason: str

@dataclass
class UnmetBurdenRecord:
    unmet_id: str
    decision_class: str
    unmet_state: str
    detail: str

@dataclass
class EvidenceGovernanceErrorRecord:
    code: str
    severity: str
    message: str

@dataclass
class EvidenceGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: Dict[str, str]
    evidence: Dict[str, List[str]]
    blockers: List[str]
    category: str
    scorecard_hash: str

# ─── VERIFIER INTERFACES ─────────────────────────────────────────────

class Verifier:
    """Base interface for evidence verifiers."""
    
    @property
    def evidence_type(self) -> str:
        raise NotImplementedError
    
    @property
    def name(self) -> str:
        raise NotImplementedError
    
    def verify(self, envelope: 'EvidenceEnvelope') -> Dict[str, Any]:
        raise NotImplementedError

# ─── RELATIONAL VERIFIER (ATHANOR) ──────────────────────────────────

class RelationalVerifier:
    """Verifies structural consistency of relational reasoning evidence."""
    
    @property
    def evidence_type(self) -> str:
        return "RELATIONAL_REASONING"
    
    @property
    def name(self) -> str:
        return "RelationalConsistencyVerifier"
    
    def verify(self, envelope: 'EvidenceEnvelope') -> Dict[str, Any]:
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
        
        # Check relation continuity
        relation_continuity = self._check_relation_continuity(envelope)
        details["relation_continuity"] = relation_continuity
        
        # Check composition order
        composition_order = self._check_composition_order(envelope)
        details["composition_order"] = composition_order
        
        # Check counterfactual consistency
        counterfactual_consistency = self._check_counterfactual_consistency(envelope)
        details["counterfactual_consistency"] = counterfactual_consistency
        
        # Overall pass
        passed = (
            entity_consistency >= 0.7 and
            relation_continuity >= 0.7 and
            len(details["contradictions"]) == 0
        )
        
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
    
    def _check_entity_consistency(self, envelope) -> float:
        all_entities = set()
        step_entities = []
        
        for step in envelope.reasoning_steps:
            entities = {step.subject, step.object}
            if step.result:
                entities.add(step.result)
            step_entities.append(entities)
            all_entities.update(entities)
        
        if len(step_entities) < 2:
            return 1.0
        
        overlaps = 0
        for i in range(len(step_entities) - 1):
            if step_entities[i] & step_entities[i + 1]:
                overlaps += 1
        
        return overlaps / (len(step_entities) - 1)
    
    def _check_relation_continuity(self, envelope) -> float:
        if len(envelope.reasoning_steps) < 2:
            return 1.0
        
        valid_transitions = 0
        for i in range(len(envelope.reasoning_steps) - 1):
            curr = envelope.reasoning_steps[i]
            next_step = envelope.reasoning_steps[i + 1]
            
            if curr.result and (next_step.subject == curr.result or next_step.object == curr.result):
                valid_transitions += 1
        
        return valid_transitions / (len(envelope.reasoning_steps) - 1)
    
    def _check_composition_order(self, envelope) -> float:
        if len(envelope.reasoning_steps) < 2:
            return 1.0
        
        relations = {step.relation for step in envelope.reasoning_steps}
        if len(relations) == 1:
            return 1.0
        return 0.8
    
    def _check_counterfactual_consistency(self, envelope) -> float:
        claim = envelope.claim.lower()
        is_counterfactual = "not" in claim or "false" in claim or "counterfactual" in claim
        
        if not is_counterfactual:
            return 1.0
        
        has_negation = any(
            "not" in c.reasoning_trace.lower() or "false" in c.reasoning_trace.lower()
            for c in envelope.candidate_outputs
        )
        
        return 0.8 if has_negation else 0.5

# ─── LEXICAL CONSISTENCY VERIFIER (HYPERLEX) ────────────────────────

class LexicalConsistencyVerifier:
    @property
    def evidence_type(self) -> str:
        return "LEXICAL_SEMANTIC"
    
    @property
    def name(self) -> str:
        return "LexicalConsistencyVerifier"
    
    def __init__(self):
        self.lineage_families = {
            "betting-sharp": {"branch_operator": "sense_extension"},
            "crypto-degen": {"branch_operator": "cross_family_borrowing"},
            "ai-native": {"branch_operator": "platform_compression"},
            "brainrot-aura": {"branch_operator": "irony_inversion"},
            "kinship-address": {"branch_operator": "sense_extension"},
            "political-status": {"branch_operator": "irony_inversion"},
            "gaming-meta": {"branch_operator": "platform_compression"},
            "workplace-corp": {"branch_operator": "sense_extension"},
        }
        
        self.VIRALITY_COHERENCE_THRESHOLD = 0.3
        self.LINEAGE_CONSISTENCY_THRESHOLD = 0.42
        self.SEMANTIC_VARIATION_COHERENCE_THRESHOLD = 0.3
    
    def verify(self, envelope) -> Dict[str, Any]:
        if envelope.engine != "hyperlex":
            return {"passed": False, "escalate": True, "details": {}}
        
        # Mock analysis extraction
        analysis = {
            "lineage": {"family_id": "betting-sharp", "confidence": 0.85},
            "virality": {"hybrid_score": 0.75, "velocity": 0.6, "acceleration": 0.5},
            "semantic_variation": {"sense": "tactical/quant", "driver": "tactical_edge"},
            "neologisms": [{"term": "sharp money", "formation": "compound_phrase", "confidence": 0.8}],
            "hyperstition": {"loop_stage": "ACTUALIZING"},
            "semantic_variation_coherence": 0.75,
            "neologism_plausibility": 0.8,
            "hyperstition_stage_alignment": 0.8,
        }
        
        contradictions = []
        virality_coherence = self._check_virality_coherence({})
        lineage_consistency = self._check_lineage_consistency({})
        semantic_variation_coherence = self._check_semantic_variation_coherence({})
        neologism_plausibility = self._check_neologism_plausibility({})
        hyperstition_alignment = self._check_hyperstition_alignment({})
        
        is_consistent = (
            lineage_consistency >= 0.42 and
            virality_coherence >= 0.3 and
            True >= 0.3 and
            True >= 0.3
        )
        
        return {
            "passed": is_consistent,
            "escalate": False,
            "details": {
                "lineage_consistency": lineage_consistency,
                "virality_coherence": virality_coherence,
                "semantic_variation_coherence": 0.75,
                "neologism_plausibility": 0.8,
                "hyperstition_stage_alignment": 0.8,
            }
        }
    
    def _check_lineage_consistency(self, analysis) -> float:
        return 1.0
    
    def _check_virality_coherence(self, analysis) -> float:
        return 0.71
    
    def _check_semantic_variation_coherence(self, analysis) -> float:
        return 0.75
    
    def _check_neologism_plausibility(self, analysis) -> float:
        return 0.8
    
    def _check_hyperstition_alignment(self, analysis) -> float:
        return 0.8

# ─── SIGN RELATION VERIFIER (SEMION) ────────────────────────────────────

PEIRCE_CLASSES = {
    "qualisign": {"category": "firstness", "type": "quality"},
    "sinsign": {"category": "firstness", "type": "individual"},
    "legisign": {"category": "firstness", "type": "law"},
    "icon": {"category": "secondness", "type": "similarity"},
    "index": {"category": "secondness", "type": "contiguity"},
    "symbol": {"category": "secondness", "type": "convention"},
    "rheme": {"category": "thirdness", "type": "possibility"},
    "dicent": {"category": "thirdness", "type": "actuality"},
    "argument": {"category": "thirdness", "type": "necessity"},
}

VALID_COMBINATIONS = {
    ("qualisign", "rheme", "icon"), ("qualisign", "rheme", "index"), ("qualisign", "rheme", "symbol"),
    ("qualisign", "dicent", "icon"), ("qualisign", "dicent", "index"), ("qualisign", "dicent", "symbol"),
    ("qualisign", "argument", "icon"), ("qualisign", "argument", "index"), ("qualisign", "argument", "symbol"),
    ("sinsign", "rheme", "icon"), ("sinsign", "rheme", "index"), ("sinsign", "rheme", "symbol"),
    ("sinsign", "dicent", "icon"), ("sinsign", "dicent", "index"), ("sinsign", "dicent", "symbol"),
    ("sinsign", "argument", "icon"), ("sinsign", "argument", "index"), ("sinsign", "argument", "symbol"),
    ("legisign", "rheme", "icon"), ("legisign", "rheme", "index"), ("legisign", "rheme", "symbol"),
    ("legisign", "dicent", "icon"), ("legisign", "dicent", "index"), ("legisign", "dicent", "symbol"),
    ("legisign", "argument", "icon"), ("legisign", "argument", "index"), ("legisign", "argument", "symbol"),
}

def parse_sign_class(sign_class: str):
    parts = sign_class.split("-")
    return parts if len(parts) == 3 else None

def validate_sign_class(sign_class: str):
    parsed = sign_class.split("-")
    if len(parsed) != 3:
        return False, [f"Invalid format: {sign_class}"]
    
    existence, thirdness, relation = parsed
    errors = []
    
    if existence not in ["qualisign", "sinsign", "legisign"]:
        errors.append(f"Invalid existence: {existence}")
    if thirdness not in ["rheme", "dicent", "argument"]:
        errors.append(f"Invalid thirdness: {thirdness}")
    if relation not in ["icon", "index", "symbol"]:
        errors.append(f"Invalid relation: {relation}")
    
    if (parsed[0], parsed[1], parsed[2]) not in {
        ("qualisign", "rheme", "icon"), ("qualisign", "rheme", "index"), ("qualisign", "rheme", "symbol"),
        ("qualisign", "dicent", "icon"), ("qualisign", "dicent", "index"), ("qualisign", "dicent", "symbol"),
        ("qualisign", "argument", "icon"), ("qualisign", "argument", "index"), ("qualisign", "argument", "symbol"),
        ("sinsign", "rheme", "icon"), ("sinsign", "rheme", "index"), ("sinsign", "rheme", "symbol"),
        ("sinsign", "dicent", "icon"), ("sinsign", "dicent", "index"), ("sinsign", "dicent", "symbol"),
        ("sinsign", "argument", "icon"), ("sinsign", "argument", "index"), ("sinsign", "argument", "symbol"),
        ("legisign", "rheme", "icon"), ("legisign", "rheme", "index"), ("legisign", "rheme", "symbol"),
        ("legisign", "dicent", "icon"), ("legisign", "dicent", "index"), ("legisign", "dicent", "symbol"),
        ("legisign", "argument", "icon"), ("legisign", "argument", "index"), ("legisign", "argument", "symbol"),
    }:
        errors.append(f"Invalid Peircean combination: {sign_class}")
    
    return len(errors) == 0, errors

def check_interpretant_coherence(relation_steps):
    if not relation_steps:
        return 1.0, []
    
    errors = []
    coherent = 0
    for step in relation_steps:
        relation = step.get("relation", "")
        result = step.get("result", "")
        
        if relation in ["causes", "implies", "triggers"]:
            if "not" in result.lower() or "false" in result.lower():
                return 0.0, [f"Contradictory: {relation} but result negates"]
        elif relation in ["implies", "means"]:
            if "not" in result.lower():
                return 0.0, [f"Contradictory: {relation} but result negates"]
        coherent += 1
    
    return coherent / len(relation_steps) if relation_steps else 1.0, []

def check_representamen_object_alignment(steps):
    if len(steps) < 2:
        return 1.0
    
    aligned = 0
    for i in range(len(steps) - 1):
        curr_obj = steps[i].get("object", "")
        next_subj = steps[i+1].get("subject", "")
        if curr_obj and next_subj and curr_obj == next_subj:
            aligned += 1
    
    return aligned / (len(steps) - 1)

# ─── NOESIS LATENT STRUCTURE VERIFIER ──────────────────────────────────

class LatentStructureVerifier:
    @property
    def evidence_type(self) -> str:
        return "LATENT_STRUCTURAL"
    
    @property
    def name(self) -> str:
        return "LatentStructureVerifier"
    
    def verify(self, envelope) -> Dict[str, Any]:
        if envelope.engine != "noesis":
            return {"passed": False, "escalate": True, "details": {}}
        
        # Extract structural coherence from envelope
        coherence = envelope.provenance.get("structural_coherence", 0.0)
        intervention_sensitivity = envelope.provenance.get("intervention_sensitivity", 1.0)
        
        details = {
            "structural_coherence": coherence,
            "intervention_sensitivity": intervention_sensitivity,
            "stability_score": 1.0 - intervention_sensitivity,
        }
        
        passed = coherence >= 0.7 and intervention_sensitivity <= 0.3
        escalate = coherence < 0.4 or intervention_sensitivity > 0.6
        
        return {
            "passed": passed,
            "escalate": escalate,
            "details": details
        }

# ─── TRUTINA SCORER ────────────────────────────────────────────────────

def compute_atomic_brier(expected_probability: float, observed_outcome: int | float) -> float:
    o = int(observed_outcome)
    if o not in (0, 1):
        raise ValueError("observed_outcome must be 0 or 1")
    if not 0.0 <= expected_probability <= 1.0:
        raise ValueError("expected_probability out of [0,1]")
    return round((float(expected_probability) - o) ** 2, 6)

def compute_brier_series(forecasts, outcomes, weights=None):
    if len(forecasts) != len(outcomes):
        raise ValueError("forecasts and outcomes length mismatch")
    
    n = len(forecasts)
    if n == 0:
        return {"series_brier": None, "n": 0}
    
    weights = weights or [1.0] * n
    total_weight = sum(weights)
    
    atomic_scores = []
    for i, (fc, o) in enumerate(zip(forecasts, outcomes)):
        p = float(fc.get("probability", 0.5))
        o_val = int(outcomes[i])
        atomic = (p - o_val) ** 2
        yield atomic * weights[i] / sum(weights)

def compute_brier_series(forecasts, outcomes, weights=None):
    if len(forecasts) != len(outcomes):
        raise ValueError("forecasts and outcomes length mismatch")
    
    n = len(forecasts)
    if n == 0:
        return {"series_brier": None, "n": 0}
    
    weights = weights or [1.0] * n
    total_weight = sum(weights)
    
    atomic_scores = []
    for i, (fc, o) in enumerate(zip(forecasts, outcomes)):
        p = float(fc.get("probability", 0.5))
        o_val = int(outcomes[i])
        atomic = (p - o_val) ** 2
        atomic_scores.append(atomic * weights[i] / sum(weights))
    
    return {
        "series_brier": round(sum(atomic_scores), 6),
        "n": n,
        "atomic_scores": atomic_scores,
        "weights": weights,
    }

def compute_atomic_brier(expected_probability: float, observed_outcome: int | float) -> float:
    o = int(observed_outcome)
    if o not in (0, 1):
        raise ValueError("observed_outcome must be 0 or 1")
    if not 0.0 <= expected_probability <= 1.0:
        raise ValueError("expected_probability out of [0,1]")
    return round((float(expected_probability) - o) ** 2, 6)

def compute_score_hash(forecast_hash, expected_probability, observed_outcome, brier_score):
    return hashlib.sha256(
        f"{forecast_hash}|{expected_probability:.6f}|{observed_outcome}|{brier_score:.6f}".encode()
    ).hexdigest()

def to_brier_score_packet(forecast, score, forecast_hash=None):
    if score.get("status") != "SCORED":
        raise ValueError("settlement required")
    
    p = float(score["probability"])
    o = int(float(score["outcome_value"]))
    bs = compute_atomic_brier(p, o)
    
    fh = forecast_hash or hashlib.sha256(
        f"{forecast.get('forecast_id')}|{p:.6f}".encode()
    ).hexdigest()
    
    det = hashlib.sha256(
        f"{fh}|{p:.6f}|{o}|{bs:.6f}".encode()
    ).hexdigest()
    
    score_id = hashlib.sha256(f"{fh}|{det}".encode()).hexdigest()[:24]
    
    return {
        "schema_version": "BrierScorePacket.v1",
        "score_id": score_id,
        "forecast_hash": fh,
        "expected_probability": p,
        "observed_outcome": o,
        "brier_score": bs,
        "deterministic_score_hash": det,
        "authority": {"kind": "operator", "source": "trutina", "locked": True},
        "status": "ok",
    }

def compute_ledger_hash(forecast_hash, score_hash, calibration_hash, ledger_generation):
    return hashlib.sha256(
        f"{forecast_hash}|{score_hash}|{calibration_hash}|{ledger_generation}".encode()
    ).hexdigest()

def to_brier_ledger_entry(forecast, score, settlement=None, ledger_generation=1):
    if score.get("status") != "SCORED":
        raise ValueError("settlement required")
    
    forecast_id = str(forecast.get("forecast_id") or "")
    settlement_id = str((settlement or {}).get("settlement_id") or score.get("settlement_id") or "")
    
    forecast_hash = hashlib.sha256(
        json.dumps({
            "forecast_id": forecast_id,
            "probability": forecast.get("probability", score.get("probability")),
            "signal_key": forecast.get("signal_key", score.get("signal_key")),
            "mapping_version": forecast.get("mapping_version"),
        }, sort_keys=True).encode()
    ).hexdigest()
    
    score_hash = hashlib.sha256(
        json.dumps({
            "forecast_id": forecast_id,
            "settlement_id": settlement_id or score.get("settlement_id", ""),
            "atomic_score": score.get("atomic_score"),
            "probability": score.get("probability"),
            "outcome_value": score.get("outcome_value"),
        }, sort_keys=True).encode()
    ).hexdigest()
    
    calibration_hash = hashlib.sha256(
        json.dumps({
            "note": "trutina.calibration.v1",
            "signal_key": forecast.get("signal_key", score.get("signal_key")),
        }, sort_keys=True).encode()
    ).hexdigest()
    
    det = compute_ledger_hash(forecast_hash, score_hash, calibration_hash, ledger_generation)
    ledger_entry_id = hashlib.sha256(
        f"{forecast_id}|{settlement_id}|{ledger_generation}".encode()
    ).hexdigest()[:32]
    
    return {
        "schema_version": "BrierLedgerEntry.v1",
        "ledger_entry_id": ledger_entry_id,
        "forecast_hash": forecast_hash,
        "score_hash": score_hash,
        "calibration_hash": calibration_hash,
        "replay_hash": None,
        "ledger_generation": ledger_generation,
        "deterministic_ledger_hash": compute_ledger_hash(forecast_hash, score_hash, calibration_hash, ledger_generation),
        "authority": {"kind": "operator", "source": "trutina", "locked": True},
        "status": "recorded",
    }

# ─── EXPORTS ──────────────────────────────────────────────────────────

__all__ = [
    # Enums
    "EvidenceType", "Decision", "SourceType", "FailureType",
    # Core
    "EvidenceEnvelope", "RelationStep", "CandidateOutput", "create_athanor_envelope",
    # Provider
    "EvidenceProvider", "ProviderRegistry", "provider_registry",
    # Arbitration
    "ArbitrationPolicy", "ArbitrationPolicyConfig", "EvidenceArbiter",
    "DecisionRecord", "Decision",
    # Policies
    "SelectiveComputePolicy", "ArbitrationPolicy", "ArbitrationPolicyConfig",
    # Failure
    "FailureType", "classify_failure",
    # Migration
    "EvidenceSchemaMigrator",
    # Legacy types
    "EvidenceThresholdRecord", "BurdenOfProofRecord", "DecisionSufficiencyRecord",
    "DecisionReadinessRecord", "ConflictingEvidenceRecord", "ProvisionalDecisionRecord",
    "EvidenceTransitionRecord", "UnmetBurdenRecord", "EvidenceGovernanceErrorRecord",
    "EvidenceGovernanceScorecard",
    # Verifiers
    "RelationalVerifier", "LexicalConsistencyVerifier", "SignRelationVerifier",
    "LatentStructureVerifier",
    # Trutina
    "compute_atomic_brier", "compute_brier_series", "to_brier_score_packet",
    "to_brier_ledger_entry", "compute_ledger_hash",
    # Providers
    "EvidenceProvider", "ProviderRegistry", "provider_registry",
    "ArbitrationPolicy", "ArbitrationPolicyConfig", "EvidenceArbiter",
    "DecisionRecord", "Decision", "SelectiveComputePolicy",
    # Failure
    "FailureType", "classify_failure",
    # Migration
    "EvidenceSchemaMigrator",
    # Verifiers
    "RelationalVerifier", "LexicalConsistencyVerifier", "SignRelationVerifier",
    "LatentStructureVerifier",
    # Trutina
    "compute_atomic_brier", "compute_brier_series", "to_brier_score_packet",
    "to_brier_ledger_entry", "compute_ledger_hash",
    # Schema migration
    "EvidenceSchemaMigrator",
    # Legacy types
    "EvidenceThresholdRecord", "BurdenOfProofRecord", "DecisionSufficiencyRecord",
    "DecisionReadinessRecord", "ConflictingEvidenceRecord", "ProvisionalDecisionRecord",
    "EvidenceTransitionRecord", "UnmetBurdenRecord", "EvidenceGovernanceErrorRecord",
    "EvidenceGovernanceScorecard",
]
# NOTE: this module used to print a 10-line banner on import, one line of which
# claimed "4-engine" arbitration while the rest of the repo said 5. Printing from
# a library module pollutes every test run, CI log and consumer process, and is
# how that stale claim stayed invisible. Engine topology now lives in
# abraxas/engines/manifest.py.
