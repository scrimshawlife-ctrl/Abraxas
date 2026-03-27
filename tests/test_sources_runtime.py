from __future__ import annotations

import json

import pytest

from abraxas.cli.sources import fetch_source_cmd, fetch_sources_batch_cmd, refresh_sources_cmd
from abraxas.sources.runtime import resolve_adapter, run_source_once, run_sources_batch
from abraxas.sources.types import SourceWindow


class _FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._payload


def test_resolve_adapter_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unknown source adapter"):
        resolve_adapter("does_not_exist")


def test_run_source_once_uses_source_ref_fallback(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout=15: _FakeResponse(b'{"ok": true}'),
    )

    packets = run_source_once(
        source_id="NOAA_SWPC_PLANETARY_KP",
        window=SourceWindow(start_utc="2026-03-27T00:00:00Z", end_utc="2026-03-27T01:00:00Z"),
        params={},
        cache_dir=tmp_path,
        run_ctx={"run_id": "sources-runtime-test"},
    )

    assert len(packets) == 1
    assert packets[0].source_id == "NOAA_SWPC_PLANETARY_KP"
    assert packets[0].payload == {"ok": True}


def test_fetch_source_cmd_prints_packets(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout=15: _FakeResponse(b'{"signal":"charged"}'),
    )

    code = fetch_source_cmd(
        "NOAA_SWPC_PLANETARY_KP",
        start_utc="2026-03-27T00:00:00Z",
        end_utc="2026-03-27T01:00:00Z",
        params_json="{}",
        cache_dir=str(tmp_path),
        run_id="sources-cli-test",
    )
    assert code == 0

    out = capsys.readouterr().out
    payload = json.loads(out)
    assert isinstance(payload, list)
    assert payload[0]["source_id"] == "NOAA_SWPC_PLANETARY_KP"
    assert payload[0]["payload"] == {"signal": "charged"}


def test_run_sources_batch_collects_packets_and_errors(monkeypatch, tmp_path) -> None:
    def _fake_urlopen(request, timeout=15):
        url = str(request.full_url)
        if "planetary_k_index_1m" in url:
            return _FakeResponse(b'{"kp": 5}')
        raise OSError("blocked-for-test")

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    report = run_sources_batch(
        source_ids=["NOAA_SWPC_PLANETARY_KP", "TOMSK_SOS_SCHUMANN"],
        window=SourceWindow(start_utc="2026-03-27T00:00:00Z", end_utc="2026-03-27T01:00:00Z"),
        params_by_source={},
        default_params={},
        cache_dir=tmp_path,
        run_ctx={"run_id": "sources-batch-test"},
    )
    assert report["ok"] is False
    assert "NOAA_SWPC_PLANETARY_KP" in report["packets_by_source"]
    assert "TOMSK_SOS_SCHUMANN" in report["errors"]
    assert report["summary"]["total_sources"] == 2
    assert report["summary"]["failed"] == 1
    assert report["summary"]["succeeded"] == 1
    assert report["summary"]["total_packets"] == 1
    assert len(report["source_results"]) == 2


def test_fetch_sources_batch_cmd_prints_report(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout=15: _FakeResponse(b'{"batch":"ok"}'),
    )
    code = fetch_sources_batch_cmd(
        ["NOAA_SWPC_PLANETARY_KP", "NOAA_SWPC_PLANETARY_KP"],
        start_utc="2026-03-27T00:00:00Z",
        end_utc="2026-03-27T01:00:00Z",
        cache_dir=str(tmp_path),
    )
    assert code == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["source_ids"] == ["NOAA_SWPC_PLANETARY_KP"]
    assert payload["ok"] is True
    assert payload["summary"]["succeeded"] == 1


def test_fetch_sources_batch_cmd_strict_returns_nonzero_on_errors(monkeypatch, tmp_path) -> None:
    def _raise(*args, **kwargs):
        raise OSError("network down")

    monkeypatch.setattr("urllib.request.urlopen", _raise)
    code = fetch_sources_batch_cmd(
        ["NOAA_SWPC_PLANETARY_KP"],
        start_utc="2026-03-27T00:00:00Z",
        end_utc="2026-03-27T01:00:00Z",
        cache_dir=str(tmp_path),
        strict=True,
    )
    assert code == 2


def test_refresh_sources_cmd_writes_report(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout=15: _FakeResponse(b'{"refresh":"ok"}'),
    )
    out_file = tmp_path / "refresh_report.json"
    code = refresh_sources_cmd(
        ["NOAA_SWPC_PLANETARY_KP"],
        start_utc="2026-03-27T00:00:00Z",
        end_utc="2026-03-27T01:00:00Z",
        cache_dir=str(tmp_path),
        out=str(out_file),
    )
    assert code == 0
    assert out_file.exists()

    payload_stdout = json.loads(capsys.readouterr().out)
    payload_file = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload_stdout["kind"] == "source_refresh_report.v0"
    assert payload_file["report"]["ok"] is True


def test_refresh_sources_cmd_strict_returns_nonzero_on_errors(monkeypatch, tmp_path) -> None:
    def _raise(*args, **kwargs):
        raise OSError("network down")

    monkeypatch.setattr("urllib.request.urlopen", _raise)
    code = refresh_sources_cmd(
        ["NOAA_SWPC_PLANETARY_KP"],
        start_utc="2026-03-27T00:00:00Z",
        end_utc="2026-03-27T01:00:00Z",
        cache_dir=str(tmp_path),
        strict=True,
    )
    assert code == 2


def test_refresh_sources_cmd_requires_selection() -> None:
    with pytest.raises(SystemExit, match="No sources selected"):
        refresh_sources_cmd([], refresh_all=False)
