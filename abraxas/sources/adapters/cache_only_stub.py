"""Cache-only adapter helper for external sources."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from abraxas.sources.adapters.base import SourceAdapter, load_cached
from abraxas.sources.packets import SourcePacket
from abraxas.sources.types import SourceSpec, SourceWindow


class CacheOnlyAdapter(SourceAdapter):
    adapter_name: str = "cache_only"
    version: str = "0.1"

    def fetch(self, window: SourceWindow, params: Dict[str, Any], cache_dir: Optional[Path], run_ctx: Dict[str, Any]) -> bytes:
        cache_key = self.cache_key(window=window, params=params, run_ctx=run_ctx)
        cache_path = self.cache_path(cache_dir=cache_dir, cache_key=cache_key)
        return load_cached(cache_path)

    def parse(self, raw: bytes, run_ctx: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {"raw_text": raw.decode("utf-8", errors="replace")}

    def emit_packets(
        self,
        parsed: Dict[str, Any],
        *,
        source_spec: SourceSpec,
        window: SourceWindow,
        cache_path: Optional[Path],
        raw_hash: str,
    ) -> list[SourcePacket]:
        provenance = {
            "fetch_hash": raw_hash,
            "parse_hash": "cache_only",
            "adapter_version": self.adapter_version(),
            "cache_path": str(cache_path) if cache_path else None,
            "refs": [ref.model_dump() for ref in source_spec.refs],
            "notes": "cache-only adapter; no network fetch",
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
