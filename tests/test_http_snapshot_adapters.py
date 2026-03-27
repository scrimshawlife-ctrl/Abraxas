from __future__ import annotations

from pathlib import Path

import pytest

from abraxas.sources.adapters.cldr_snapshot import CLDRSnapshotAdapter
from abraxas.sources.adapters.http_snapshot import HTTPSnapshotAdapter
from abraxas.sources.types import Cadence, CachePolicy, SourceKind, SourceRef, SourceSpec, SourceWindow


class _FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._payload


def _source_spec() -> SourceSpec:
    return SourceSpec(
        source_id="TEST_SOURCE",
        kind=SourceKind.governance,
        provider="test",
        cadence=Cadence.daily,
        backfill="none",
        adapter="http_snapshot",
        cache_policy=CachePolicy.required,
        determinism_notes="test",
        provenance_notes="test",
        refs=[SourceRef(id="r1", title="Ref", url="https://example.com")],
    )


def test_http_snapshot_fetch_network_then_cache(tmp_path, monkeypatch) -> None:
    adapter = HTTPSnapshotAdapter()
    window = SourceWindow(start_utc="2026-01-01T00:00:00Z", end_utc="2026-01-01T01:00:00Z")
    params = {"url": "https://example.com/data.json", "timeout_s": 3}
    run_ctx = {"run_id": "r1"}

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout=15: _FakeResponse(b'{"ok":true}'),
    )

    raw = adapter.fetch(window, params, tmp_path, run_ctx)
    assert raw == b'{"ok":true}'

    cache_key = adapter.cache_key(window=window, params=params, run_ctx=run_ctx)
    cache_file = tmp_path / f"{adapter.adapter_id()}_{cache_key}.bin"
    assert cache_file.exists()


def test_http_snapshot_fetch_uses_cache_on_network_error(tmp_path, monkeypatch) -> None:
    adapter = HTTPSnapshotAdapter()
    window = SourceWindow(start_utc="2026-01-01T00:00:00Z", end_utc="2026-01-01T01:00:00Z")
    params = {"url": "https://example.com/data.json"}
    run_ctx = {"run_id": "r2"}

    cache_key = adapter.cache_key(window=window, params=params, run_ctx=run_ctx)
    cache_file = tmp_path / f"{adapter.adapter_id()}_{cache_key}.bin"
    cache_file.write_bytes(b'{"cached":1}')

    def _raise(*args, **kwargs):
        raise OSError("network down")

    monkeypatch.setattr("urllib.request.urlopen", _raise)

    raw = adapter.fetch(window, params, tmp_path, run_ctx)
    assert raw == b'{"cached":1}'


def test_http_snapshot_parse_and_emit_packets() -> None:
    adapter = HTTPSnapshotAdapter()
    parsed = adapter.parse(b'{"k":1}', run_ctx={})
    assert parsed == {"k": 1}

    parsed_text = adapter.parse(b"not-json", run_ctx={})
    assert "raw_text" in parsed_text

    packets = adapter.emit_packets(
        parsed={"k": 1},
        source_spec=_source_spec(),
        window=SourceWindow(start_utc="2026-01-01T00:00:00Z", end_utc="2026-01-01T01:00:00Z"),
        cache_path=Path("/tmp/cache.bin"),
        raw_hash="abc",
    )
    assert len(packets) == 1
    assert packets[0].source_id == "TEST_SOURCE"
    assert packets[0].provenance["fetch_hash"] == "abc"


def test_stubbed_adapters_now_use_http_snapshot() -> None:
    assert issubclass(CLDRSnapshotAdapter, HTTPSnapshotAdapter)


def test_http_snapshot_rejects_non_http_url(tmp_path) -> None:
    adapter = HTTPSnapshotAdapter()
    window = SourceWindow(start_utc="2026-01-01T00:00:00Z", end_utc="2026-01-01T01:00:00Z")
    with pytest.raises(ValueError, match="requires http\\(s\\) URL"):
        adapter.fetch(window, {"url": "file:///etc/passwd"}, tmp_path, {"run_id": "r3"})


def test_http_snapshot_fetch_parse_emit_uses_source_ref_when_url_missing(tmp_path, monkeypatch) -> None:
    adapter = HTTPSnapshotAdapter()
    window = SourceWindow(start_utc="2026-01-01T00:00:00Z", end_utc="2026-01-01T01:00:00Z")
    source = _source_spec()

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout=15: _FakeResponse(b'{"from":"ref"}'),
    )

    packets = adapter.fetch_parse_emit(
        source_spec=source,
        window=window,
        params={},
        cache_dir=tmp_path,
        run_ctx={"run_id": "r4"},
    )
    assert len(packets) == 1
    assert packets[0].payload == {"from": "ref"}
