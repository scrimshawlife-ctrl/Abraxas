from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict


@dataclass(frozen=True)
class CostBreakdown:
    sources: int
    claims: int
    clusters: int
    terms: int
    predictions: int
    base_credits: int
    total_credits: int

    def to_dict(self) -> Dict:
        return asdict(self)


W_SOURCE = 1
W_CLAIM = 1
W_CLUSTER = 3
W_TERM = 2
W_PRED = 1
BASE = 5


def compute_cost(
    *,
    n_sources: int,
    n_claims: int,
    n_clusters: int,
    n_terms: int,
    n_predictions: int,
) -> CostBreakdown:
    subtotal = (
        W_SOURCE * n_sources
        + W_CLAIM * n_claims
        + W_CLUSTER * n_clusters
        + W_TERM * n_terms
        + W_PRED * n_predictions
    )
    total = max(BASE, subtotal)
    return CostBreakdown(
        sources=int(n_sources),
        claims=int(n_claims),
        clusters=int(n_clusters),
        terms=int(n_terms),
        predictions=int(n_predictions),
        base_credits=BASE,
        total_credits=int(total),
    )
