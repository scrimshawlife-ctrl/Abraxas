"""Rune adapter for memetic capabilities.

Thin adapter layer exposing abraxas.memetic.* modules via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from abraxas.core.provenance import canonical_envelope
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


__all__ = [
    "load_sources_from_osh_deterministic"
]
