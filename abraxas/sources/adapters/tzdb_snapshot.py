"""Adapter for vendored IANA TZDB snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from abraxas.core.canonical import sha256_hex
from abraxas.sources.adapters.base import SourceAdapter, cache_raw
from abraxas.sources.packets import SourcePacket
from abraxas.sources.types import SourceSpec, SourceWindow


class TZDBSnapshotAdapter(SourceAdapter):
    adapter_name = "tzdb_snapshot"

    def _snapshot_path(self, params: Dict[str, Any]) -> Path:
        version = params.get("version") or "2025c"
        return Path(__file__).resolve().parents[3] / "data" / "temporal" / f"iana_tzdb_{version}.json"

    def fetch(self, window: SourceWindow, params: Dict[str, Any], cache_dir: Optional[Path], run_ctx: Dict[str, Any]) -> bytes:
        path = self._snapshot_path(params)
        raw = path.read_bytes()
        cache_raw(raw, cache_dir, f"tzdb_{sha256_hex(raw)[:12]}")
        return raw

    def parse(self, raw: bytes, run_ctx: Dict[str, Any]) -> Dict[str, Any]:
        return json.loads(raw.decode("utf-8"))

    def emit_packets(
        self,
        parsed: Dict[str, Any],
        *,
        source_spec: SourceSpec,
        window: SourceWindow,
        cache_path: Optional[Path],
        raw_hash: str,
    ) -> List[SourcePacket]:
        observed_at = parsed.get("generated_at_utc") or "1970-01-01T00:00:00Z"
        payload = {
            "version": parsed.get("version"),
            "zones": parsed.get("zones"),
        }
        provenance = {
            "fetch_hash": raw_hash,
            "parse_hash": sha256_hex(json.dumps(payload, sort_keys=True).encode("utf-8")),
            "adapter_version": self.adapter_version(),
            "cache_path": str(cache_path) if cache_path else None,
            "refs": [ref.model_dump() for ref in source_spec.refs],
            "notes": "tzdb snapshot parsed",
            "snapshot_version": parsed.get("version"),
        }
        return [
            SourcePacket(
                source_id=source_spec.source_id,
                observed_at_utc=str(observed_at),
                window_start_utc=window.start_utc,
                window_end_utc=window.end_utc,
                payload=payload,
                provenance=provenance,
            )
        ]
