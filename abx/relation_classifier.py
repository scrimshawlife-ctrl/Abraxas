from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class RelationResult:
    relation: str                 # SUPPORTS / CONTRADICTS / REFRAMES
    confidence: float             # 0..1
    rationale: Dict[str, float]   # fired features -> weights


_NEGATIONS = {
    "not", "no", "never", "none", "without", "hardly", "rarely", "n't",
    "debunked", "debunks", "debunk", "false", "hoax", "misleading",
    "incorrect", "untrue", "fabricated", "fake", "myth",
}

_SUPPORT_CUES = {
    "confirms", "confirmed", "evidence", "proves", "proof", "supports", "support",
    "shows", "shown", "reveals", "revealed", "found", "finds", "indicates",
    "report", "reported", "according", "data show", "study finds",
}

_CONTRA_CUES = {
    "denies", "denied", "refutes", "refuted", "contradicts", "contradict",
    "debunks", "debunked", "fact check", "fact-check", "false", "misleading",
    "hoax", "fake", "not true", "no evidence", "lacks evidence",
}

_HEDGE_CUES = {
    "alleged", "allegedly", "reportedly", "may", "might", "could",
    "unclear", "unconfirmed", "rumor", "rumour", "speculation", "suggests",
}

_REFRAME_CUES = {
    "context", "explainer", "analysis", "background", "timeline", "what we know",
    "primer", "breakdown", "overview", "why", "how",
}


def _norm(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _tokenize(s: str) -> List[str]:
    s = _norm(s)
    # keep simple alpha tokens + contractions
    toks = re.findall(r"[a-z0-9]+(?:'[a-z]+)?", s)
    return toks


def _contains_phrase(s: str, phrase: str) -> bool:
    return phrase in _norm(s)


def _window_has_negation(tokens: List[str], idx: int, w: int = 3) -> bool:
    lo = max(0, idx - w)
    hi = min(len(tokens), idx + w + 1)
    for t in tokens[lo:hi]:
        if t in _NEGATIONS:
            return True
    return False


def _score_lexicon(text: str, lex: set[str]) -> float:
    t = _norm(text)
    score = 0.0
    for k in lex:
        if k in t:
            # longer phrases count slightly more
            score += 1.0 + min(1.0, 0.02 * len(k))
    return score


def classify_relation(
    *,
    claim_text: str,
    anchor_title: str,
    anchor_snippet: str,
) -> RelationResult:
    """
    Deterministic stance guess.
    - Uses cues + negation patterns + hedging.
    - Conservative: uncertainty pushes toward REFRAMES.
    """
    ct = _norm(claim_text)
    at = _norm(anchor_title)
    sn = _norm(anchor_snippet)
    blob = f"{at} {sn}".strip()

    # base cue scores
    s_support = _score_lexicon(blob, _SUPPORT_CUES)
    s_contra = _score_lexicon(blob, _CONTRA_CUES)
    s_hedge = _score_lexicon(blob, _HEDGE_CUES)
    s_reframe = _score_lexicon(blob, _REFRAME_CUES)

    rationale: Dict[str, float] = {}
    if s_support: rationale["support_cues"] = float(s_support)
    if s_contra: rationale["contra_cues"] = float(s_contra)
    if s_hedge: rationale["hedge_cues"] = float(s_hedge)
    if s_reframe: rationale["reframe_cues"] = float(s_reframe)

    # Negation sensitivity: if a support cue appears near negation, flip some mass to contra.
    toks = _tokenize(blob)
    for i, tok in enumerate(toks):
        if tok in {"confirms", "confirmed", "proves", "proof", "supports", "reveals", "shows"}:
            if _window_has_negation(toks, i, w=3):
                rationale["support_negated"] = rationale.get("support_negated", 0.0) + 1.0
                s_support = max(0.0, s_support - 0.8)
                s_contra += 0.6

    # Claim keyword overlap (weak signal; helps when cues absent)
    claim_terms = set([t for t in _tokenize(ct) if len(t) >= 5])  # longer terms reduce noise
    blob_terms = set([t for t in toks if len(t) >= 5])
    overlap = len(claim_terms.intersection(blob_terms))
    if overlap:
        rationale["claim_overlap"] = float(overlap)
        s_support += 0.10 * overlap
        s_contra += 0.08 * overlap

    # Hedge reduces confidence in either direction; nudges to reframe.
    # Also: if both support and contra are high, that implies contested -> reframe.
    contested = (s_support >= 1.5 and s_contra >= 1.5)
    if contested:
        rationale["contested"] = 1.0
        s_reframe += 1.2

    # Decision
    # net scores
    net_support = s_support - 0.6 * s_hedge
    net_contra = s_contra - 0.6 * s_hedge
    net_reframe = s_reframe + 0.4 * s_hedge

    rationale["net_support"] = float(net_support)
    rationale["net_contra"] = float(net_contra)
    rationale["net_reframe"] = float(net_reframe)

    # conservative thresholds
    best = max(net_support, net_contra, net_reframe)
    if best <= 1.0:
        return RelationResult("REFRAMES", 0.40, rationale)

    # Choose label
    if best == net_reframe:
        conf = min(0.90, 0.55 + 0.10 * best)
        return RelationResult("REFRAMES", float(conf), rationale)
    if best == net_contra and (net_contra >= net_support + 0.5):
        conf = min(0.92, 0.55 + 0.10 * best)
        return RelationResult("CONTRADICTS", float(conf), rationale)
    if best == net_support and (net_support >= net_contra + 0.5):
        conf = min(0.92, 0.55 + 0.10 * best)
        return RelationResult("SUPPORTS", float(conf), rationale)

    # If close call, reframe
    return RelationResult("REFRAMES", 0.55, rationale)
