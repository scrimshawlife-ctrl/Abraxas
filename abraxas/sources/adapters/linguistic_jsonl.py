"""Cache-first linguistic JSONL adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.linguistics.packets import build_text_item
from abraxas.sources.adapters.base import SourceAdapter, load_cached
from abraxas.sources.packets import SourcePacket
from abraxas.sources.types import SourceSpec, SourceWindow


class LinguisticJSONLAdapter(SourceAdapter):
    adapter_name = "linguistic_jsonl"
    version = "0.1"

    def fetch(self, window: SourceWindow, params: Dict[str, Any], cache_dir: Optional[Path], run_ctx: Dict[str, Any]) -> bytes:
        path = Path(params["path"])
        return path.read_bytes()

    def parse(self, raw: bytes, run_ctx: Dict[str, Any]) -> Dict[str, Any]:
        items = []
        for line in raw.decode("utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            ts = payload.get("ts") or payload.get("ts_utc") or payload.get("timestamp")
            text = payload.get("text") or ""
            metadata = payload.get("meta") or {}
            items.append(build_text_item(str(ts), str(text), metadata).model_dump())
        return {"items": items}

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
            "notes": "linguistic jsonl cache",
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
