"""
Abraxas Evidence Envelope — canonical contract for all reasoning engines.

This is the single source of truth for evidence flowing into Abraxas.
No engine may emit evidence that does not conform to this contract.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid


class EvidenceType(str, Enum):
    RELATIONAL_REASONING = "RELATIONAL_REASONING"
    LEXICAL_SEMANTIC = "LEXICAL_SEMANTIC"
    LATENT_STRUCTURAL = "LATENT_STRUCTURAL"
    CALIBRATION = "CALIBRATION"
    FACTUAL = "FACTUAL"
    COUNTERFACTUAL = "COUNTERFACTUAL"
    MULTIMODAL = "MULTIMODAL"
    SIGN_RELATION = "SIGN_RELATION"
    TEMPORAL_REASONING = "TEMPORAL_REASONING"
    RESONANCE_ANALYSIS = "RESONANCE_ANALYSIS"
    NARRATIVE_SYNTHESIS = "NARRATIVE_SYNTHESIS"
    MULTIMODAL_INTEGRATION = "MULTIMODAL_INTEGRATION"
    PERSISTENT_MEMORY = "PERSISTENT_MEMORY"
    YGGDRASIL_DECISION = "YGGDRASIL_DECISION"
    VIDEO_ANALYSIS = "VIDEO_ANALYSIS"


class Decision(str, Enum):
    ACCEPT = "ACCEPT"
    VERIFY = "VERIFY"
    RECOMPUTE = "RECOMPUTE"
    ESCALATE = "ESCALATE"
    ABSTAIN = "ABSTAIN"
    REJECT = "REJECT"


@dataclass
class RelationStep:
    relation: str
    subject: str
    object: str
    result: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CandidateOutput:
    answer: str
    confidence: float
    reasoning_trace: str
    relation_steps: List[RelationStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceEnvelope:
    """Canonical evidence contract for Abraxas."""

    #: Describes the FORMAT of this artifact, not its content. It exists because
    #: `EvidenceSchemaMigrator` reads it to decide whether migration is needed
    #: (`abraxas/evidence/__init__.py`, `current_version = envelope.get("schema_version", "v1")`),
    #: and writes it back so that a second migration call is a no-op. It is therefore present on the
    #: artifact but excluded from any identity/content hash, the same identity-versus-metadata rule this
    #: repository applies to `timestamp` and to the lexicon content fingerprint.
    schema_version: str = "v2"

    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    engine: str = ""
    engine_version: str = ""
    model_identity: str = ""
    request_id: str = ""
    
    claim: str = ""
    candidate_outputs: List[CandidateOutput] = field(default_factory=list)
    
    evidence_type: EvidenceType = EvidenceType.RELATIONAL_REASONING
    reasoning_steps: List[RelationStep] = field(default_factory=list)
    relations: List[str] = field(default_factory=list)
    intermediate_states: List[Dict[str, Any]] = field(default_factory=list)
    
    confidence: float = 0.0
    uncertainty: float = 0.0
    decision_margin: float = 0.0
    entropy: float = 0.0
    
    dependencies: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    
    provenance: Dict[str, Any] = field(default_factory=dict)
    artifact_refs: List[str] = field(default_factory=list)
    
    verification_metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to canonical JSON for storage and transmission."""
        return {
            "evidence_id": self.evidence_id,
            "engine": self.engine,
            "engine_version": self.engine_version,
            "model_identity": self.model_identity,
            "request_id": self.request_id,
            "claim": self.claim,
            "candidate_outputs": [c.__dict__ for c in self.candidate_outputs],
            "evidence_type": self.evidence_type.value,
            "reasoning_steps": [s.__dict__ for s in self.reasoning_steps],
            "relations": self.relations,
            "intermediate_states": self.intermediate_states,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "decision_margin": self.decision_margin,
            "entropy": self.entropy,
            "dependencies": self.dependencies,
            "assumptions": self.assumptions,
            "provenance": self.provenance,
            "artifact_refs": self.artifact_refs,
            "verification_metadata": self.verification_metadata,
            "timestamp": self.timestamp,
            "schema_version": self.schema_version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvidenceEnvelope':
        """Reconstruct from canonical JSON."""
        data = data.copy()
        data["evidence_type"] = EvidenceType(data["evidence_type"])
        data["candidate_outputs"] = [
            CandidateOutput(**c) for c in data.get("candidate_outputs", [])
        ]
        data["reasoning_steps"] = [
            RelationStep(**s) for s in data.get("reasoning_steps", [])
        ]
        return cls(**data)


def create_athanor_envelope(
    claim: str,
    candidates: List[CandidateOutput],
    model_identity: str,
    request_id: str,
    relations: Optional[List[str]] = None,
    reasoning_steps: Optional[List[RelationStep]] = None,
    confidence: float = 0.0,
    uncertainty: float = 0.0,
    provenance: Optional[Dict[str, Any]] = None
) -> EvidenceEnvelope:
    """Helper to create properly typed Athanor evidence."""
    return EvidenceEnvelope(
        engine="athanor",
        engine_version="1.0",
        model_identity=model_identity,
        request_id=request_id,
        claim=claim,
        candidate_outputs=candidates,
        evidence_type=EvidenceType.RELATIONAL_REASONING,
        relations=relations or [],
        reasoning_steps=reasoning_steps or [],
        confidence=confidence,
        uncertainty=uncertainty,
        provenance=provenance or {"source": "unspecified"},
    )