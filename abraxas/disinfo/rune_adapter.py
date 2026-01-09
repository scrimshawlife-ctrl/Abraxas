"""Rune adapter for disinfo capabilities.

Thin adapter layer exposing abraxas.disinfo.* modules via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.disinfo.apply import apply_disinfo_metrics as apply_disinfo_metrics_core


def apply_disinfo_metrics_deterministic(
    item: Dict[str, Any],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible disinformation metrics applicator.

    Wraps existing apply_disinfo_metrics with provenance envelope.
    Applies PI (Provenance Integrity), SML (Synthetic Media Likelihood),
    and NMP (Narrative Manipulation Pressure) metrics to an item.

    Args:
        item: Item dict to apply metrics to (source, context, etc.)
        seed: Optional deterministic seed (unused for metrics, kept for consistency)

    Returns:
        Dictionary with enriched_item, provenance, and not_computable (always None)
    """
    # Call existing apply_disinfo_metrics function (modifies item in-place, returns it)
    enriched_item = apply_disinfo_metrics_core(item)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"enriched_item": enriched_item},
        config={},
        inputs={"item": item},
        operation_id="disinfo.apply.metrics",
        seed=seed
    )

    # Return with renamed keys for clarity
    return {
        "enriched_item": enriched_item,
        "provenance": envelope["provenance"],
        "not_computable": None  # metric application never fails, returns enriched item
    }


__all__ = [
    "apply_disinfo_metrics_deterministic"
]
