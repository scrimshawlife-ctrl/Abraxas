"""Temporal metric extractor (calendar/timezone snapshots)."""

from __future__ import annotations

from typing import Dict, List

from abraxas.metric_extractors.base import MetricExtractor, MetricPoint, packet_hash


class TemporalExtractor(MetricExtractor):
    extractor_name = "temporal"
    version = "0.1"

    def accepts(self, source_id: str) -> bool:
        return source_id in {"IANA_TZDB", "UNICODE_CLDR_SUPPLEMENTAL", "NIST_TIME_BULLETINS"}

    def extract(self, packets: List[Dict[str, any]], run_ctx: Dict[str, any]) -> List[MetricPoint]:
        points: List[MetricPoint] = []
        for packet in packets:
            payload = packet.get("payload") or {}
            events_count = payload.get("events_count")
            tz_changes = payload.get("timezone_offset_changes")
            ts = packet.get("observed_at_utc") or packet.get("window_end_utc") or "1970-01-01T00:00:00Z"
            if events_count is not None:
                points.append(
                    MetricPoint(
                        metric_id="temporal.events_count",
                        value=events_count,
                        ts_utc=ts,
                        window_start_utc=packet.get("window_start_utc"),
                        window_end_utc=packet.get("window_end_utc"),
                        source_id=packet.get("source_id"),
                        provenance={
                            "packet_hash": packet_hash(packet),
                            "extractor_version": self.extractor_version(),
                            "notes": "calendar events count",
                        },
                    )
                )
            else:
                points.append(
                    MetricPoint(
                        metric_id="temporal.events_count",
                        value=None,
                        ts_utc=ts,
                        window_start_utc=packet.get("window_start_utc"),
                        window_end_utc=packet.get("window_end_utc"),
                        source_id=packet.get("source_id"),
                        computability="not_computable",
                        provenance={
                            "packet_hash": packet_hash(packet),
                            "extractor_version": self.extractor_version(),
                            "notes": "calendar events count",
                        },
                    )
                )
            if tz_changes is not None:
                points.append(
                    MetricPoint(
                        metric_id="temporal.timezone_offset_changes",
                        value=tz_changes,
                        ts_utc=ts,
                        window_start_utc=packet.get("window_start_utc"),
                        window_end_utc=packet.get("window_end_utc"),
                        source_id=packet.get("source_id"),
                        provenance={
                            "packet_hash": packet_hash(packet),
                            "extractor_version": self.extractor_version(),
                            "notes": "timezone offset changes",
                        },
                    )
                )
        return points
