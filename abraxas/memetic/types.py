from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List


@dataclass(frozen=True)
class TermCandidate:
    term_id: str
    term: str
    n: int
    count: int
    first_seen_ts: str
    last_seen_ts: str
    velocity_per_day: float
    half_life_est_s: float
    novelty_score: float
    propagation_score: float
    manipulation_risk: float
    tags: List[str]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MimeticWeatherUnit:
    unit_id: str
    label: str
    kind: str
    intensity: float
    direction: str
    confidence: float
    first_seen_ts: str
    last_seen_ts: str
    horizon_tags: List[str]
    supporting_terms: List[str]
    disinfo_metrics: Dict[str, float]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
