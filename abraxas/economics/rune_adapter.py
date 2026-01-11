"""Rune adapter for economics capabilities.

Thin adapter layer exposing economics.* modules via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.economics.costing import compute_cost as compute_cost_core


def compute_cost_deterministic(
    *,
    n_sources: int,
    n_claims: int,
    n_clusters: int,
    n_terms: int,
    n_predictions: int,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible cost breakdown calculator.

    Wraps existing compute_cost with provenance envelope.

    Args:
        n_sources: Number of sources
        n_claims: Number of claims
        n_clusters: Number of clusters
        n_terms: Number of terms
        n_predictions: Number of predictions
        seed: Optional deterministic seed (unused, kept for consistency)

    Returns:
        Dictionary with cost breakdown, provenance, and not_computable (always None)
    """
    breakdown = compute_cost_core(
        n_sources=int(n_sources),
        n_claims=int(n_claims),
        n_clusters=int(n_clusters),
        n_terms=int(n_terms),
        n_predictions=int(n_predictions),
    )
    breakdown_dict = breakdown.to_dict()

    envelope = canonical_envelope(
        result={"cost": breakdown_dict},
        config={},
        inputs={
            "n_sources": int(n_sources),
            "n_claims": int(n_claims),
            "n_clusters": int(n_clusters),
            "n_terms": int(n_terms),
            "n_predictions": int(n_predictions),
        },
        operation_id="economics.costing.compute",
        seed=seed,
    )

    return {
        "cost": breakdown_dict,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"],
    }


__all__ = ["compute_cost_deterministic"]
