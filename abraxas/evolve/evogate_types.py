from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ReplayResult:
    """
    v0.1: abstract replay result container.
    Later: wire to your real CRE/replay runner.
    """

    ok: bool
    metric_deltas: Dict[str, float]
    notes: List[str]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvoGateReport:
    run_id: str
    ts: str
    pack_id: str
    applied_proposal_ids: List[str]
    candidate_policy_path: str
    baseline_metrics_path: Optional[str]
    replay: ReplayResult
    promote_recommended: bool
    thresholds: Dict[str, Any]
    notes: List[str]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["replay"] = self.replay.to_dict()
        return d
