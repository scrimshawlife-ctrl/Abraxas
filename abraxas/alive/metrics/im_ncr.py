# abraxas/alive/metrics/im_ncr.py
"""
IM.NCR v0.1 — Narrative Compression Ratio

Measures structural compression: the degree to which complex reality
is collapsed into a single simple frame.

NCR rises when the text:
- uses universal quantifiers ("always", "everyone", "nothing but")
- signals single-cause framing ("because of X" repeated, "it's all X")
- uses totalizing frames ("the real reason", "the only explanation")
- reduces complexity via binary moral sorting ("good vs evil", "us vs them")

v0.1 is a cue-based estimator. Later we can refine with parsing/semantic clustering.
"""

from __future__ import annotations
from typing import Dict, Any, List
import re

CAP = 18  # saturation cap for cue hits

CUE_FAMILIES = {
    # universal / totalizing language
    "UNIVERSAL": [
        r"\balways\b",
        r"\bnever\b",
        r"\beveryone\b",
        r"\bno one\b",
        r"\ball\b",
        r"\bnothing\b",
        r"\bonly\b",
        r"\bentire\b",
        r"\bcompletely\b",
        r"\btotal\b",
        r"\bmust\b",
    ],
    # single-cause / monocausal framing
    "MONOCAUSE": [
        r"\bit'?s all\b",
        r"\bthe real reason\b",
        r"\bthe only reason\b",
        r"\bnothing but\b",
        r"\bbecause of\b",
        r"\bdue to\b",
        r"\bas a result of\b",
    ],
    # binary moral sorting / reduction
    "BINARY": [
        r"\bus vs them\b",
        r"\bgood (?:and|vs)\s+evil\b",
        r"\bpatriot\b",
        r"\btraitor\b",
        r"\benemy\b",
        r"\bparasite\b",
        r"\bdegenerate\b",
        r"\bpure\b",
        r"\bcorrupt\b",
    ],
    # certainty boosters / closure language
    "CERTAINTY": [
        r"\bobviously\b",
        r"\bclearly\b",
        r"\bundeniable\b",
        r"\bno doubt\b",
        r"\bprove\b",
        r"\bfact is\b",
        r"\btruth is\b",
    ],
}

WEIGHTS = {
    "UNIVERSAL": 0.30,
    "MONOCAUSE": 0.40,
    "BINARY": 0.20,
    "CERTAINTY": 0.10,
}


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp value to [lo, hi] range."""
    return max(lo, min(hi, x))


def _count_matches(text: str, patterns: List[str]) -> int:
    """Count total matches across all patterns."""
    n = 0
    for pat in patterns:
        n += len(re.findall(pat, text, re.IGNORECASE))
    return n


def _normalize_count(count: int, cap: int = CAP) -> float:
    """Normalize count to [0, 1] with saturation at cap."""
    return min(count, cap) / float(cap)


def compute_im_ncr(text: str) -> Dict[str, Any]:
    """
    Compute IM.NCR (Narrative Compression Ratio).

    Args:
        text: Input text to analyze

    Returns:
        Metric dict with value, confidence, evidence, components
    """
    t = (text or "").lower()

    counts: Dict[str, int] = {}
    norms: Dict[str, float] = {}
    cues_used: List[str] = []

    # Count matches for each cue family
    for fam, pats in CUE_FAMILIES.items():
        c = _count_matches(t, pats)
        counts[fam] = c
        norms[fam] = _normalize_count(c)
        if c > 0:
            # Store matched family name as lightweight evidence cue
            cues_used.append(fam)

    # Compute weighted value
    value = 0.0
    for fam, w in WEIGHTS.items():
        value += w * norms.get(fam, 0.0)

    # Epistemic confidence: rises if multiple families present
    fams_present = sum(1 for fam in CUE_FAMILIES.keys() if counts.get(fam, 0) > 0)
    conf = 0.35
    if fams_present >= 2:
        conf += 0.10
    if fams_present >= 3:
        conf += 0.10
    # Short texts are less reliable
    if len(t) < 400:
        conf -= 0.10
    conf = _clamp(conf)

    return {
        "metric_id": "IM.NCR",
        "axis": "influence",
        "name": "Narrative Compression Ratio",
        "value": _clamp(value),
        "confidence": conf,
        "status": "shadow",
        "version": "0.1.0",
        "evidence": {"cues": cues_used},
        "explanation": {
            "operational_definition": "Cue-based estimate of totalizing/monocausal/binary/certainty framing that reduces causal plurality.",
            "failure_modes": [
                "Brevity can mimic compression.",
                "Satire/slogans inflate cues.",
                "Technical summaries can be compressed without manipulation intent.",
            ],
        },
        "components": {"counts": counts, "norms": norms, "weights": WEIGHTS},
    }
