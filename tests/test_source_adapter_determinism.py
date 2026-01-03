"""Tests for deterministic adapter outputs."""

from __future__ import annotations

import hashlib

from abraxas.sources.adapters.tzdb_snapshot import TZDBSnapshotAdapter
from abraxas.sources.adapters.noaa_ncei_cdo import NCEICDOAdapter
from abraxas.sources.atlas import get_source
from abraxas.sources.types import SourceWindow


def _hash_packets(packets) -> str:
    payload = [packet.model_dump() for packet in packets]
    return hashlib.sha256(str(payload).encode("utf-8")).hexdigest()


def test_tzdb_adapter_deterministic(tmp_path):
    adapter = TZDBSnapshotAdapter()
    window = SourceWindow(start_utc="2025-01-01T00:00:00Z", end_utc="2025-12-31T23:59:59Z")
    source_spec = get_source("IANA_TZDB")
    assert source_spec is not None

    packets_a = adapter.fetch_parse_emit(
        source_spec=source_spec,
        window=window,
        params={"version": "2025c"},
        cache_dir=tmp_path,
        run_ctx={},
    )
    packets_b = adapter.fetch_parse_emit(
        source_spec=source_spec,
        window=window,
        params={"version": "2025c"},
        cache_dir=tmp_path,
        run_ctx={},
    )

    assert _hash_packets(packets_a) == _hash_packets(packets_b)


def test_cache_only_adapter_uses_cache(tmp_path):
    adapter = NCEICDOAdapter()
    window = SourceWindow(start_utc="2025-01-01T00:00:00Z", end_utc="2025-01-02T00:00:00Z")
    source_spec = get_source("NOAA_NCEI_CDO_V2")
    assert source_spec is not None

    cache_key = adapter.cache_key(window=window, params={"datasetid": "GHCND"}, run_ctx={})
    cache_path = adapter.cache_path(cache_dir=tmp_path, cache_key=cache_key)
    assert cache_path is not None
    cache_path.write_text("{\"cached\": true}", encoding="utf-8")

    packets = adapter.fetch_parse_emit(
        source_spec=source_spec,
        window=window,
        params={"datasetid": "GHCND"},
        cache_dir=tmp_path,
        run_ctx={},
    )
    assert packets[0].payload.get("cached") is True
