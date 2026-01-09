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
from abraxas.memetic.metrics_reduce import reduce_provenance_means as reduce_provenance_means_core
from abraxas.memetic.term_consensus_map import load_term_consensus_map as load_term_consensus_map_core
from abraxas.memetic.temporal import build_temporal_profiles as build_temporal_profiles_core
from abraxas.memetic.dmx import compute_dmx as compute_dmx_core
from abraxas.memetic.extract import (
    read_oracle_texts as read_oracle_texts_core,
    extract_terms as extract_terms_core,
    build_mimetic_weather as build_mimetic_weather_core
)
from abraxas.memetic.registry import (
    append_a2_terms_to_registry as append_a2_terms_to_registry_core,
    compute_missed_terms as compute_missed_terms_core
)


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


def reduce_provenance_means_deterministic(
    profiles: List[Dict[str, Any]],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible provenance means calculator.

    Wraps existing reduce_provenance_means with provenance envelope.
    Extracts mean values from temporal profiles (attribution, diversity, consensus_gap, manipulation_risk).

    Args:
        profiles: List of temporal profile dictionaries
        seed: Optional deterministic seed

    Returns:
        Dictionary with means dict, provenance, and not_computable (always None)
    """
    # Call existing reduce_provenance_means function
    means = reduce_provenance_means_core(profiles)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"means": means},
        config={},
        inputs={"profiles": profiles},
        operation_id="memetic.metrics_reduce.reduce_provenance_means",
        seed=seed
    )

    return {
        "means": means,
        "provenance": envelope["provenance"],
        "not_computable": None  # mean computation never fails, returns 0.0 on empty input
    }


def load_term_consensus_map_deterministic(
    path: str,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible term consensus map loader.

    Wraps existing load_term_consensus_map with provenance envelope.
    Loads term(lowercase) → consensus_gap mapping from term_claims JSON file.

    Args:
        path: Path to term_claims_<run>.json file
        seed: Optional deterministic seed (unused for file I/O, kept for consistency)

    Returns:
        Dictionary with term_consensus_map dict, provenance, and not_computable (always None)
    """
    # Call existing load_term_consensus_map function
    term_consensus_map = load_term_consensus_map_core(path)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"term_consensus_map": term_consensus_map},
        config={},
        inputs={"path": path},
        operation_id="memetic.term_consensus_map.load",
        seed=seed
    )

    return {
        "term_consensus_map": term_consensus_map,
        "provenance": envelope["provenance"],
        "not_computable": None  # loading never fails, returns empty dict on error
    }


def build_temporal_profiles_deterministic(
    registry_path: str,
    now_iso: Optional[str] = None,
    max_terms: int = 2000,
    min_obs: int = 2,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible temporal profiles builder.

    Wraps existing build_temporal_profiles with provenance envelope.
    Builds temporal profiles from term registry with velocity, phase, and provenance metrics.

    Args:
        registry_path: Path to term registry JSONL file
        now_iso: Optional ISO timestamp override for 'now' (defaults to current UTC time)
        max_terms: Maximum number of terms to process (default: 2000)
        min_obs: Minimum observations required per term (default: 2)
        seed: Optional deterministic seed

    Returns:
        Dictionary with profiles list (as dicts), provenance, and not_computable (always None)
    """
    # Call existing build_temporal_profiles function (returns List[TermTemporalProfile])
    profile_objects = build_temporal_profiles_core(
        registry_path,
        now_iso=now_iso,
        max_terms=max_terms,
        min_obs=min_obs
    )

    # Convert to list of dicts (call .to_dict() on each profile object)
    profiles = [p.to_dict() for p in profile_objects]

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"profiles": profiles},
        config={"max_terms": max_terms, "min_obs": min_obs},
        inputs={"registry_path": registry_path, "now_iso": now_iso},
        operation_id="memetic.temporal.build_temporal_profiles",
        seed=seed
    )

    return {
        "profiles": profiles,
        "provenance": envelope["provenance"],
        "not_computable": None  # profile building never fails, returns empty list on error
    }


def compute_dmx_deterministic(
    sources: Optional[List[Dict[str, Any]]] = None,
    signals: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible DMX calculator.

    Wraps existing compute_dmx with provenance envelope.
    Computes Disinformation/Misinformation eXposure metrics from sources and signals.

    Args:
        sources: Optional list of source dicts with credibility/independence flags
        signals: Optional dict of extracted signal flags (ai_markers, bot_markers, etc.)
        seed: Optional deterministic seed (unused for DMX, kept for consistency)

    Returns:
        Dictionary with dmx dict, provenance, and not_computable (always None)
    """
    # Call existing compute_dmx function (returns DMX dataclass)
    dmx_obj = compute_dmx_core(sources=sources, signals=signals)

    # Convert dataclass to dict
    dmx = dmx_obj.to_dict()

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"dmx": dmx},
        config={},
        inputs={"sources": sources, "signals": signals},
        operation_id="memetic.dmx.compute",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "dmx": dmx,
        "provenance": envelope["provenance"],
        "not_computable": None  # DMX computation never fails, returns defaults on error
    }


def read_oracle_texts_deterministic(
    path: str,
    max_items: int = 200,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible oracle text reader.

    Wraps existing read_oracle_texts with provenance envelope.
    Reads oracle texts from file and returns as list of (timestamp, text) tuples.

    Args:
        path: Path to oracle texts file (JSON or JSONL)
        max_items: Maximum number of items to read (default: 200)
        seed: Optional deterministic seed (unused for reading, kept for consistency)

    Returns:
        Dictionary with documents list, provenance, and not_computable (always None)
    """
    # Call existing read_oracle_texts function (returns List[Tuple[str, str]])
    documents = read_oracle_texts_core(path, max_items=max_items)

    # Convert tuples to dicts for JSON serialization
    documents_dicts = [{"timestamp": ts, "text": txt} for ts, txt in documents]

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"documents": documents_dicts},
        config={"max_items": max_items},
        inputs={"path": path},
        operation_id="memetic.extract.read_oracle_texts",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "documents": documents_dicts,
        "provenance": envelope["provenance"],
        "not_computable": None  # reading never fails, returns empty list on error
    }


def extract_terms_deterministic(
    documents: List[Dict[str, str]],
    n_values: Optional[List[int]] = None,
    max_terms: int = 60,
    baseline_counts: Optional[Dict[str, int]] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible term extractor.

    Wraps existing extract_terms with provenance envelope.
    Extracts term candidates from documents with velocity and risk metrics.

    Args:
        documents: List of {timestamp, text} dicts
        n_values: N-gram sizes to extract (default: [1, 2, 3])
        max_terms: Maximum number of terms to return (default: 60)
        baseline_counts: Optional baseline term counts for novelty calculation
        seed: Optional deterministic seed (unused for extraction, kept for consistency)

    Returns:
        Dictionary with term_candidates list (dicts), provenance, and not_computable (always None)
    """
    # Convert documents from dicts back to tuples for core function
    docs_tuples = [(doc["timestamp"], doc["text"]) for doc in documents]

    # Call existing extract_terms function (returns List[TermCandidate])
    term_objs = extract_terms_core(
        docs=docs_tuples,
        n_values=n_values,
        max_terms=max_terms,
        baseline_counts=baseline_counts
    )

    # Convert dataclass objects to dicts
    term_candidates = [t.to_dict() for t in term_objs]

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"term_candidates": term_candidates},
        config={"n_values": n_values, "max_terms": max_terms},
        inputs={"documents": documents, "baseline_counts": baseline_counts},
        operation_id="memetic.extract.extract_terms",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "term_candidates": term_candidates,
        "provenance": envelope["provenance"],
        "not_computable": None  # extraction never fails, returns empty list on error
    }


def build_mimetic_weather_deterministic(
    run_id: str,
    term_candidates: List[Dict[str, Any]],
    ts: Optional[str] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible mimetic weather builder.

    Wraps existing build_mimetic_weather with provenance envelope.
    Builds weather units (fronts) from term candidates.

    Args:
        run_id: Run identifier for provenance tracking
        term_candidates: List of term candidate dicts (from extract_terms)
        ts: Optional timestamp override (ISO format)
        seed: Optional deterministic seed (unused for building, kept for consistency)

    Returns:
        Dictionary with weather_units list (dicts), provenance, and not_computable (always None)
    """
    # Convert term_candidates from dicts to TermCandidate objects
    from abraxas.memetic.types import TermCandidate
    term_objs = [TermCandidate(**tc) for tc in term_candidates]

    # Call existing build_mimetic_weather function (returns List[MimeticWeatherUnit])
    weather_objs = build_mimetic_weather_core(
        run_id=run_id,
        terms=term_objs,
        ts=ts
    )

    # Convert dataclass objects to dicts
    weather_units = [w.to_dict() for w in weather_objs]

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"weather_units": weather_units},
        config={},
        inputs={"run_id": run_id, "term_candidates": term_candidates, "ts": ts},
        operation_id="memetic.extract.build_mimetic_weather",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "weather_units": weather_units,
        "provenance": envelope["provenance"],
        "not_computable": None  # weather building never fails, returns empty list on error
    }


def append_a2_terms_to_registry_deterministic(
    a2_path: str,
    registry_path: str = "out/a2_registry/terms.jsonl",
    source_run_id: Optional[str] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible A2 terms registry appender.

    Wraps existing append_a2_terms_to_registry with provenance envelope.
    Appends A2 slang terms to registry with chained JSONL ledger.

    Args:
        a2_path: Path to A2 artifact JSON
        registry_path: Path to registry JSONL (default: out/a2_registry/terms.jsonl)
        source_run_id: Optional source run ID override
        seed: Optional deterministic seed (unused, kept for consistency)
        **kwargs: Additional arguments (captured for provenance)

    Returns:
        Dictionary with appended (int), registry_path (str), source_run_id (str),
        provenance, and not_computable
    """
    # Call core function (returns dict)
    result = append_a2_terms_to_registry_core(
        a2_path=a2_path,
        registry_path=registry_path,
        source_run_id=source_run_id
    )

    # Build canonical envelope
    inputs_dict = {
        "a2_path": a2_path,
        "registry_path": registry_path,
        "source_run_id": source_run_id
    }
    config_dict = {
        "seed": seed,
        **kwargs
    }

    envelope = canonical_envelope(
        inputs=inputs_dict,
        outputs=result,
        config=config_dict,
        errors=None
    )

    return {
        **result,
        "provenance": envelope["provenance"],
        "not_computable": None
    }


def compute_missed_terms_deterministic(
    a2_path: str,
    registry_path: str = "out/a2_registry/terms.jsonl",
    resurrect_after_days: int = 10,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible missed terms calculator.

    Wraps existing compute_missed_terms with provenance envelope.
    Computes missed (first-time) and resurrected (returned after absence) terms.

    Args:
        a2_path: Path to A2 artifact JSON
        registry_path: Path to registry JSONL (default: out/a2_registry/terms.jsonl)
        resurrect_after_days: Days threshold for resurrection (default: 10)
        seed: Optional deterministic seed (unused, kept for consistency)
        **kwargs: Additional arguments (captured for provenance)

    Returns:
        Dictionary with version, ts, run_id, a2_path, registry_path, present (int),
        known (int), missed (list), resurrected (list), params, provenance (nested from core),
        capability provenance, and not_computable
    """
    # Call core function (returns dict with nested provenance)
    result = compute_missed_terms_core(
        a2_path=a2_path,
        registry_path=registry_path,
        resurrect_after_days=resurrect_after_days
    )

    # Build canonical envelope
    inputs_dict = {
        "a2_path": a2_path,
        "registry_path": registry_path,
        "resurrect_after_days": resurrect_after_days
    }
    config_dict = {
        "seed": seed,
        **kwargs
    }

    envelope = canonical_envelope(
        inputs=inputs_dict,
        outputs=result,
        config=config_dict,
        errors=None
    )

    return {
        **result,
        "capability_provenance": envelope["provenance"],
        "not_computable": None
    }


__all__ = [
    "load_sources_from_osh_deterministic",
    "extract_claim_items_deterministic",
    "cluster_claims_deterministic",
    "load_dmx_context_deterministic",
    "build_term_index_deterministic",
    "reduce_weighted_metrics_deterministic",
    "build_term_token_index_deterministic",
    "assign_claim_to_terms_deterministic",
    "reduce_provenance_means_deterministic",
    "load_term_consensus_map_deterministic",
    "build_temporal_profiles_deterministic",
    "compute_dmx_deterministic",
    "read_oracle_texts_deterministic",
    "extract_terms_deterministic",
    "build_mimetic_weather_deterministic",
    "append_a2_terms_to_registry_deterministic",
    "compute_missed_terms_deterministic"
]
