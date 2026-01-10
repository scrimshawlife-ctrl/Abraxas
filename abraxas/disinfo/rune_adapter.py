"""Rune adapter for disinformation capabilities.

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
    Rune-compatible disinformation metric applicator.

    Wraps existing apply_disinfo_metrics with provenance envelope.
    Adds PI/SML/NMP disinfo metrics to an evidence item.

    Args:
        item: Evidence item dict to enrich with disinformation metrics
        seed: Optional deterministic seed (unused for calculation, kept for consistency)

    Returns:
        Dictionary with item, provenance, and not_computable (always None)
    """
    enriched_item = apply_disinfo_metrics_core(item)

    envelope = canonical_envelope(
        result={"item": enriched_item},
        config={},
        inputs={"item": item},
        operation_id="disinfo.metrics.apply",
        seed=seed
    )

    return {
        "item": enriched_item,
        "provenance": envelope["provenance"],
        "not_computable": None
    }
