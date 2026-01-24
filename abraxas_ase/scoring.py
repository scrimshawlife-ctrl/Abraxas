from __future__ import annotations

import math
from collections import Counter


def letter_entropy(sorted_letters: str) -> float:
    """
    Shannon entropy over letters, normalized to [0,1] by dividing by log2(k) where k=26.
    Deterministic.
    """
    if not sorted_letters:
        return 0.0
    counts = Counter(sorted_letters)
    n = len(sorted_letters)
    h = 0.0
    for c in counts.values():
        p = c / n
        h -= p * math.log2(p)
    # normalize by max possible entropy with alphabet size 26
    return float(h / math.log2(26))


def token_anagram_potential(length: int, unique_letters: int) -> float:
    """
    TAP = (unique_letters / length) * log(length)
    log is natural log; deterministic.
    """
    if length <= 0:
        return 0.0
    return float((unique_letters / length) * math.log(length))


def stable_round(x: float, nd: int = 6) -> float:
    # stable rounding for JSON output
    return float(f"{x:.{nd}f}")
