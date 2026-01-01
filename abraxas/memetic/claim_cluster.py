from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


TOKEN = re.compile(r"[a-z0-9]{3,}")
STOP = {
    "this",
    "that",
    "with",
    "from",
    "they",
    "them",
    "were",
    "been",
    "have",
    "has",
    "had",
    "into",
    "over",
    "under",
    "about",
    "after",
    "before",
    "when",
    "what",
    "where",
    "which",
    "while",
    "will",
    "would",
    "could",
    "should",
    "also",
    "more",
    "most",
    "some",
    "many",
    "much",
    "very",
    "just",
    "than",
    "then",
    "there",
    "here",
    "your",
    "you",
}


def _tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for match in TOKEN.finditer((text or "").lower()):
        token = match.group(0)
        if token in STOP:
            continue
        tokens.add(token)
    return tokens


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return float(inter) / float(union) if union else 0.0


class DSU:
    def __init__(self, n: int) -> None:
        self.p = list(range(n))
        self.r = [0] * n

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.r[ra] < self.r[rb]:
            self.p[ra] = rb
        elif self.r[ra] > self.r[rb]:
            self.p[rb] = ra
        else:
            self.p[rb] = ra
            self.r[ra] += 1


@dataclass(frozen=True)
class ClusterMetrics:
    n_items: int
    n_clusters: int
    dominance: float
    contradiction_rate: float
    consensus_gap: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_items": self.n_items,
            "n_clusters": self.n_clusters,
            "dominance": self.dominance,
            "contradiction_rate": self.contradiction_rate,
            "consensus_gap": self.consensus_gap,
        }


def cluster_claims(
    items: List[Dict[str, Any]],
    *,
    sim_threshold: float = 0.42,
    max_pairs: int = 250000,
) -> Tuple[List[List[int]], ClusterMetrics]:
    """
    Greedy O(n^2) with a safety cap on comparisons.
    v0.1: token Jaccard threshold; union-find merges.
    """
    n = len(items)
    tokens = [_tokens(str(it.get("claim") or "")) for it in items]
    dsu = DSU(n)

    pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            pairs += 1
            if pairs > max_pairs:
                break
            if jaccard(tokens[i], tokens[j]) >= sim_threshold:
                dsu.union(i, j)
        if pairs > max_pairs:
            break

    buckets: Dict[int, List[int]] = {}
    for i in range(n):
        root = dsu.find(i)
        buckets.setdefault(root, []).append(i)
    clusters = sorted(buckets.values(), key=lambda c: (-len(c), c[0] if c else 0))

    dominance = float(len(clusters[0])) / float(n) if clusters and n else 0.0

    neg = {"not", "no", "never", "fake", "false", "hoax", "debunk"}
    neg_flags = []
    for it in items:
        toks = _tokens(str(it.get("claim") or ""))
        neg_flags.append(1 if (toks & neg) else 0)
    contradiction_rate = float(sum(neg_flags)) / float(n) if n else 0.0

    frag = 0.0
    if n:
        frag = min(1.0, float(len(clusters) - 1) / float(max(1, min(n, 25) - 1)))
    consensus_gap = max(
        0.0, min(1.0, 0.60 * frag + 0.25 * (1.0 - dominance) + 0.15 * contradiction_rate)
    )

    metrics = ClusterMetrics(
        n_items=n,
        n_clusters=len(clusters),
        dominance=float(dominance),
        contradiction_rate=float(contradiction_rate),
        consensus_gap=float(consensus_gap),
    )
    return clusters, metrics
