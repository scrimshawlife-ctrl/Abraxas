"""Rune adapter for compression detection capability."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from abraxas.compression.dispatch import detect_compression
from abraxas.core.provenance import canonical_envelope


def detect_compression_deterministic(
    text_event: Optional[str] = None,
    records: Optional[List[Dict[str, Any]]] = None,
    lexicon: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None,
    strict_execution: bool = True,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Deterministic wrapper for compression detection."""
    _ = strict_execution
    payload = {
        "text_event": text_event,
        "records": records,
        "lexicon": lexicon or [],
        "config": config or {},
    }
    result = detect_compression(payload)

    envelope = canonical_envelope(
        result=result,
        config={"config": config or {}},
        inputs={
            "text_event": text_event,
            "records": records,
            "lexicon": lexicon or [],
        },
        operation_id="compression.detect",
        seed=seed,
    )

    output = dict(result)
    output["provenance"] = envelope["provenance"]
    output["not_computable"] = envelope["not_computable"]
    return output
