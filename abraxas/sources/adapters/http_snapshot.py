"""HTTP snapshot adapter with deterministic cache-first fallback."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.sources.adapters.base import SourceAdapter, load_cached
from abraxas.sources.packets import SourcePacket
from abraxas.sources.types import SourceSpec, SourceWindow


class HTTPSnapshotAdapter(SourceAdapter):
    adapter_name = "http_snapshot"
    version = "0.2"

    @staticmethod
    def _safe_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _is_http_url(url: str) -> bool:
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
        except Exception:
            return False
        return parsed.scheme.lower() in ("http", "https") and bool(parsed.netloc.strip())

    def fetch(self, window: SourceWindow, params: Dict[str, Any], cache_dir: Optional[Path], run_ctx: Dict[str, Any]) -> bytes:
        cache_key = self.cache_key(window=window, params=params, run_ctx=run_ctx)
        cache_path = self.cache_path(cache_dir=cache_dir, cache_key=cache_key)

        url = str(params.get("url") or "").strip()
        timeout = self._safe_int(params.get("timeout_s"), 15)
        headers = params.get("headers") if isinstance(params.get("headers"), dict) else {}
        headers = {str(k): str(v) for k, v in headers.items()}
        if "User-Agent" not in headers:
            headers["User-Agent"] = f"abraxas/{self.adapter_id()}-http_snapshot"

        if not url:
            # cache-only fallback for determinism when URL isn't supplied in params.
            return load_cached(cache_path)
        if not self._is_http_url(url):
            raise ValueError(f"{self.adapter_id()} requires http(s) URL, got: {url!r}")

        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                raw = resp.read()
            if cache_path is not None:
                cache_path.write_bytes(raw)
            return raw
        except Exception:
            if cache_path is not None and cache_path.exists():
                return cache_path.read_bytes()
            raise

    def fetch_parse_emit(
        self,
        *,
        source_spec: SourceSpec,
        window: SourceWindow,
        params: Dict[str, Any],
        cache_dir: Optional[Path],
        run_ctx: Dict[str, Any],
    ) -> List[SourcePacket]:
        merged_params = dict(params)
        if not str(merged_params.get("url") or "").strip() and source_spec.refs:
            merged_params["url"] = str(source_spec.refs[0].url)
        return super().fetch_parse_emit(
            source_spec=source_spec,
            window=window,
            params=merged_params,
            cache_dir=cache_dir,
            run_ctx=run_ctx,
        )

    def parse(self, raw: bytes, run_ctx: Dict[str, Any]) -> Dict[str, Any]:
        try:
            parsed = json.loads(raw.decode("utf-8"))
            if isinstance(parsed, dict):
                return parsed
            return {"items": parsed}
        except Exception:
            return {"raw_text": raw.decode("utf-8", errors="replace")}

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
            "notes": "http snapshot adapter (network first, cache fallback)",
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
