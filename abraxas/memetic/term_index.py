from __future__ import annotations

from typing import Any, Dict, List


def _k(value: Any) -> str:
    return str(value or "").strip().lower()


def build_term_index(a2_phase: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """
    Build index: term -> metrics (float)
    Best-effort: reads a2_phase.raw_full.profiles (preferred) else a2_phase.profiles (legacy).
    """
    raw_full = a2_phase.get("raw_full") or {}
    profiles = None
    if isinstance(raw_full, dict) and isinstance(raw_full.get("profiles"), list):
        profiles = raw_full.get("profiles")
    if profiles is None:
        profiles = a2_phase.get("profiles") or []
    if not isinstance(profiles, list):
        return {}

    idx: Dict[str, Dict[str, float]] = {}
    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        term = _k(profile.get("term") or profile.get("term_key"))
        if not term:
            continue
        idx[term] = {
            "manipulation_risk": (
                float(profile.get("manipulation_risk_mean"))
                if profile.get("manipulation_risk_mean") is not None
                else (
                    float(profile.get("manipulation_risk"))
                    if profile.get("manipulation_risk") is not None
                    else None
                )
            ),
            "attribution_strength": (
                float(profile.get("attribution_strength_uplifted"))
                if profile.get("attribution_strength_uplifted") is not None
                else (
                    float(profile.get("attribution_strength"))
                    if profile.get("attribution_strength") is not None
                    else None
                )
            ),
            "source_diversity": (
                float(profile.get("source_diversity_uplifted"))
                if profile.get("source_diversity_uplifted") is not None
                else (
                    float(profile.get("source_diversity"))
                    if profile.get("source_diversity") is not None
                    else None
                )
            ),
            "consensus_gap": (
                float(profile.get("consensus_gap_term"))
                if profile.get("consensus_gap_term") is not None
                else (
                    float(profile.get("consensus_gap"))
                    if profile.get("consensus_gap") is not None
                    else None
                )
            ),
        }
    return idx


def reduce_weighted_metrics(
    terms: List[str],
    idx: Dict[str, Dict[str, float]],
) -> Dict[str, float]:
    """
    v0.1 weighting:
      - default equal weights across matched terms
      - for risk: mean
      - for attribution/diversity: mean
      - for consensus_gap: mean
    If no terms match, return zeros.
    """
    matched: List[Dict[str, float]] = []
    for term in terms:
        key = _k(term)
        if key in idx:
            matched.append(idx[key])
    if not matched:
        return {
            "manipulation_risk_mean": 0.0,
            "attribution_strength_mean": 0.0,
            "source_diversity_mean": 0.0,
            "consensus_gap_mean": 0.0,
            "matched_terms": 0.0,
        }

    def _mean_or_zero(values: List[float]) -> float:
        return float(sum(values) / float(len(values))) if values else 0.0

    risks = [m["manipulation_risk"] for m in matched if m.get("manipulation_risk") is not None]
    attrs = [m["attribution_strength"] for m in matched if m.get("attribution_strength") is not None]
    diversity = [m["source_diversity"] for m in matched if m.get("source_diversity") is not None]
    gaps = [m["consensus_gap"] for m in matched if m.get("consensus_gap") is not None]
    return {
        "manipulation_risk_mean": _mean_or_zero(risks),
        "attribution_strength_mean": _mean_or_zero(attrs),
        "source_diversity_mean": _mean_or_zero(diversity),
        "consensus_gap_mean": _mean_or_zero(gaps),
        "manipulation_risk_count": float(len(risks)),
        "attribution_strength_count": float(len(attrs)),
        "source_diversity_count": float(len(diversity)),
        "consensus_gap_count": float(len(gaps)),
        "matched_terms": float(len(matched)),
    }
