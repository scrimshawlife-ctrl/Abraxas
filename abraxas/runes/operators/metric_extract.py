"""ABX-Rune Operator: METRIC_EXTRACT."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.metric_extractors import EXTRACTORS, MetricPoint
from abraxas.sources.domain_map import domain_for_source_id


class MetricExtractResult(BaseModel):
    shadow_only: bool = Field(True, description="Shadow-only enforcement")
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)


def apply_metric_extract(packets: List[Dict[str, Any]], *, strict_execution: bool = False) -> Dict[str, Any]:
    if strict_execution and packets is None:
        raise NotImplementedError("METRIC_EXTRACT requires packets")

    packet_domain_by_source: Dict[str, str] = {}
    packet_grade_by_source: Dict[str, str] = {}
    for packet in packets or []:
        source_id = str(packet.get("source_id") or "unknown")
        domain = packet.get("domain") or (packet.get("provenance") or {}).get("domain")
        packet_domain_by_source[source_id] = str(domain or domain_for_source_id(source_id))
        data_grade = packet.get("data_grade") or (packet.get("provenance") or {}).get("data_grade")
        packet_grade_by_source[source_id] = str(data_grade or "real")

    metrics: List[MetricPoint] = []
    for extractor in EXTRACTORS:
        accepted = [packet for packet in packets if extractor.accepts(packet.get("source_id"))]
        metrics.extend(extractor.extract(accepted, {}))

    for point in metrics:
        if not getattr(point, "domain", None) or point.domain == "unknown":
            point.domain = packet_domain_by_source.get(point.source_id) or domain_for_source_id(point.source_id)
        if not getattr(point, "data_grade", None):
            point.data_grade = packet_grade_by_source.get(point.source_id) or "real"

    payload = [point.canonical_payload() for point in metrics]
    provenance = {
        "inputs_hash": sha256_hex(canonical_json(packets or [])),
        "metrics_hash": sha256_hex(canonical_json(payload)),
    }
    return MetricExtractResult(metrics=payload, provenance=provenance).model_dump()
