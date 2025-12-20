"""
LL.LFC - Life-Logistics Friction Coefficient

Measures material enactment cost across 7 friction vectors:
- Time Load (TL)
- Cognitive Load (CL)
- Social Load (SL)
- Resource Load (RL)
- Compliance Load (CoL)
- Volatility Load (VL)
- Embodiment Load (EL)
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
import re

CAP = 12  # max matches per load before saturation

LOADS = ["TL", "CL", "SL", "RL", "CoL", "VL", "EL"]

CUE_FAMILIES: Dict[str, List[str]] = {
    "TL": [
        r"\bdaily\b",
        r"\bevery day\b",
        r"\bconstantly\b",
        r"\balways\b",
        r"24/7",
        r"\bmonitor\b",
        r"\bkeep watch\b",
        r"\bnever stop\b",
    ],
    "CL": [
        r"\bdecode\b",
        r"\bhidden\b",
        r"they don['']t want you to know",
        r"\bonly we understand\b",
        r"\breal truth\b",
    ],
    "SL": [
        r"\bcut (them|him|her) off\b",
        r"\btraitor\b",
        r"\benemy within\b",
        r"\bloyal\b",
        r"\breal ones\b",
        r"\bpurity\b",
        r"\bdisown\b",
        r"\bnever associate\b",
    ],
    "RL": [
        r"\bdonate\b",
        r"\bsupport us\b",
        r"\bbuy\b",
        r"\bsubscribe\b",
        r"\bmembership\b",
        r"\bfund\b",
        r"\bgear\b",
        r"\bsupplies\b",
    ],
    "CoL": [
        r"\bpolicy\b",
        r"\bprocedure\b",
        r"\bprotocol\b",
        r"\bcompliance\b",
        r"\breport\b",
        r"\bsubmit\b",
        r"\bforms?\b",
        r"\btraining\b",
        r"\bmeeting\b",
    ],
    "VL": [
        r"\bnow\b",
        r"\burgent\b",
        r"\bimmediately\b",
        r"before it['']s too late",
        r"\bcrisis\b",
        r"\blast chance\b",
        r"\bemergency\b",
    ],
    "EL": [
        r"\bfast\b",
        r"\btrain\b",
        r"\bdiscipline\b",
        r"\bmarch\b",
        r"\bsacrifice\b",
        r"\bsleep less\b",
        r"\bendure\b",
        r"\bdetox\b",
    ],
}


def _count_matches(text: str, patterns: List[str]) -> int:
    """Count total matches across all patterns."""
    n = 0
    for pat in patterns:
        n += len(re.findall(pat, text, re.IGNORECASE))
    return n


def _normalize_count(count: int, cap: int = CAP) -> float:
    """Normalize count to 0..1 with saturation at cap."""
    return min(count, cap) / float(cap)


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp value to range."""
    return max(lo, min(hi, x))


def _derive_weights_from_profile(profile: Optional[Dict[str, Any]]) -> Dict[str, float]:
    """
    Derive per-load weights from user profile.
    
    Low capacity → higher weight (more friction impact).
    """
    # Default equal weights
    if not profile:
        return {k: 1.0 / len(LOADS) for k in LOADS}

    cap = profile.get("capacity", {})
    pref = profile.get("preference", {})
    susc = profile.get("susceptibility", {})

    capacity_time = float(cap.get("time", 0.5))
    capacity_sleep = float(cap.get("sleep", 0.5))
    capacity_social = float(cap.get("social", 0.5))
    capacity_money = float(cap.get("money", 0.5))
    preference_structure = float(pref.get("structure", 0.5))
    susceptibility_volatility = float(susc.get("volatility", 0.5))

    w = {}
    w["TL"] = 0.10 + 0.15 * (1.0 - capacity_time)
    w["EL"] = 0.08 + 0.12 * (1.0 - capacity_sleep)
    w["SL"] = 0.10 + 0.15 * (1.0 - capacity_social)
    w["RL"] = 0.10 + 0.15 * (1.0 - capacity_money)
    w["CoL"] = 0.10 + 0.10 * (1.0 - preference_structure)
    w["VL"] = 0.10 + 0.15 * (susceptibility_volatility)

    # Give CL a base + let it absorb remainder
    w["CL"] = 0.12

    # Normalize to sum to 1
    s = sum(w.values())
    if s <= 0:
        return {k: 1.0 / len(LOADS) for k in LOADS}
    return {k: v / s for k, v in w.items()}


def compute_ll_lfc(text: str, profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Compute LL.LFC (Life-Logistics Friction Coefficient).
    
    Args:
        text: Artifact text content
        profile: User profile with capacity/susceptibility data
    
    Returns:
        Metric dict with value, confidence, evidence, components
    """
    t = (text or "").lower()

    loads: Dict[str, float] = {}
    counts: Dict[str, int] = {}
    cues: Dict[str, List[str]] = {}

    for k in LOADS:
        patterns = CUE_FAMILIES.get(k, [])
        c = _count_matches(t, patterns)
        counts[k] = c
        loads[k] = _normalize_count(c)
        # lightweight evidence cues
        cues[k] = [p for p in patterns if re.search(p, t, re.IGNORECASE)]

    # Weighted aggregation
    weights = _derive_weights_from_profile(profile)
    value = 0.0
    for k in LOADS:
        value += weights.get(k, 0.0) * loads.get(k, 0.0)

    # Confidence (epistemic)
    nonzero = sum(1 for k in LOADS if loads[k] > 0)
    peak = max(loads.values()) if loads else 0.0
    conf = 0.35
    if nonzero >= 3:
        conf += 0.10
    if peak >= 0.5:
        conf += 0.10
    conf = _clamp(conf)

    return {
        "metric_id": "LL.LFC",
        "axis": "life_logistics",
        "name": "Life-Logistics Friction Coefficient",
        "value": _clamp(value),
        "confidence": conf,
        "status": "shadow",
        "version": "0.1.0",
        "evidence": {
            "cues": sorted({c for k in LOADS for c in cues[k]}),
        },
        "explanation": {
            "operational_definition": "Weighted burden of enactment across time/cognitive/social/resource/compliance/volatility/embodiment loads.",
            "failure_modes": [
                "Satire can inflate volatility/compliance cues.",
                "Manuals can imply high compliance burden without frequent enactment.",
                "Voluntary high-discipline practices can resemble coercive load.",
            ],
        },
        "components": {
            "loads": loads,  # per-load normalized 0..1
            "counts": counts,  # raw match counts
            "weights": weights,  # profile-shaped weights
        },
    }
