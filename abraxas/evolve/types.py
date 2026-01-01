from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class ProposalKind(str, Enum):
    SIW_TIGHTEN_SOURCE = "SIW_TIGHTEN_SOURCE"
    SIW_LOOSEN_SOURCE = "SIW_LOOSEN_SOURCE"
    VECTOR_NODE_CADENCE_CHANGE = "VECTOR_NODE_CADENCE_CHANGE"
    OFFLINE_EVIDENCE_ESCALATION = "OFFLINE_EVIDENCE_ESCALATION"
    EVIDENCE_ESCALATION = "EVIDENCE_ESCALATION"
    COMPONENT_FOCUS_SUGGESTION = "COMPONENT_FOCUS_SUGGESTION"
    CALIBRATION_POLICY_ADJUSTMENT = "CALIBRATION_POLICY_ADJUSTMENT"


@dataclass(frozen=True)
class EvolutionProposal:
    proposal_id: str
    kind: ProposalKind
    target: Dict[str, Any]
    rationale: Dict[str, Any]
    recommended_change: Dict[str, Any]
    expected_impact: Dict[str, Any]
    risk: Dict[str, Any]
    confidence: float
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["kind"] = self.kind.value
        return data


@dataclass(frozen=True)
class EvolutionProposalPack:
    pack_id: str
    run_id: str
    ts: str
    proposals: List[EvolutionProposal]
    summary: Dict[str, Any]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "run_id": self.run_id,
            "ts": self.ts,
            "proposals": [proposal.to_dict() for proposal in self.proposals],
            "summary": dict(self.summary),
            "provenance": dict(self.provenance),
        }
