"""Rune adapter for memetic capabilities.

Thin adapter layer exposing abraxas.memetic.* modules via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.memetic.claim_cluster import cluster_claims as cluster_claims_core
from abraxas.memetic.claim_extract import (
    extract_claim_items_from_sources as extract_claim_items_from_sources_core,
)
from abraxas.memetic.claims_sources import load_sources_from_osh as load_sources_from_osh_core


def load_sources_from_osh_deterministic(
    osh_ledger_path: str,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible OSH source loader.

    Wraps existing load_sources_from_osh with provenance envelope.
    Loads source documents from Open Source Harvest (OSH) ledger.

    Args:
        osh_ledger_path: Path to OSH ledger JSONL file
        seed: Optional deterministic seed (unused for loading, kept for consistency)

    Returns:
        Dictionary with sources list, stats dict, provenance, and not_computable (always None)
    """
    # Call existing load_sources_from_osh function (no changes to core logic)
    sources, stats = load_sources_from_osh_core(osh_ledger_path)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"sources": sources, "stats": stats},
        config={},
        inputs={"osh_ledger_path": osh_ledger_path},
        operation_id="memetic.claims_sources.load",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "sources": sources,
        "stats": stats,
        "provenance": envelope["provenance"],
        "not_computable": None  # source loading never fails, returns empty list on error
    }


def extract_claim_items_deterministic(
    sources: List[Dict[str, Any]],
    run_id: str,
    max_per_source: int = 5,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible claims extraction.

    Wraps existing extract_claim_items_from_sources with provenance envelope.
    Extracts deterministic claim items from source documents.

    Args:
        sources: List of source documents (dicts with text fields)
        run_id: Run identifier for deterministic tag
        max_per_source: Max sentences per source
        seed: Optional deterministic seed (unused, kept for consistency)

    Returns:
        Dictionary with items list, provenance, and not_computable (always None)
    """
    normalized_sources = sources if isinstance(sources, list) else []
    items = extract_claim_items_from_sources_core(
        normalized_sources,
        run_id=run_id,
        max_per_source=int(max_per_source),
    )

    envelope = canonical_envelope(
        result={"items": items},
        config={},
        inputs={
            "sources": normalized_sources,
            "run_id": run_id,
            "max_per_source": int(max_per_source),
        },
        operation_id="memetic.claim_extract.items",
        seed=seed,
    )

    return {
        "items": items,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"],
    }


def cluster_claims_deterministic(
    items: List[Dict[str, Any]],
    sim_threshold: float = 0.42,
    max_pairs: int = 250000,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible claims clustering.

    Wraps existing cluster_claims with provenance envelope.
    Clusters claim items with deterministic Jaccard thresholding.

    Args:
        items: Claim items to cluster
        sim_threshold: Jaccard similarity threshold for clustering
        max_pairs: Safety cap on pairwise comparisons
        seed: Optional deterministic seed (unused, kept for consistency)

    Returns:
        Dictionary with clusters, metrics, provenance, and not_computable (always None)
    """
    normalized_items = items if isinstance(items, list) else []
    clusters, metrics = cluster_claims_core(
        normalized_items,
        sim_threshold=float(sim_threshold),
        max_pairs=int(max_pairs),
    )
    metrics_dict = metrics.to_dict()

    envelope = canonical_envelope(
        result={"clusters": clusters, "metrics": metrics_dict},
        config={},
        inputs={
            "items": normalized_items,
            "sim_threshold": float(sim_threshold),
            "max_pairs": int(max_pairs),
        },
        operation_id="memetic.claim_cluster.cluster",
        seed=seed,
    )

    return {
        "clusters": clusters,
        "metrics": metrics_dict,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"],
    }


__all__ = [
    "load_sources_from_osh_deterministic",
    "extract_claim_items_deterministic",
    "cluster_claims_deterministic",
]
