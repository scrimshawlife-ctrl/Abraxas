"""Astronomy metric extractor (Horizons cache-only scaffolding)."""

from __future__ import annotations

from typing import Dict, List

from abraxas.metric_extractors.base import MetricExtractor, MetricPoint, packet_hash


class AstronomyExtractor(MetricExtractor):
    extractor_name = "astronomy"
    version = "0.1"

    def accepts(self, source_id: str) -> bool:
        return source_id == "NASA_JPL_HORIZONS_EPHEM"

    def extract(self, packets: List[Dict[str, any]], run_ctx: Dict[str, any]) -> List[MetricPoint]:
        points: List[MetricPoint] = []
        for packet in packets:
            payload = packet.get("payload") or {}
            lunar_phase = payload.get("lunar_phase")
            ts = packet.get("observed_at_utc") or packet.get("window_end_utc") or "1970-01-01T00:00:00Z"
            computability = "computed" if lunar_phase is not None else "not_computable"
            points.append(
                MetricPoint(
                    metric_id="astronomy.lunar_phase",
                    value=lunar_phase,
                    ts_utc=ts,
                    window_start_utc=packet.get("window_start_utc"),
                    window_end_utc=packet.get("window_end_utc"),
                    source_id=packet.get("source_id"),
                    computability=computability,
                    provenance={
                        "packet_hash": packet_hash(packet),
                        "extractor_version": self.extractor_version(),
                        "notes": "lunar phase",
                    },
                )
            )
        return points
