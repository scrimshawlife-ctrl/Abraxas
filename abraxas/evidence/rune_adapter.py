"""Rune adapter for evidence capabilities.

Thin adapter layer exposing abraxas.evidence.* modules via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from abraxas.core.provenance import canonical_envelope
from abraxas.evidence.index import evidence_by_term as evidence_by_term_core
from abraxas.evidence.support import support_weight_for_claim as support_weight_for_claim_core
from abraxas.evidence.lift import (
    load_bundles_from_index as load_bundles_from_index_core,
    term_lift as term_lift_core,
    uplift_factors as uplift_factors_core
)


def evidence_by_term_deterministic(
    bundles_dir: str,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible evidence index loader.

    Wraps existing evidence_by_term with provenance envelope.
    Loads evidence bundles and indexes them by term.

    Args:
        bundles_dir: Directory path containing evidence bundle JSON files
        seed: Optional deterministic seed (unused for loading, kept for consistency)

    Returns:
        Dictionary with evidence_by_term dict, provenance, and not_computable (always None)
    """
    # Call existing evidence_by_term function (no changes to core logic)
    evidence_index = evidence_by_term_core(bundles_dir)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"evidence_by_term": evidence_index},
        config={},
        inputs={"bundles_dir": bundles_dir},
        operation_id="evidence.index.evidence_by_term",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "evidence_by_term": evidence_index,
        "provenance": envelope["provenance"],
        "not_computable": None  # evidence indexing never fails, returns empty dict on error
    }


def support_weight_for_claim_deterministic(
    term: str,
    claim_text: str,
    evidence_by_term: Dict[str, List[Dict[str, Any]]],
    max_bonus: float = 0.35,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible evidence support weight calculator.

    Wraps existing support_weight_for_claim with provenance envelope.
    Computes support weight bonus based on evidence bundle overlap.

    Args:
        term: Term to look up evidence for
        claim_text: Claim text to compare against evidence bundles
        evidence_by_term: Term → evidence bundles index (from evidence_by_term)
        max_bonus: Maximum support weight bonus (default: 0.35)
        seed: Optional deterministic seed (unused for computation, kept for consistency)

    Returns:
        Dictionary with support_weight, debug dict, provenance, and not_computable (always None)
    """
    # Call existing support_weight_for_claim function (returns tuple)
    support_weight, debug = support_weight_for_claim_core(
        term=term,
        claim_text=claim_text,
        evidence_by_term=evidence_by_term,
        max_bonus=max_bonus
    )

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"support_weight": support_weight, "debug": debug},
        config={"max_bonus": max_bonus},
        inputs={"term": term, "claim_text": claim_text, "evidence_by_term": evidence_by_term},
        operation_id="evidence.support.support_weight",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "support_weight": support_weight,
        "debug": debug,
        "provenance": envelope["provenance"],
        "not_computable": None  # support weight computation never fails, returns 0.0 on error
    }


def load_bundles_from_index_deterministic(
    bundles_dir: str,
    index_path: str,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible evidence bundle loader.

    Wraps existing load_bundles_from_index with provenance envelope.
    Loads bundles using an evidence_index_<run>.json if available,
    falls back to full directory scan when index is missing or empty.

    Args:
        bundles_dir: Directory path containing evidence bundle JSON files
        index_path: Path to evidence_index_<run>.json file
        seed: Optional deterministic seed (unused for file I/O, kept for consistency)

    Returns:
        Dictionary with bundles list, provenance, and not_computable (always None)
    """
    # Call existing load_bundles_from_index function
    bundles = load_bundles_from_index_core(bundles_dir, index_path)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"bundles": bundles},
        config={},
        inputs={"bundles_dir": bundles_dir, "index_path": index_path},
        operation_id="evidence.lift.load_bundles_from_index",
        seed=seed
    )

    return {
        "bundles": bundles,
        "provenance": envelope["provenance"],
        "not_computable": None  # bundle loading never fails, returns empty list on error
    }


def term_lift_deterministic(
    bundles: List[Dict[str, Any]],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible term lift calculator.

    Wraps existing term_lift with provenance envelope.
    Computes term(lowercase) → lift summary mapping.

    Args:
        bundles: List of evidence bundle dictionaries
        seed: Optional deterministic seed

    Returns:
        Dictionary with lift_by_term dict, provenance, and not_computable (always None)
    """
    # Call existing term_lift function
    lift_by_term = term_lift_core(bundles)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"lift_by_term": lift_by_term},
        config={},
        inputs={"bundles": bundles},
        operation_id="evidence.lift.term_lift",
        seed=seed
    )

    return {
        "lift_by_term": lift_by_term,
        "provenance": envelope["provenance"],
        "not_computable": None  # term lift computation never fails
    }


def uplift_factors_deterministic(
    lift: Dict[str, Any],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible uplift factors calculator.

    Wraps existing uplift_factors with provenance envelope.
    Converts lift summary into bounded additive uplifts for attribution and diversity.

    Args:
        lift: Lift summary from term_lift for a single term
        seed: Optional deterministic seed

    Returns:
        Dictionary with attribution_uplift, diversity_uplift, provenance, and not_computable (always None)
    """
    # Call existing uplift_factors function (returns tuple)
    attribution_uplift, diversity_uplift = uplift_factors_core(lift)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"attribution_uplift": attribution_uplift, "diversity_uplift": diversity_uplift},
        config={},
        inputs={"lift": lift},
        operation_id="evidence.lift.uplift_factors",
        seed=seed
    )

    return {
        "attribution_uplift": attribution_uplift,
        "diversity_uplift": diversity_uplift,
        "provenance": envelope["provenance"],
        "not_computable": None  # uplift factors computation never fails
    }


__all__ = [
    "evidence_by_term_deterministic",
    "support_weight_for_claim_deterministic",
    "load_bundles_from_index_deterministic",
    "term_lift_deterministic",
    "uplift_factors_deterministic"
]
