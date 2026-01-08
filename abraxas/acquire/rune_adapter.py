"""Rune adapter for acquire capabilities.

Thin adapter layer exposing abraxas.acquire.* modules via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.acquire.decodo_client import (
    decodo_status as decodo_status_core,
    build_decodo_query as build_decodo_query_core
)
from abraxas.acquire.vector_map_schema import default_vector_map_v0_1 as default_vector_map_core


def decodo_status_deterministic(
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible Decodo status check.

    Wraps existing decodo_status with provenance envelope.
    Checks if DECODO_API_KEY environment variable is present.

    Args:
        seed: Optional deterministic seed (unused for status check, kept for consistency)

    Returns:
        Dictionary with status dict, provenance, and not_computable (always None)
    """
    # Call existing decodo_status function (returns DecodoStatus dataclass)
    status_obj = decodo_status_core()

    # Convert dataclass to dict
    status = status_obj.to_dict()

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"status": status},
        config={},
        inputs={},
        operation_id="acquire.decodo.status",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "status": status,
        "provenance": envelope["provenance"],
        "not_computable": None  # status check never fails
    }


def build_decodo_query_deterministic(
    term: str,
    domains: Optional[List[str]] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible Decodo query builder.

    Wraps existing build_decodo_query with provenance envelope.
    Creates declarative query object for Decodo API.

    Args:
        term: Search term
        domains: Optional list of domain filters
        seed: Optional deterministic seed (unused for query build, kept for consistency)

    Returns:
        Dictionary with query dict, provenance, and not_computable (always None)
    """
    # Call existing build_decodo_query function (returns dict)
    query = build_decodo_query_core(term, domains=domains)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"query": query},
        config={},
        inputs={"term": term, "domains": domains},
        operation_id="acquire.decodo.build_query",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "query": query,
        "provenance": envelope["provenance"],
        "not_computable": None  # query build never fails
    }


def default_vector_map_deterministic(
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible default vector map provider.

    Wraps existing default_vector_map_v0_1 with provenance envelope.
    Returns hardcoded default vector map with channel definitions.

    Args:
        seed: Optional deterministic seed (unused for default map, kept for consistency)

    Returns:
        Dictionary with vector_map dict, provenance, and not_computable (always None)
    """
    # Call existing default_vector_map_v0_1 function (returns dict)
    vector_map = default_vector_map_core()

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"vector_map": vector_map},
        config={},
        inputs={},
        operation_id="acquire.vector_map.default",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "vector_map": vector_map,
        "provenance": envelope["provenance"],
        "not_computable": None  # default map never fails
    }


__all__ = [
    "decodo_status_deterministic",
    "build_decodo_query_deterministic",
    "default_vector_map_deterministic"
]
