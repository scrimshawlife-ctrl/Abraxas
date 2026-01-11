"""Base classes for deterministic source adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.sources.packets import SourcePacket
from abraxas.sources.types import SourceSpec, SourceWindow


class SourceAdapter:
    adapter_name: str = "base"
    version: str = "0.1"

    def adapter_id(self) -> str:
        return self.adapter_name

    def adapter_version(self) -> str:
        return self.version

    def cache_key(self, *, window: SourceWindow, params: Dict[str, Any], run_ctx: Dict[str, Any]) -> str:
        payload = {"window": window.model_dump(), "params": params, "adapter": self.adapter_id()}
        return sha256_hex(canonical_json(payload))

    def cache_path(self, *, cache_dir: Optional[Path], cache_key: str) -> Optional[Path]:
        if cache_dir is None:
            return None
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / f"{self.adapter_id()}_{cache_key}.bin"

    def fetch(self, window: SourceWindow, params: Dict[str, Any], cache_dir: Optional[Path], run_ctx: Dict[str, Any]) -> bytes:
        raise NotImplementedError

    def parse(self, raw: bytes, run_ctx: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def emit_packets(
        self,
        parsed: Dict[str, Any],
        *,
        source_spec: SourceSpec,
        window: SourceWindow,
        cache_path: Optional[Path],
        raw_hash: str,
    ) -> List[SourcePacket]:
        raise NotImplementedError

    def fetch_parse_emit(
        self,
        *,
        source_spec: SourceSpec,
        window: SourceWindow,
        params: Dict[str, Any],
        cache_dir: Optional[Path],
        run_ctx: Dict[str, Any],
    ) -> List[SourcePacket]:
        raw = self.fetch(window, params, cache_dir, run_ctx)
        parsed = self.parse(raw, run_ctx)
        cache_key = self.cache_key(window=window, params=params, run_ctx=run_ctx)
        cache_path = self.cache_path(cache_dir=cache_dir, cache_key=cache_key)
        raw_hash = sha256_hex(raw)
        return self.emit_packets(
            parsed,
            source_spec=source_spec,
            window=window,
            cache_path=cache_path,
            raw_hash=raw_hash,
        )


def cache_raw(raw: bytes, cache_dir: Optional[Path], cache_key: str) -> Optional[Path]:
    if cache_dir is None:
        return None
    cache_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{cache_key}.bin"
    path = cache_dir / filename
    path.write_bytes(raw)
    return path


def load_cached(cache_path: Optional[Path]) -> bytes:
    if cache_path is None or not cache_path.exists():
        raise FileNotFoundError("cache-only adapter requires cached payload")
    return cache_path.read_bytes()
