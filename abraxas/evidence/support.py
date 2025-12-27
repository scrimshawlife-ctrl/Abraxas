from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


_WORD = re.compile(r"[a-z0-9']+")


def _tokens(s: str) -> set[str]:
    s = (s or "").lower()
    return set(_WORD.findall(s))


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return float(inter) / float(union) if union else 0.0


def support_weight_for_claim(
    *,
    term: str,
    claim_text: str,
    evidence_by_term: Dict[str, List[Dict[str, Any]]],
    max_bonus: float = 0.35,
) -> Tuple[float, Dict[str, Any]]:
    """
    Deterministic, bounded weight bonus based on overlap with evidence bundle claim texts.
    Returns (bonus, debug).
    """
    tk = (term or "").strip().lower()
    ev = evidence_by_term.get(tk) or []
    ct = _tokens(claim_text)
    best = 0.0
    best_id = None
    best_src = None
    best_cred = 0.5

    for b in ev:
        bid = str(b.get("bundle_id") or "")
        cred = float(b.get("credence") or 0.5)
        if cred < 0.0:
            cred = 0.0
        if cred > 1.0:
            cred = 1.0
        claims = b.get("claims") if isinstance(b.get("claims"), list) else []
        for c in claims:
            if not isinstance(c, dict):
                continue
            etxt = str(c.get("text") or "")
            sim = jaccard(ct, _tokens(etxt))
            score = sim * (0.6 + 0.4 * cred)
            if score > best:
                best = score
                best_id = bid
                best_src = str(b.get("source_ref") or "")
                best_cred = cred

    if best < 0.08:
        bonus = 0.0
    elif best < 0.18:
        bonus = 0.10 * max_bonus
    elif best < 0.30:
        bonus = 0.35 * max_bonus
    else:
        bonus = 1.00 * max_bonus

    return float(bonus), {
        "best_overlap_score": float(best),
        "best_bundle_id": best_id,
        "best_bundle_credence": float(best_cred),
        "best_source_ref": best_src,
    }
