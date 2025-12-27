from __future__ import annotations

import re
from typing import Dict, List, Set


TOKEN = re.compile(r"[a-z0-9]{3,}")


def _tokens(text: str) -> Set[str]:
    return set(match.group(0) for match in TOKEN.finditer((text or "").lower()))


def build_term_token_index(terms: List[str]) -> Dict[str, Set[str]]:
    """
    term -> tokens(term)
    """
    idx: Dict[str, Set[str]] = {}
    for term in terms:
        value = str(term or "").strip()
        if not value:
            continue
        idx[value.lower()] = _tokens(value)
    return idx


def assign_claim_to_terms(
    claim: str,
    term_tok_idx: Dict[str, Set[str]],
    *,
    min_overlap: int = 1,
    max_terms: int = 5,
) -> List[str]:
    """
    Deterministic assignment: rank terms by token overlap with claim.
    """
    ct = _tokens(claim)
    scored = []
    for term, tokens in term_tok_idx.items():
        overlap = len(ct & tokens)
        if overlap >= int(min_overlap):
            scored.append((overlap, term))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [term for _, term in scored[: int(max_terms)]]
