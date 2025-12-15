# abraxas/linguistic/similarity.py
# Similarity metrics

from __future__ import annotations
from typing import List
import math
import hashlib

from .phonetics import phonetic_key
from .tokenize import tokens

def levenshtein(a: str, b: str) -> int:
    """Compute Levenshtein edit distance."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    # DP, O(len(a)*len(b)), deterministic
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            ins = cur[j-1] + 1
            dele = prev[j] + 1
            sub = prev[j-1] + (0 if ca == cb else 1)
            cur.append(min(ins, dele, sub))
        prev = cur
    return prev[-1]

def normalized_edit_similarity(a: str, b: str) -> float:
    """Normalized edit similarity (1.0 = identical)."""
    if not a and not b:
        return 1.0
    dist = levenshtein(a.lower(), b.lower())
    denom = max(len(a), len(b), 1)
    return round(1.0 - (dist / denom), 6)

def phonetic_similarity(a: str, b: str) -> float:
    """
    Stable phonetic similarity: compare phonetic keys + fallback to edit similarity.
    """
    ka = phonetic_key(a)
    kb = phonetic_key(b)
    if ka and kb and ka == kb:
        return 1.0
    if ka and kb:
        # Compare keys by edit similarity
        return max(0.0, normalized_edit_similarity(ka, kb))
    # Fallback
    return max(0.0, normalized_edit_similarity(a, b))

def _stable_hash_int(s: str) -> int:
    """Deterministic hash across runs."""
    h = hashlib.sha256(s.encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big", signed=False)

def hashed_bow_vector(text: str, dims: int = 256) -> List[float]:
    """
    Deterministic hashed bag-of-words vector (no ML deps).
    """
    vec = [0.0] * dims
    for t in tokens(text):
        idx = _stable_hash_int(t) % dims
        vec[idx] += 1.0
    # L2 normalize
    norm = math.sqrt(sum(v*v for v in vec)) or 1.0
    return [v / norm for v in vec]

def cosine(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two vectors."""
    if len(a) != len(b) or not a:
        return 0.0
    return round(sum(x*y for x, y in zip(a, b)), 6)

def intent_preservation_score(context_a: str, context_b: str, dims: int = 256) -> float:
    """
    Approx intent preservation: cosine similarity between context vectors.
    This is deterministic and "good enough" until you swap in embeddings.
    """
    va = hashed_bow_vector(context_a, dims=dims)
    vb = hashed_bow_vector(context_b, dims=dims)
    return cosine(va, vb)
