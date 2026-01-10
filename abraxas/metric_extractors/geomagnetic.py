"""Geomagnetic metric extractor (Kp)."""

from __future__ import annotations

from typing import Any, Dict, List

from abraxas.metric_extractors.base import MetricExtractor, MetricPoint, packet_hash


class GeomagneticExtractor(MetricExtractor):
    extractor_name = "geomagnetic"
    version = "0.1"

    def accepts(self, source_id: str) -> bool:
        return source_id == "NOAA_SWPC_PLANETARY_KP"

    def extract(self, packets: List[Dict[str, Any]], run_ctx: Dict[str, Any]) -> List[MetricPoint]:
        points: List[MetricPoint] = []
        for packet in packets:
            payload = packet.get("payload") or {}
            kp_value = payload.get("kp_value")
            ts = packet.get("observed_at_utc") or packet.get("window_end_utc") or "1970-01-01T00:00:00Z"
            computability = "computed" if kp_value is not None else "not_computable"
            points.append(
                MetricPoint(
                    metric_id="geomagnetic.kp_value",
                    value=kp_value,
                    ts_utc=ts,
                    window_start_utc=packet.get("window_start_utc"),
                    window_end_utc=packet.get("window_end_utc"),
                    source_id=packet.get("source_id"),
                    computability=computability,
                    provenance={
                        "packet_hash": packet_hash(packet),
                        "extractor_version": self.extractor_version(),
                        "notes": "Kp index",
                    },
                )
            )
            if kp_value is not None:
                category = "quiet" if kp_value < 4 else "active" if kp_value < 6 else "storm"
                points.append(
                    MetricPoint(
                        metric_id="geomagnetic.kp_category",
                        value=category,
                        ts_utc=ts,
                        window_start_utc=packet.get("window_start_utc"),
                        window_end_utc=packet.get("window_end_utc"),
                        source_id=packet.get("source_id"),
                        provenance={
                            "packet_hash": packet_hash(packet),
                            "extractor_version": self.extractor_version(),
                            "notes": "Kp category",
                        },
                    )
                )
        return points
