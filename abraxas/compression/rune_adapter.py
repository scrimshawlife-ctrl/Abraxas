"""Rune adapter for compression capabilities.

Thin adapter layer exposing abraxas.compression.* modules via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.compression.dispatch import detect_compression as detect_compression_core


def detect_compression_deterministic(
    text_event: Optional[str] = None,
    records: Optional[list] = None,
    lexicon: Optional[list] = None,
    config: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible compression detector.
    Detects symbolic compression (SCO/ECO) events in text.

    Args:
        text_event: Single text event (optional if records provided)
        records: List of record dicts with 'text' field
        lexicon: List of canonical/variant token pairs
        config: Optional config dict (supports 'domain')
        seed: Deterministic seed (for provenance)

    Returns:
        Dict with compression_event, metrics, labels, confidence, events, provenance
    """
    if lexicon is None:
        lexicon = []
    if config is None:
        config = {}

    payload = {
        "text_event": text_event,
        "records": records,
        "lexicon": lexicon,
        "config": config,
    }

    result = detect_compression_core(payload)

    envelope = canonical_envelope(
        result=result,
        config=config,
        inputs={"text_event": text_event, "records": records, "lexicon": lexicon},
        operation_id="compression.detect",
        seed=seed
    )

    return {
        "compression_event": result["compression_event"],
        "metrics": result["metrics"],
        "labels": result["labels"],
        "confidence": result["confidence"],
        "events": result["events"],
        "provenance": envelope["provenance"],
        "not_computable": None
    }


__all__ = ["detect_compression_deterministic"]
