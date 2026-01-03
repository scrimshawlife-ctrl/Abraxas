"""Economics metric extractor for V11 proxies."""

from __future__ import annotations

from typing import Dict, List

from abraxas.metric_extractors.base import MetricExtractor, MetricPoint, packet_hash


def _series_values(payload: Dict[str, any]) -> List[Dict[str, any]]:
    return payload.get("series") or []


def _series_id(point: Dict[str, any]) -> str:
    meta = point.get("meta") or {}
    return str(meta.get("series_id") or "").lower()


def _delta(points: List[Dict[str, any]]) -> float | None:
    if len(points) < 2:
        return None
    return float(points[-1]["value"]) - float(points[0]["value"])


def _rate(points: List[Dict[str, any]]) -> float | None:
    if len(points) < 2:
        return None
    start = float(points[0]["value"])
    if start == 0:
        return None
    return (float(points[-1]["value"]) - start) / abs(start)


class EconomicsExtractor(MetricExtractor):
    extractor_name = "economics"
    version = "0.1"

    def accepts(self, source_id: str) -> bool:
        return source_id.startswith("ECON_")

    def extract(self, packets: List[Dict[str, any]], run_ctx: Dict[str, any]) -> List[MetricPoint]:
        points: List[MetricPoint] = []
        for packet in packets:
            payload = packet.get("payload") or {}
            series = _series_values(payload)
            ts = packet.get("observed_at_utc") or packet.get("window_end_utc") or "1970-01-01T00:00:00Z"
            window_start = packet.get("window_start_utc")
            window_end = packet.get("window_end_utc")
            base_prov = {
                "packet_hash": packet_hash(packet),
                "extractor_version": self.extractor_version(),
            }

            def emit(metric_id: str, value: float | None, notes: str):
                points.append(
                    MetricPoint(
                        metric_id=metric_id,
                        value=value,
                        ts_utc=ts,
                        window_start_utc=window_start,
                        window_end_utc=window_end,
                        source_id=packet.get("source_id"),
                        computability="computed" if value is not None else "not_computable",
                        provenance={**base_prov, "notes": notes},
                    )
                )

            inflation_points = [p for p in series if "inflation" in _series_id(p) or "cpi" in _series_id(p)]
            labor_points = [p for p in series if "unemployment" in _series_id(p) or "claims" in _series_id(p)]
            volatility_points = [p for p in series if "volatility" in _series_id(p) or "vix" in _series_id(p)]

            emit("economics.cost_of_living_delta_proxy", _delta(inflation_points), "cpi delta")
            emit("economics.inflation_rate_proxy", _rate(inflation_points), "inflation rate")
            emit("economics.labor_volatility_proxy", _delta(labor_points), "labor volatility")
            emit("economics.market_stress_proxy", _delta(volatility_points), "market stress")

        return points
