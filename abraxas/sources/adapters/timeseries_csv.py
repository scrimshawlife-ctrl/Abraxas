"""Cache-first time series CSV adapter."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.sources.adapters.base import SourceAdapter
from abraxas.sources.packets import SourcePacket
from abraxas.sources.types import SourceSpec, SourceWindow


class TimeSeriesCSVAdapter(SourceAdapter):
    adapter_name = "timeseries_csv"
    version = "0.1"

    def fetch(self, window: SourceWindow, params: Dict[str, Any], cache_dir: Optional[Path], run_ctx: Dict[str, Any]) -> bytes:
        path = Path(params["path"])
        return path.read_bytes()

    def parse(self, raw: bytes, run_ctx: Dict[str, Any]) -> Dict[str, Any]:
        rows = []
        reader = csv.DictReader(raw.decode("utf-8").splitlines())
        for row in reader:
            ts = row.get("ts") or row.get("timestamp") or row.get("date")
            value = float(row.get("value"))
            unit = row.get("unit") or "unit"
            series_id = row.get("series_id") or "series"
            rows.append({"ts_utc": ts, "value": round(value, 6), "unit": unit, "meta": {"series_id": series_id}})
        return {"series": rows}

    def emit_packets(
        self,
        parsed: Dict[str, Any],
        *,
        source_spec: SourceSpec,
        window: SourceWindow,
        cache_path: Optional[Path],
        raw_hash: str,
    ) -> List[SourcePacket]:
        provenance = {
            "fetch_hash": raw_hash,
            "parse_hash": sha256_hex(canonical_json(parsed)),
            "adapter_version": self.adapter_version(),
            "cache_path": str(cache_path) if cache_path else None,
            "refs": [ref.model_dump() for ref in source_spec.refs],
            "notes": "timeseries csv",
        }
        return [
            SourcePacket(
                source_id=source_spec.source_id,
                observed_at_utc=window.end_utc or window.start_utc or "1970-01-01T00:00:00Z",
                window_start_utc=window.start_utc,
                window_end_utc=window.end_utc,
                payload=parsed,
                provenance=provenance,
            )
        ]
