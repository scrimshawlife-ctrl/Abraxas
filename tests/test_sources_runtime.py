from __future__ import annotations

import json
from pathlib import Path

import pytest

from abraxas.cli.sources import fetch_source_cmd, fetch_sources_batch_cmd, refresh_sources_cmd
from abx.boundary.adapterContainment import build_adapter_containment_report
from abx.boundary.connectorCapabilities import build_connector_capabilities
from abraxas.sources.atlas import get_source
from abraxas.sources.runtime import ADAPTER_REGISTRY, resolve_adapter, run_source_once, run_sources_batch
from abraxas.sources.types import CachePolicy, SourceWindow

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "sources"

_P0_SOURCES = (
    ("WORLDBANK_REGION_V2", "worldbank_region_v2", "worldbank_region_v2.json"),
    ("EXCHANGERATE_OPEN_V6", "exchangerate_open_v6", "exchangerate_open_v6.json"),
    ("USGS_EARTHQUAKE_FDSN", "usgs_earthquake_fdsn", "usgs_earthquake_fdsn.json"),
    ("US_FEDERAL_REGISTER", "us_federal_register", "us_federal_register.json"),
    ("RESTCOUNTRIES_V3", "restcountries_v3", "restcountries_v3.json"),
)


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


@pytest.mark.parametrize("source_id,adapter_name,fixture_name", _P0_SOURCES)
def test_p0_source_resolves_via_get_source_and_adapter(
    source_id: str,
    adapter_name: str,
    fixture_name: str,
    monkeypatch,
    tmp_path,
) -> None:
    spec = get_source(source_id)
    assert spec is not None
    assert spec.source_id == source_id
    assert spec.adapter == adapter_name
    assert spec.cache_policy == CachePolicy.required
    assert spec.refs
    assert spec.refs[0].url.startswith("http")
    assert "SHADOW" in spec.provenance_notes
    assert "influence=NONE" in spec.provenance_notes

    adapter = resolve_adapter(adapter_name)
    assert adapter.adapter_name == adapter_name
    assert ADAPTER_REGISTRY[adapter_name] is type(adapter)

    fixture_bytes = (_FIXTURES / fixture_name).read_bytes()
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout=15: _FakeResponse(fixture_bytes),
    )
    packets = run_source_once(
        source_id=source_id,
        window=SourceWindow(start_utc="2026-01-01T00:00:00Z", end_utc="2026-01-01T01:00:00Z"),
        params={},
        cache_dir=tmp_path,
        run_ctx={"run_id": f"p0-{adapter_name}"},
    )
    assert len(packets) == 1
    assert packets[0].source_id == source_id
    assert packets[0].payload
    assert packets[0].provenance["adapter_version"] == adapter.adapter_version()


def test_p0_connectors_are_translation_only_external_asserted() -> None:
    connector_ids = {
        "connector.worldbank_region_v2",
        "connector.exchangerate_open_v6",
        "connector.usgs_earthquake_fdsn",
        "connector.us_federal_register",
        "connector.restcountries_v3",
    }
    capabilities = {row.connector_id: row for row in build_connector_capabilities()}
    for connector_id in connector_ids:
        row = capabilities[connector_id]
        assert row.role == "translation"
        assert "policy_decision" in row.disallowed_actions
        assert "trust_escalation" in row.disallowed_actions

    report = build_adapter_containment_report()
    assert report["status"] == "PASS"
    transforms = [row for row in report["transforms"] if row["connector_id"] in connector_ids]
    assert len(transforms) == len(connector_ids)
    for row in transforms:
        assert row["transform_type"] == "translation"
        assert row["input_trust"] == "EXTERNAL_ASSERTED"
        assert row["output_trust"] == "EXTERNAL_ASSERTED"
        assert "policy_decision" not in (row["metadata"].get("policy_flags") or [])


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
