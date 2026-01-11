"""Governance metric extractor for V10 proxies."""

from __future__ import annotations

from typing import Dict, List

from abraxas.metric_extractors.base import MetricExtractor, MetricPoint, packet_hash


def _documents(payload: Dict[str, any]) -> List[Dict[str, any]]:
    return payload.get("documents") or []


class GovernanceExtractor(MetricExtractor):
    extractor_name = "governance"
    version = "0.1"

    def accepts(self, source_id: str) -> bool:
        return source_id.startswith("GOV_") or source_id.startswith("GOVERNANCE_")

    def extract(self, packets: List[Dict[str, any]], run_ctx: Dict[str, any]) -> List[MetricPoint]:
        points: List[MetricPoint] = []
        for packet in packets:
            docs = _documents(packet.get("payload") or {})
            ts = packet.get("observed_at_utc") or packet.get("window_end_utc") or "1970-01-01T00:00:00Z"
            window_start = packet.get("window_start_utc")
            window_end = packet.get("window_end_utc")
            base_prov = {
                "packet_hash": packet_hash(packet),
                "extractor_version": self.extractor_version(),
            }
            doc_count = len(docs)
            total_chars = sum(len(doc.get("body", "")) for doc in docs)
            if doc_count == 0:
                value = None
            else:
                value = min(1.0, (doc_count / 50.0) + (total_chars / 50000.0))

            points.append(
                MetricPoint(
                    metric_id="governance.policy_density_proxy",
                    value=value,
                    ts_utc=ts,
                    window_start_utc=window_start,
                    window_end_utc=window_end,
                    source_id=packet.get("source_id"),
                    computability="computed" if value is not None else "not_computable",
                    provenance={**base_prov, "notes": "policy density"},
                )
            )
            points.append(
                MetricPoint(
                    metric_id="governance.enforcement_lag_proxy",
                    value=None,
                    ts_utc=ts,
                    window_start_utc=window_start,
                    window_end_utc=window_end,
                    source_id=packet.get("source_id"),
                    computability="not_computable",
                    provenance={**base_prov, "notes": "requires enforcement data"},
                )
            )
            points.append(
                MetricPoint(
                    metric_id="governance.compliance_cost_proxy",
                    value=None,
                    ts_utc=ts,
                    window_start_utc=window_start,
                    window_end_utc=window_end,
                    source_id=packet.get("source_id"),
                    computability="not_computable",
                    provenance={**base_prov, "notes": "requires compliance data"},
                )
            )
        return points
