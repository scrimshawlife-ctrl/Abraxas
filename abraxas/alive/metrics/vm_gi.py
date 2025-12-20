# abraxas/alive/metrics/vm_gi.py
"""
VM.GI v0.1 — Generativity Index

Measures degree of novelty production: capacity to generate new interpretations,
artifacts, forks, and internal debate versus rigid repetition and purity enforcement.

GI rises when the artifact contains:
- open-ended prompts ("try… experiment… explore…")
- multiple pathways ("options… alternatives… consider…")
- explicit tolerance for variation ("interpret… remix… adapt…")
- uncertainty embraced ("maybe… might… test…")
- artifact/output invitations ("write… build… make… draft…")

GI falls when it contains:
- chant/loop language ("repeat… share everywhere… slogan…")
- purity enforcement ("real ones… traitors… only…")
- absolute closure ("the only truth… no doubt…")
- obedience focus ("must follow… never question…")

v0.1 is cue-based but balanced (positive and negative signals).
"""

from __future__ import annotations
from typing import Dict, Any, List
import re

CAP_POS = 20
CAP_NEG = 20

POS_CUES = {
    "INQUIRY": [
        r"\bexplore\b",
        r"\bexperiment\b",
        r"\btry\b",
        r"\btest\b",
        r"\binvestigate\b",
        r"\bconsider\b",
        r"\bquestion\b",
        r"\bcurious\b",
    ],
    "MULTIPATH": [
        r"\balternatives?\b",
        r"\boptions?\b",
        r"\bmultiple\b",
        r"\bvarious\b",
        r"\bdepending on\b",
        r"\bit depends\b",
    ],
    "VARIATION": [
        r"\binterpret\b",
        r"\bremix\b",
        r"\badapt\b",
        r"\biterate\b",
        r"\bfork\b",
        r"\bvariants?\b",
    ],
    "CREATION": [
        r"\bwrite\b",
        r"\bbuild\b",
        r"\bmake\b",
        r"\bcreate\b",
        r"\bdesign\b",
        r"\bdraft\b",
        r"\bprototype\b",
    ],
    "UNCERTAINTY_OK": [
        r"\bmaybe\b",
        r"\bmight\b",
        r"\bperhaps\b",
        r"\bpossible\b",
        r"\bprobabl(y|e)\b",
    ],
}

NEG_CUES = {
    "CHANT": [
        r"\brepeat\b",
        r"\bshare everywhere\b",
        r"\bspread the word\b",
        r"\bchant\b",
        r"\bslogan\b",
    ],
    "PURITY": [
        r"\bonly\b",
        r"\breal ones\b",
        r"\btraitor\b",
        r"\bpurity\b",
        r"\bnever associate\b",
    ],
    "OBEDIENCE": [
        r"\bmust follow\b",
        r"\bdo not question\b",
        r"\bnever question\b",
        r"\bobey\b",
        r"\bsubmit\b",
    ],
    "CLOSURE": [
        r"\bthe only truth\b",
        r"\bundeniable\b",
        r"\bno doubt\b",
        r"\bsettled\b",
        r"\bfinal\b",
    ],
}

WEIGHTS_POS = {
    "INQUIRY": 0.25,
    "MULTIPATH": 0.20,
    "VARIATION": 0.20,
    "CREATION": 0.25,
    "UNCERTAINTY_OK": 0.10,
}

WEIGHTS_NEG = {
    "CHANT": 0.30,
    "PURITY": 0.30,
    "OBEDIENCE": 0.20,
    "CLOSURE": 0.20,
}


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp value to [lo, hi] range."""
    return max(lo, min(hi, x))


def _count(text: str, patterns: List[str]) -> int:
    """Count total matches across all patterns."""
    n = 0
    for pat in patterns:
        n += len(re.findall(pat, text, re.IGNORECASE))
    return n


def _norm(count: int, cap: int) -> float:
    """Normalize count to [0, 1] with saturation at cap."""
    return min(count, cap) / float(cap)


def compute_vm_gi(text: str) -> Dict[str, Any]:
    """
    Compute VM.GI (Generativity Index).

    Args:
        text: Input text to analyze

    Returns:
        Metric dict with value, confidence, evidence, components
    """
    t = (text or "").lower()

    # Positive generativity cues
    pos_counts = {}
    pos_norms = {}
    pos_used = []

    for fam, pats in POS_CUES.items():
        c = _count(t, pats)
        pos_counts[fam] = c
        pos_norms[fam] = _norm(c, CAP_POS)
        if c > 0:
            pos_used.append(fam)

    # Negative anti-generativity cues
    neg_counts = {}
    neg_norms = {}
    neg_used = []

    for fam, pats in NEG_CUES.items():
        c = _count(t, pats)
        neg_counts[fam] = c
        neg_norms[fam] = _norm(c, CAP_NEG)
        if c > 0:
            neg_used.append(fam)

    # Compute weighted scores
    pos = sum(WEIGHTS_POS[f] * pos_norms.get(f, 0.0) for f in WEIGHTS_POS)
    neg = sum(WEIGHTS_NEG[f] * neg_norms.get(f, 0.0) for f in WEIGHTS_NEG)

    # GI is "positive generativity" minus "closure/chant suppression"
    raw = pos - 0.85 * neg
    # Map to 0..1 with a gentle sigmoid-ish clamp
    value = _clamp(0.5 + raw)

    # Confidence calculation
    fams_pos = sum(1 for f in POS_CUES if pos_counts.get(f, 0) > 0)
    fams_neg = sum(1 for f in NEG_CUES if neg_counts.get(f, 0) > 0)

    conf = 0.35
    if fams_pos >= 2:
        conf += 0.10
    if fams_pos >= 3:
        conf += 0.10
    # Short texts are less reliable
    if len(t) < 400:
        conf -= 0.10
    # If strong negative presence, confidence that GI is suppressed increases
    if fams_neg >= 2:
        conf += 0.05
    conf = _clamp(conf)

    return {
        "metric_id": "VM.GI",
        "axis": "vitality",
        "name": "Generativity Index",
        "value": value,
        "confidence": conf,
        "status": "shadow",
        "version": "0.1.0",
        "evidence": {"cues": sorted(set(pos_used + neg_used))},
        "explanation": {
            "operational_definition": "Cue-based estimate of novelty production via inquiry/multipath/variation/creation tempered by chant/purity/obedience/closure.",
            "failure_modes": [
                "Poetic novelty may not be actionable.",
                "Recruitment phases can look generative before tightening.",
                "Domain-specific docs can inflate GI.",
            ],
        },
        "components": {
            "pos_counts": pos_counts,
            "neg_counts": neg_counts,
            "pos_norms": pos_norms,
            "neg_norms": neg_norms,
            "weights_pos": WEIGHTS_POS,
            "weights_neg": WEIGHTS_NEG,
        },
    }
