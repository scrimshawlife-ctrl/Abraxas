"""ABX-Rune Operator: METRIC_EXTRACT."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.metric_extractors import EXTRACTORS, MetricPoint


class MetricExtractResult(BaseModel):
    shadow_only: bool = Field(True, description="Shadow-only enforcement")
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)


def apply_metric_extract(packets: List[Dict[str, Any]], *, strict_execution: bool = False) -> Dict[str, Any]:
    if strict_execution and packets is None:
        raise NotImplementedError("METRIC_EXTRACT requires packets")

    metrics: List[MetricPoint] = []
    for extractor in EXTRACTORS:
        accepted = [packet for packet in packets if extractor.accepts(packet.get("source_id"))]
        metrics.extend(extractor.extract(accepted, {}))

    payload = [point.canonical_payload() for point in metrics]
    provenance = {
        "inputs_hash": sha256_hex(canonical_json(packets or [])),
        "metrics_hash": sha256_hex(canonical_json(payload)),
    }
    return MetricExtractResult(metrics=payload, provenance=provenance).model_dump()
