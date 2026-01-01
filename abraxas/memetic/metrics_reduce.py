from __future__ import annotations

from typing import Any, Dict, List


def mean(xs: List[float]) -> float:
    if not xs:
        return 0.0
    return float(sum(xs) / float(len(xs)))


def reduce_provenance_means(profiles: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Extract mean values from temporal profiles.
    Expected keys (best-effort):
      - attribution_strength
      - source_diversity
      - consensus_gap
      - manipulation_risk_mean / manipulation_risk
    """
    attribution: List[float] = []
    source_diversity: List[float] = []
    consensus_gap: List[float] = []
    manipulation_risk: List[float] = []
    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        if "attribution_strength_uplifted" in profile:
            attribution.append(float(profile.get("attribution_strength_uplifted") or 0.0))
        elif "attribution_strength" in profile:
            attribution.append(float(profile.get("attribution_strength") or 0.0))
        if "source_diversity_uplifted" in profile:
            source_diversity.append(float(profile.get("source_diversity_uplifted") or 0.0))
        elif "source_diversity" in profile:
            source_diversity.append(float(profile.get("source_diversity") or 0.0))
        if "consensus_gap" in profile:
            consensus_gap.append(float(profile.get("consensus_gap") or 0.0))
        if "manipulation_risk_mean" in profile:
            manipulation_risk.append(float(profile.get("manipulation_risk_mean") or 0.0))
        elif "manipulation_risk" in profile:
            manipulation_risk.append(float(profile.get("manipulation_risk") or 0.0))

    return {
        "attribution_strength_mean": mean(attribution),
        "source_diversity_mean": mean(source_diversity),
        "consensus_gap_mean": mean(consensus_gap),
        "manipulation_risk_mean": mean(manipulation_risk),
    }
