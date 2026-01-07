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
from abraxas.memetic.dmx import compute_dmx as compute_dmx_core
from abraxas.memetic.dmx_context import load_dmx_context as load_dmx_context_core
from abraxas.memetic.extract import (
    build_mimetic_weather as build_mimetic_weather_core,
    extract_terms as extract_terms_core,
    read_oracle_texts as read_oracle_texts_core,
)
from abraxas.memetic.types import TermCandidate


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
    "read_oracle_texts_deterministic",
    "extract_terms_deterministic",
    "build_mimetic_weather_deterministic",
    "compute_dmx_deterministic",
    "load_dmx_context_deterministic",
]


def read_oracle_texts_deterministic(
    path: str,
    max_items: int = 200,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    docs = read_oracle_texts_core(path, max_items=int(max_items))
    docs_payload = [{"ts": ts, "text": text} for ts, text in docs]

    envelope = canonical_envelope(
        result={"docs": docs_payload},
        config={},
        inputs={"path": path, "max_items": int(max_items)},
        operation_id="memetic.oracle_texts.read",
        seed=seed,
    )

    return {
        "docs": docs_payload,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"],
    }


def extract_terms_deterministic(
    docs: List[Dict[str, Any]],
    max_terms: int = 60,
    n_values: Optional[List[int]] = None,
    baseline_counts: Optional[Dict[str, int]] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    normalized_docs = []
    for doc in docs or []:
        if not isinstance(doc, dict):
            continue
        ts = str(doc.get("ts") or "")
        text = str(doc.get("text") or "")
        normalized_docs.append((ts, text))

    terms = extract_terms_core(
        normalized_docs,
        n_values=n_values,
        max_terms=int(max_terms),
        baseline_counts=baseline_counts,
    )
    terms_payload = [term.to_dict() for term in terms]

    envelope = canonical_envelope(
        result={"terms": terms_payload},
        config={},
        inputs={
            "docs": docs,
            "max_terms": int(max_terms),
            "n_values": n_values,
            "baseline_counts": baseline_counts,
        },
        operation_id="memetic.terms.extract",
        seed=seed,
    )

    return {
        "terms": terms_payload,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"],
    }


def build_mimetic_weather_deterministic(
    run_id: str,
    terms: List[Dict[str, Any]],
    ts: Optional[str] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    normalized_terms: List[TermCandidate] = []
    required_fields = {
        "term_id",
        "term",
        "n",
        "count",
        "first_seen_ts",
        "last_seen_ts",
        "velocity_per_day",
        "half_life_est_s",
        "novelty_score",
        "propagation_score",
        "manipulation_risk",
        "tags",
        "provenance",
    }
    for term in terms or []:
        if not isinstance(term, dict):
            continue
        if not required_fields.issubset(term.keys()):
            continue
        normalized_terms.append(TermCandidate(**{k: term[k] for k in required_fields}))

    units = build_mimetic_weather_core(run_id, normalized_terms, ts=ts)
    units_payload = [unit.to_dict() for unit in units]

    envelope = canonical_envelope(
        result={"units": units_payload},
        config={},
        inputs={"run_id": run_id, "terms": terms, "ts": ts},
        operation_id="memetic.weather.build",
        seed=seed,
    )

    return {
        "units": units_payload,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"],
    }


def compute_dmx_deterministic(
    sources: Optional[List[Dict[str, Any]]] = None,
    signals: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    dmx = compute_dmx_core(sources=sources, signals=signals)
    dmx_payload = dmx.to_dict()

    envelope = canonical_envelope(
        result={"dmx": dmx_payload},
        config={},
        inputs={"sources": sources, "signals": signals},
        operation_id="memetic.dmx.compute",
        seed=seed,
    )

    return {
        "dmx": dmx_payload,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"],
    }


def load_dmx_context_deterministic(
    mwr_path: str,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    dmx_context = load_dmx_context_core(mwr_path)

    envelope = canonical_envelope(
        result={"dmx_context": dmx_context},
        config={},
        inputs={"mwr_path": mwr_path},
        operation_id="memetic.dmx_context.load",
        seed=seed,
    )

    return {
        "dmx_context": dmx_context,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"],
    }
