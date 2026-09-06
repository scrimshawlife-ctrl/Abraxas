"""Unit tests for the TimesFM 2.5 Shadow lab. No Hugging Face downloads."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from abraxas.sources.adapters.timesfm_local import TimesFMLocalAdapter
from abraxas.sources.atlas import get_source
from abraxas.sources.runtime import ADAPTER_REGISTRY, resolve_adapter
from abraxas.sources.timesfm_shadow.constants import (
    ADAPTER_ID,
    ATLAS_SOURCE_ID,
    BIAS_DELTA_FEED,
    HF_REVISION,
    LICENSE,
    MODEL_ID,
    RUNE_TIMESFM_FORECAST,
    RUNE_TIMESFM_FORECAST_KIND,
    SOURCE_ID,
)
from abraxas.sources.timesfm_shadow.energy_charts import parse_energy_charts_price
from abraxas.sources.timesfm_shadow.infer import extract_quantiles, nearest_quantile_index, run_timesfm_2_5_cpu
from abraxas.sources.timesfm_shadow.packets import (
    ForecastBlock,
    HistoryBlock,
    TimesFMShadowForecastV0,
    assert_shadow_locks,
    build_shadow_packet,
    default_fold_in,
)
from abraxas.sources.timesfm_shadow.smoke import main as smoke_main
from abraxas.sources.timesfm_shadow.smoke import run_de_lu_smoke
from abraxas.sources.types import CachePolicy, SourceWindow

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "sources"
_REPO = Path(__file__).resolve().parents[1]


class _FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._payload


def _history() -> HistoryBlock:
    return HistoryBlock(
        timestamps=["2024-01-01T00:00:00Z", "2024-01-01T01:00:00Z"],
        values=[10.0, 11.0],
        window_n=2,
    )


def _fake_infer(values, horizon, seed, hf_revision):
    assert hf_revision == HF_REVISION
    assert seed == 7
    assert values == [10.0, 11.0]
    mean = [float(i + 1) for i in range(horizon)]
    quantiles = {
        "q10": [float(i) for i in range(horizon)],
        "q50": [float(i + 1) for i in range(horizon)],
        "q90": [float(i + 2) for i in range(horizon)],
    }
    return mean, quantiles


def test_adapter_registered() -> None:
    assert ADAPTER_REGISTRY[ADAPTER_ID] is TimesFMLocalAdapter
    adapter = resolve_adapter(ADAPTER_ID)
    assert adapter.adapter_name == ADAPTER_ID
    assert adapter.adapter_version() == "0.1"


def test_atlas_energy_charts_is_shadow() -> None:
    spec = get_source(ATLAS_SOURCE_ID)
    assert spec is not None
    assert spec.adapter == ADAPTER_ID
    assert spec.cache_policy == CachePolicy.required
    assert "SHADOW" in spec.provenance_notes
    assert "influence=NONE" in spec.provenance_notes
    assert SOURCE_ID in spec.provenance_notes
    assert spec.refs[0].url.endswith("bzn=DE-LU")


def test_energy_charts_parse_fixture() -> None:
    payload = json.loads((_FIXTURES / "energy_charts_price_de_lu.json").read_text(encoding="utf-8"))
    history = parse_energy_charts_price(payload, window_n=8)
    assert history.window_n == 5
    assert history.timestamps[0] == "2024-01-01T00:00:00Z"
    assert history.values == [40.5, 41.25, 39.0, 38.5, 42.0]
    clipped = parse_energy_charts_price(payload, window_n=2)
    assert clipped.values == [38.5, 42.0]


def test_energy_charts_parse_rejects_bad_bzn_and_shape() -> None:
    payload = json.loads((_FIXTURES / "energy_charts_price_de_lu.json").read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match="bzn=DE-LU"):
        parse_energy_charts_price(payload, bzn="FR")
    with pytest.raises(ValueError, match="equal length"):
        parse_energy_charts_price({"unix_seconds": [1], "price": [1.0, 2.0]})


def test_adapter_parse_attaches_history() -> None:
    raw = (_FIXTURES / "energy_charts_price_de_lu.json").read_bytes()
    parsed = TimesFMLocalAdapter().parse(raw, run_ctx={"window_n": 3})
    assert parsed["history"]["window_n"] == 3
    assert parsed["history"]["values"] == [39.0, 38.5, 42.0]


def test_packet_locks_and_hash() -> None:
    packet = build_shadow_packet(
        history=_history(),
        mean=[1.0, 2.0],
        quantiles={"q10": [0.0, 1.0], "q50": [1.0, 2.0], "q90": [2.0, 3.0]},
        horizon=2,
        seed=7,
        hf_revision=HF_REVISION,
    )
    assert_shadow_locks(packet)
    assert packet.packet_type == "TimesFMShadowForecast.v0"
    assert packet.valid_for_forecast is False
    assert packet.license == LICENSE
    assert packet.model_id == MODEL_ID
    assert packet.hf_revision == HF_REVISION
    assert packet.semantics == "generative_prior_not_objective_probability"
    dumped = packet.model_dump()
    assert "objective_probability" not in dumped
    assert dumped == TimesFMShadowForecastV0.model_validate(dumped).model_dump()
    assert packet.packet_hash() == packet.packet_hash()


def test_packet_rejects_forecast_lane_and_wrong_revision() -> None:
    history = _history()
    forecast = ForecastBlock(
        horizon=1,
        mean=[1.0],
        quantiles={"q10": [0.0], "q50": [1.0], "q90": [2.0]},
    )
    with pytest.raises(ValidationError):
        TimesFMShadowForecastV0(
            valid_for_forecast=True,  # type: ignore[arg-type]
            hf_revision=HF_REVISION,
            seed=1,
            history=history,
            forecast=forecast,
            fold_in=default_fold_in(),
        )
    with pytest.raises(ValidationError, match="hf_revision"):
        TimesFMShadowForecastV0(
            hf_revision="deadbeef",
            seed=1,
            history=history,
            forecast=forecast,
            fold_in=default_fold_in(),
        )
    with pytest.raises(ValidationError):
        TimesFMShadowForecastV0(
            model_id="google/timesfm-3.0-demo",  # type: ignore[arg-type]
            hf_revision=HF_REVISION,
            seed=1,
            history=history,
            forecast=forecast,
            fold_in=default_fold_in(),
        )


def test_predict_uses_injected_infer_fn() -> None:
    packet = TimesFMLocalAdapter().predict(
        _history(),
        horizon=3,
        seed=7,
        hf_revision=HF_REVISION,
        infer_fn=_fake_infer,
    )
    assert packet.forecast.horizon == 3
    assert packet.forecast.mean == [1.0, 2.0, 3.0]
    assert packet.valid_for_forecast is False


def test_quantile_extractors() -> None:
    assert nearest_quantile_index((0.1, 0.5, 0.9), 0.5) == 1
    rows = [[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]]
    quantiles = extract_quantiles(rows, horizon=1)
    assert quantiles["q10"] == [1.0]
    assert quantiles["q50"] == [5.0]
    assert quantiles["q90"] == [9.0]


def test_optional_infer_requires_deps(monkeypatch) -> None:
    def _missing(name: str, feature_name: str, **kwargs):
        raise RuntimeError(f"missing {name} for {feature_name}")

    monkeypatch.setattr(
        "abraxas.sources.timesfm_shadow.infer.require_optional_dependency",
        _missing,
    )
    with pytest.raises(RuntimeError, match="missing torch"):
        run_timesfm_2_5_cpu([1.0, 2.0], 2, 1, HF_REVISION)


def test_smoke_cli_help() -> None:
    with pytest.raises(SystemExit) as exc:
        smoke_main(["--help"])
    assert exc.value.code == 0


def test_preflight_shadow_lab_is_eligible() -> None:
    cp = subprocess.run(
        [sys.executable, ".abraxas/scripts/preflight.py", "--subsystem", "timesfm_shadow_lab_v0"],
        capture_output=True,
        text=True,
        cwd=_REPO,
    )
    assert cp.returncode == 0
    assert "ELIGIBLE" in cp.stdout
    blocked = subprocess.run(
        [
            sys.executable,
            ".abraxas/scripts/preflight.py",
            "--subsystem",
            "timesfm_shadow_lab_v0",
            "--change-class",
            "forecast_active_change",
        ],
        capture_output=True,
        text=True,
        cwd=_REPO,
    )
    assert blocked.returncode == 1
    assert "restricted change class" in blocked.stdout


def test_rune_stub_is_code_only() -> None:
    assert RUNE_TIMESFM_FORECAST == "RUNE.TIMESFM_FORECAST"
    assert RUNE_TIMESFM_FORECAST_KIND == "code_only_stub"
    registry = json.loads((_REPO / "abraxas" / "runes" / "registry.json").read_text(encoding="utf-8"))
    ids = set()
    for row in registry.get("runes", []):
        if isinstance(row, dict):
            ids.add(str(row.get("id") or ""))
            ids.add(str(row.get("rune_id") or ""))
    assert RUNE_TIMESFM_FORECAST not in ids
    definitions = _REPO / "abraxas" / "runes" / "definitions"
    assert not list(definitions.glob("*timesfm*"))


def test_smoke_writes_local_json(monkeypatch, tmp_path) -> None:
    fixture = (_FIXTURES / "energy_charts_price_de_lu.json").read_bytes()
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout=15: _FakeResponse(fixture),
    )
    packet = run_de_lu_smoke(
        out_dir=tmp_path,
        horizon=2,
        seed=7,
        window_n=4,
        infer_fn=_fake_infer_from_any_history,
        cache_dir=tmp_path / "cache",
    )
    latest = tmp_path / "timesfm_shadow_forecast.v0.latest.json"
    assert latest.exists()
    payload = json.loads(latest.read_text(encoding="utf-8"))
    assert payload["valid_for_forecast"] is False
    assert payload["license"] == LICENSE
    assert payload["model_id"] == MODEL_ID
    assert payload["hf_revision"] == HF_REVISION
    assert payload["source_id"] == SOURCE_ID
    assert payload["bzn"] == "DE-LU"
    assert payload["forecast"]["horizon"] == 2
    bias = [feed for feed in payload["fold_in"]["feeds"] if feed["target"] == BIAS_DELTA_FEED][0]
    assert bias["writes_objective_probability"] is False
    assert packet.valid_for_forecast is False


def test_adapter_fetch_parse_emit_uses_energy_charts(monkeypatch, tmp_path) -> None:
    fixture = (_FIXTURES / "energy_charts_price_de_lu.json").read_bytes()
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout=15: _FakeResponse(fixture),
    )
    spec = get_source(ATLAS_SOURCE_ID)
    assert spec is not None
    packets = TimesFMLocalAdapter().fetch_parse_emit(
        source_spec=spec,
        window=SourceWindow(start_utc="2024-01-01T00:00:00Z", end_utc="2024-01-01T06:00:00Z"),
        params={},
        cache_dir=tmp_path,
        run_ctx={"run_id": "timesfm-unit", "window_n": 2},
    )
    assert len(packets) == 1
    assert packets[0].source_id == ATLAS_SOURCE_ID
    assert packets[0].payload["history"]["values"] == [38.5, 42.0]


def _fake_infer_from_any_history(values, horizon, seed, hf_revision):
    assert hf_revision == HF_REVISION
    assert len(values) >= 1
    mean = [float(values[-1]) for _ in range(horizon)]
    return mean, {"q10": mean, "q50": mean, "q90": mean}
