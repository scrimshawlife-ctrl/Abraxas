from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class DMX:
    version: str
    synthetic_likelihood: float
    attribution_strength: float
    coordination_signature: float
    incentive_gradient: float
    forensics_flags: int
    source_diversity: float
    consensus_gap: float
    overall_manipulation_risk: float
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def compute_dmx(
    *,
    sources: Optional[List[Dict[str, Any]]] = None,
    signals: Optional[Dict[str, Any]] = None,
) -> DMX:
    """
    Deterministic heuristic DMX (v0.1).
    - sources: list of source dicts (may include {domain, type, credibility, independent, disagrees, has_primary})
    - signals: dict of extracted flags (may include {ai_markers, bot_markers, incentive_markers, forensics_flags})
    """
    sources = sources or []
    signals = signals or {}

    has_primary = 0
    credible = 0
    independent = 0
    disagrees = 0
    for source in sources:
        if not isinstance(source, dict):
            continue
        if bool(source.get("has_primary")):
            has_primary += 1
        credibility = float(source.get("credibility") or 0.0)
        if credibility >= 0.6:
            credible += 1
        if bool(source.get("independent")):
            independent += 1
        if bool(source.get("disagrees")):
            disagrees += 1

    total = max(1, len(sources))
    attribution_strength = _clamp01((0.55 * (has_primary / total)) + (0.45 * (credible / total)))
    source_diversity = _clamp01(independent / total)
    consensus_gap = _clamp01(disagrees / total)

    ai_markers = float(signals.get("ai_markers") or 0.0)
    bot_markers = float(signals.get("bot_markers") or 0.0)
    incentive_markers = float(signals.get("incentive_markers") or 0.0)
    forensics_flags = int(signals.get("forensics_flags") or 0)

    synthetic_likelihood = _clamp01(ai_markers)
    coordination_signature = _clamp01(bot_markers)
    incentive_gradient = _clamp01(incentive_markers)

    risk = (
        0.22 * synthetic_likelihood
        + 0.18 * coordination_signature
        + 0.18 * incentive_gradient
        + 0.14 * _clamp01(forensics_flags / 6.0)
        + 0.12 * (1.0 - attribution_strength)
        + 0.08 * (1.0 - source_diversity)
        + 0.08 * consensus_gap
    )
    overall = _clamp01(risk)

    return DMX(
        version="dmx.v0.1",
        synthetic_likelihood=synthetic_likelihood,
        attribution_strength=attribution_strength,
        coordination_signature=coordination_signature,
        incentive_gradient=incentive_gradient,
        forensics_flags=forensics_flags,
        source_diversity=source_diversity,
        consensus_gap=consensus_gap,
        overall_manipulation_risk=overall,
        provenance={"method": "compute_dmx.v0.1"},
    )
