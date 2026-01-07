"""Rune adapter for memetic capabilities.

Thin adapter layer exposing abraxas.memetic.* modules via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from abraxas.core.provenance import canonical_envelope
from abraxas.memetic.claims_sources import load_sources_from_osh as load_sources_from_osh_core
from abraxas.memetic.claim_extract import extract_claim_items_from_sources as extract_claim_items_core
from abraxas.memetic.claim_cluster import cluster_claims as cluster_claims_core
from abraxas.memetic.dmx_context import load_dmx_context as load_dmx_context_core
from abraxas.memetic.term_index import build_term_index as build_term_index_core
from abraxas.memetic.term_index import reduce_weighted_metrics as reduce_weighted_metrics_core
from abraxas.memetic.term_assign import build_term_token_index as build_term_token_index_core
from abraxas.memetic.term_assign import assign_claim_to_terms as assign_claim_to_terms_core


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
    Rune-compatible claim item extractor.

    Wraps existing extract_claim_items_from_sources with provenance envelope.
    Extracts claim sentences from source documents.

    Args:
        sources: List of source documents (from load_sources_from_osh)
        run_id: Run identifier for provenance tracking
        max_per_source: Maximum claim sentences to extract per source (default: 5)
        seed: Optional deterministic seed (unused for extraction, kept for consistency)

    Returns:
        Dictionary with items list, provenance, and not_computable (always None)
    """
    # Call existing extract_claim_items_from_sources function (no changes to core logic)
    items = extract_claim_items_core(
        sources,
        run_id=run_id,
        max_per_source=max_per_source
    )

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"items": items},
        config={"max_per_source": max_per_source},
        inputs={"sources": sources, "run_id": run_id},
        operation_id="memetic.claim_extract.extract",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "items": items,
        "provenance": envelope["provenance"],
        "not_computable": None  # extraction never fails, returns empty list on error
    }


def cluster_claims_deterministic(
    items: List[Dict[str, Any]],
    sim_threshold: float = 0.42,
    max_pairs: int = 250000,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible claim clusterer.

    Wraps existing cluster_claims with provenance envelope.
    Clusters similar claim sentences using token Jaccard similarity.

    Args:
        items: List of claim items (from extract_claim_items_from_sources)
        sim_threshold: Similarity threshold for clustering (default: 0.42)
        max_pairs: Maximum pairwise comparisons to perform (default: 250000)
        seed: Optional deterministic seed (unused for clustering, kept for consistency)

    Returns:
        Dictionary with clusters list, metrics dict, provenance, and not_computable (always None)
    """
    # Call existing cluster_claims function (no changes to core logic)
    clusters, metrics = cluster_claims_core(
        items,
        sim_threshold=sim_threshold,
        max_pairs=max_pairs
    )

    # Convert metrics to dict
    metrics_dict = metrics.to_dict()

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"clusters": clusters, "metrics": metrics_dict},
        config={"sim_threshold": sim_threshold, "max_pairs": max_pairs},
        inputs={"items": items},
        operation_id="memetic.claim_cluster.cluster",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "clusters": clusters,
        "metrics": metrics_dict,
        "provenance": envelope["provenance"],
        "not_computable": None  # clustering never fails, returns empty clusters on error
    }


def load_dmx_context_deterministic(
    mwr_path: str,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible DMX context loader.

    Wraps existing load_dmx_context with provenance envelope.
    Loads DMX (Disinformation/Misinformation) context from MWR artifact.

    Args:
        mwr_path: Path to MWR (Memetic Weather Report) artifact JSON file
        seed: Optional deterministic seed (unused for loading, kept for consistency)

    Returns:
        Dictionary with dmx_context dict, provenance, and not_computable (always None)
    """
    # Call existing load_dmx_context function (no changes to core logic)
    dmx_context = load_dmx_context_core(mwr_path)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"dmx_context": dmx_context},
        config={},
        inputs={"mwr_path": mwr_path},
        operation_id="memetic.dmx_context.load",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "dmx_context": dmx_context,
        "provenance": envelope["provenance"],
        "not_computable": None  # DMX loading never fails, returns default LOW bucket on error
    }


def build_term_index_deterministic(
    a2_phase: Dict[str, Any],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible term index builder.

    Wraps existing build_term_index with provenance envelope.
    Builds term → metrics index from A2 phase artifact.

    Args:
        a2_phase: A2 phase artifact dict with profiles
        seed: Optional deterministic seed (unused for indexing, kept for consistency)

    Returns:
        Dictionary with term_index dict, provenance, and not_computable (always None)
    """
    # Call existing build_term_index function (no changes to core logic)
    term_index = build_term_index_core(a2_phase)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"term_index": term_index},
        config={},
        inputs={"a2_phase": a2_phase},
        operation_id="memetic.term_index.build",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "term_index": term_index,
        "provenance": envelope["provenance"],
        "not_computable": None  # index building never fails, returns empty dict on error
    }


def reduce_weighted_metrics_deterministic(
    terms: List[str],
    term_index: Dict[str, Dict[str, float]],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible weighted metrics reducer.

    Wraps existing reduce_weighted_metrics with provenance envelope.
    Aggregates metrics across terms using term index.

    Args:
        terms: List of term strings to aggregate metrics for
        term_index: Term → metrics index (from build_term_index)
        seed: Optional deterministic seed (unused for reduction, kept for consistency)

    Returns:
        Dictionary with weighted_metrics dict, provenance, and not_computable (always None)
    """
    # Call existing reduce_weighted_metrics function (no changes to core logic)
    weighted_metrics = reduce_weighted_metrics_core(terms, term_index)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"weighted_metrics": weighted_metrics},
        config={},
        inputs={"terms": terms, "term_index": term_index},
        operation_id="memetic.term_index.reduce",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "weighted_metrics": weighted_metrics,
        "provenance": envelope["provenance"],
        "not_computable": None  # metric reduction never fails, returns zeros if no matches
    }


def build_term_token_index_deterministic(
    terms: List[str],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible term token index builder.

    Wraps existing build_term_token_index with provenance envelope.
    Builds term → token set index for claim assignment.

    Args:
        terms: List of term strings to tokenize and index
        seed: Optional deterministic seed (unused for indexing, kept for consistency)

    Returns:
        Dictionary with term_token_index dict, provenance, and not_computable (always None)
    """
    # Call existing build_term_token_index function (returns dict[str, set[str]])
    term_token_index_sets = build_term_token_index_core(terms)

    # Convert sets to sorted lists for JSON serialization
    term_token_index = {
        term: sorted(list(tokens)) for term, tokens in term_token_index_sets.items()
    }

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"term_token_index": term_token_index},
        config={},
        inputs={"terms": terms},
        operation_id="memetic.term_assign.build_index",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "term_token_index": term_token_index,
        "provenance": envelope["provenance"],
        "not_computable": None  # index building never fails, returns empty dict on error
    }


def assign_claim_to_terms_deterministic(
    claim: str,
    term_token_index: Dict[str, List[str]],
    min_overlap: int = 1,
    max_terms: int = 5,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible claim→term assigner.

    Wraps existing assign_claim_to_terms with provenance envelope.
    Assigns claim to terms via token overlap ranking.

    Args:
        claim: Claim text to assign to terms
        term_token_index: Term → token list index (from build_term_token_index)
        min_overlap: Minimum token overlap required (default: 1)
        max_terms: Maximum terms to return (default: 5)
        seed: Optional deterministic seed (unused for assignment, kept for consistency)

    Returns:
        Dictionary with assigned_terms list, provenance, and not_computable (always None)
    """
    # Convert lists back to sets for core function
    term_token_index_sets = {
        term: set(tokens) for term, tokens in term_token_index.items()
    }

    # Call existing assign_claim_to_terms function
    assigned_terms = assign_claim_to_terms_core(
        claim,
        term_token_index_sets,
        min_overlap=min_overlap,
        max_terms=max_terms
    )

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"assigned_terms": assigned_terms},
        config={"min_overlap": min_overlap, "max_terms": max_terms},
        inputs={"claim": claim, "term_token_index": term_token_index},
        operation_id="memetic.term_assign.assign",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "assigned_terms": assigned_terms,
        "provenance": envelope["provenance"],
        "not_computable": None  # term assignment never fails, returns empty list on error
    }


__all__ = [
    "load_sources_from_osh_deterministic",
    "extract_claim_items_deterministic",
    "cluster_claims_deterministic",
    "load_dmx_context_deterministic",
    "build_term_index_deterministic",
    "reduce_weighted_metrics_deterministic",
    "build_term_token_index_deterministic",
    "assign_claim_to_terms_deterministic"
]
