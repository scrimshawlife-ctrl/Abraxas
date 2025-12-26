from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class GapKind(str, Enum):
    COVERAGE_GAP = "COVERAGE_GAP"
    INTEGRITY_GAP = "INTEGRITY_GAP"
    STRUCTURAL_GAP = "STRUCTURAL_GAP"
    GROUND_TRUTH_GAP = "GROUND_TRUTH_GAP"
    ROUTING_GAP = "ROUTING_GAP"
    LATENCY_GAP = "LATENCY_GAP"


class AcquisitionActionKind(str, Enum):
    ONLINE_FETCH = "ONLINE_FETCH"
    OFFLINE_REQUEST = "OFFLINE_REQUEST"


@dataclass(frozen=True)
class DataGap:
    gap_id: str
    kind: GapKind
    topic_key: Optional[str]
    horizon: Optional[str]
    domain: Optional[str]
    component_ids: List[str]
    portfolio_ids: List[str]
    symptoms: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    priority: float
    created_ts: str
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["kind"] = self.kind.value
        return data


@dataclass(frozen=True)
class AcquisitionAction:
    action_id: str
    kind: AcquisitionActionKind
    topic_key: Optional[str]
    horizon: Optional[str]
    method: str
    selector: Dict[str, Any]
    cadence_hint: Optional[str]
    expected_impact: Dict[str, Any]
    cost_estimate: Dict[str, Any]
    risk_estimate: Dict[str, Any]
    instructions: str
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["kind"] = self.kind.value
        return data


@dataclass(frozen=True)
class DataAcquisitionPlan:
    plan_id: str
    ts: str
    run_id: str
    gaps: List[DataGap]
    actions: List[AcquisitionAction]
    summary: Dict[str, Any]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "ts": self.ts,
            "run_id": self.run_id,
            "gaps": [gap.to_dict() for gap in self.gaps],
            "actions": [action.to_dict() for action in self.actions],
            "summary": dict(self.summary),
            "provenance": dict(self.provenance),
        }
