# abraxas/alive/metrics/im_rfc.py
"""
IM.RFC v0.1 — Reality Friction Coefficient

Measures whether a narrative collides with reality cleanly (falsifiable, testable)
or self-seals against disproof.

RFC rises when the text:
- uses measurement language (data, evidence, quantify)
- makes predictions or time-bound expectations
- includes test/verification language
- acknowledges uncertainty or conditionality

RFC falls when the text:
- includes immunity clauses ("anyone who disagrees")
- moves goalposts ("timeline changed", "any day now")
- frames itself as unfalsifiable
- discourages questioning or critics

v0.1 is a cue-based estimator.
"""

from __future__ import annotations
from typing import Dict, Any, List
import re

CAP = 20

CONTACT_CUES = {
    "MEASURE": [
        r"\bdata\b",
        r"\bevidence\b",
        r"\bmeasure\b",
        r"\bquantif(y|ying|ication)\b",
        r"\bmetrics?\b",
        r"\bstatistic(s|al)\b",
        r"\bexperiment\b",
    ],
    "TESTING": [
        r"\btest\b",
        r"\bfalsif(y|iable|ication)\b",
        r"\breplicat(e|ion)\b",
        r"\bverify\b",
        r"\bvalidate\b",
        r"\bcontrol group\b",
    ],
    "PREDICT": [
        r"\bif\b.+\bthen\b",
        r"\bwe expect\b",
        r"\bforecast\b",
        r"\bpredict\b",
        r"\bwithin \d+ (days|weeks|months|years)\b",
    ],
    "UNCERTAINTY": [
        r"\bmight\b",
        r"\bmaybe\b",
        r"\bdepends\b",
        r"\bprobabl(y|e)\b",
        r"\bconfidence\b",
        r"\buncertain\b",
    ],
}

SEALING_CUES = {
    "IMMUNITY": [
        r"\banyone who disagrees\b",
        r"\bthey are lying\b",
        r"\byou're brainwashed\b",
        r"\bthey don't want you to know\b",
        r"\bthe mainstream\b.*\blies\b",
    ],
    "GOALPOSTS": [
        r"\bsoon\b",
        r"\bany day now\b",
        r"\bthe timeline changed\b",
        r"\bdelayed\b",
        r"\bpostponed\b",
    ],
    "UNFALSIFIABLE": [
        r"\bno evidence\b.*\bis evidence\b",
        r"\beverything is a sign\b",
        r"\bthey can hide it\b",
        r"\bcan't be proven\b.*\bbut\b",
    ],
    "DISCOURAGE": [
        r"\bdo not question\b",
        r"\bnever question\b",
        r"\bignore critics\b",
        r"\bdon't listen\b",
        r"\bjust trust\b",
    ],
}

W_CONTACT = {"MEASURE": 0.35, "TESTING": 0.30, "PREDICT": 0.25, "UNCERTAINTY": 0.10}
W_SEAL = {"IMMUNITY": 0.40, "GOALPOSTS": 0.20, "UNFALSIFIABLE": 0.25, "DISCOURAGE": 0.15}


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp value to [lo, hi] range."""
    return max(lo, min(hi, x))


def _count(text: str, patterns: List[str]) -> int:
    """Count total matches across all patterns."""
    n = 0
    for pat in patterns:
        n += len(re.findall(pat, text))
    return n


def _norm(count: int, cap: int = CAP) -> float:
    """Normalize count to [0, 1] with saturation at cap."""
    return min(count, cap) / float(cap)


def compute_im_rfc(text: str) -> Dict[str, Any]:
    """
    Compute IM.RFC (Reality Friction Coefficient).

    Args:
        text: Input text to analyze

    Returns:
        Metric dict with value, confidence, evidence, components
    """
    t = (text or "").lower()

    c_counts: Dict[str, int] = {}
    c_norms: Dict[str, float] = {}
    c_used: List[str] = []
    for fam, pats in CONTACT_CUES.items():
        c = _count(t, pats)
        c_counts[fam] = c
        c_norms[fam] = _norm(c)
        if c > 0:
            c_used.append(fam)

    s_counts: Dict[str, int] = {}
    s_norms: Dict[str, float] = {}
    s_used: List[str] = []
    for fam, pats in SEALING_CUES.items():
        c = _count(t, pats)
        s_counts[fam] = c
        s_norms[fam] = _norm(c)
        if c > 0:
            s_used.append(fam)

    contact = sum(W_CONTACT[f] * c_norms.get(f, 0.0) for f in W_CONTACT)
    sealing = sum(W_SEAL[f] * s_norms.get(f, 0.0) for f in W_SEAL)

    # RFC v0.1 = contact - seal, mapped into 0..1
    raw = contact - sealing
    value = _clamp((raw + 1.0) / 2.0)

    # Confidence: needs enough text + at least one of (contact|sealing) families present
    fams_present = len(set(c_used + s_used))
    conf = 0.35
    if fams_present >= 2:
        conf += 0.10
    if fams_present >= 3:
        conf += 0.10
    if len(t) < 400:
        conf -= 0.10
    conf = _clamp(conf)

    cues_used = sorted(set(c_used + s_used))

    return {
        "metric_id": "IM.RFC",
        "axis": "influence",
        "name": "Reality Friction Coefficient",
        "value": value,
        "confidence": conf,
        "status": "shadow",
        "version": "0.1.0",
        "evidence": {"cues": cues_used},
        "explanation": {
            "operational_definition": "Cue-based estimate of reality-contact (test/measure/predict) minus self-sealing (immunity/goalposts/unfalsifiable/discourage-disproof).",
            "failure_modes": [
                "Genre matters: poetry/fiction/ethics are not empirical.",
                "Short texts may omit testing language without being self-sealing.",
                "Some contexts imply tests outside the text.",
            ],
        },
        "components": {
            "contact": {"counts": c_counts, "norms": c_norms, "weights": W_CONTACT},
            "sealing": {"counts": s_counts, "norms": s_norms, "weights": W_SEAL},
        },
    }
