"""Tests for live atlas mode."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from abraxas.atlas.construct import build_atlas_pack
from abraxas.live.run import LiveRunContext, run_live_atlas
from abraxas.live.windowing import LiveWindowConfig, compute_live_windows


def _stub_invoke(capability: str, payload, ctx=None):
    if capability == "rune:metric_extract":
        return {"metrics": [{"metric_id": "test.metric", "value": 1.0, "timestamp_utc": "2025-01-01T00:00:00Z"}]}
    if capability == "rune:tvm_frame":
        return {
            "frames": [
                {
                    "window_start_utc": payload["window_start_utc"],
                    "window_end_utc": payload["window_end_utc"],
                    "domain": "test",
                    "vectors": {"V1_SIGNAL_DENSITY": {"score": 0.1}},
                    "provenance": {"frame_hash": "frame_hash"},
                }
            ]
        }
    if capability == "rune:influence_detect":
        return {"ics": {}, "provenance": {"inputs_hash": "influence_hash"}}
    if capability == "rune:synchronicity_map":
        return {"envelopes": [], "provenance": {"inputs_hash": "sync_hash"}}
    raise AssertionError(f"Unexpected capability: {capability}")


def _write_packet(cache_dir: Path, start: str, end: str) -> None:
    packet = {"window_start_utc": start, "window_end_utc": end, "source_id": "TEST"}
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "packet.json").write_text(json.dumps(packet), encoding="utf-8")


def test_live_windows_aligned():
    config = LiveWindowConfig(window_size="7d", step_size="1d", retention=2)
    windows = compute_live_windows("2025-01-10T12:34:00Z", config)
    assert windows[-1].end_utc == "2025-01-10T00:00:00Z"
    assert windows[-1].start_utc == "2025-01-03T00:00:00Z"
    assert windows[0].end_utc == "2025-01-09T00:00:00Z"
    assert windows[0].start_utc == "2025-01-02T00:00:00Z"


def test_live_deterministic(monkeypatch, tmp_path):
    monkeypatch.setattr("abraxas.live.run.invoke_capability", _stub_invoke)
    _write_packet(tmp_path, "2025-01-01T00:00:00Z", "2025-01-08T00:00:00Z")
    config = LiveWindowConfig(window_size="7d", step_size="1d", retention=1)
    run_ctx = LiveRunContext(run_id="run", now_utc="2025-01-08T00:00:00Z")
    hashes = {
        run_live_atlas(None, config, run_ctx, tmp_path).provenance["live_hash"]
        for _ in range(12)
    }
    assert len(hashes) == 1


def test_snapshot_matches_static_atlas(monkeypatch, tmp_path):
    monkeypatch.setattr("abraxas.live.run.invoke_capability", _stub_invoke)
    _write_packet(tmp_path, "2025-01-01T00:00:00Z", "2025-01-08T00:00:00Z")
    config = LiveWindowConfig(window_size="7d", step_size="1d", retention=1)
    run_ctx = LiveRunContext(run_id="run", now_utc="2025-01-08T00:00:00Z")
    live_pack = run_live_atlas(None, config, run_ctx, tmp_path)
    snapshot = live_pack.windows[-1]

    seedpack = {
        "schema_version": "seedpack.v0.2",
        "year": 2025,
        "frames": [
            {
                "window_start_utc": "2025-01-01T00:00:00Z",
                "window_end_utc": "2025-01-08T00:00:00Z",
                "domain": "test",
                "vectors": {"V1_SIGNAL_DENSITY": {"score": 0.1}},
                "provenance": {"frame_hash": "frame_hash"},
            }
        ],
        "influence": {"ics": {}, "provenance": {"inputs_hash": "influence_hash"}},
        "synchronicity": {"envelopes": [], "provenance": {"inputs_hash": "sync_hash"}},
    }
    seedpack["seedpack_hash"] = "seed_hash"
    static_pack = build_atlas_pack(seedpack, window_granularity="7d").model_dump()
    assert snapshot["pressure_cells"] == static_pack["pressure_cells"]


def test_cache_only_offline(monkeypatch, tmp_path):
    monkeypatch.setattr("abraxas.live.run.invoke_capability", _stub_invoke)
    config = LiveWindowConfig(window_size="7d", step_size="1d", retention=1)
    run_ctx = LiveRunContext(run_id="run", now_utc="2025-01-08T00:00:00Z")
    live_pack = run_live_atlas(None, config, run_ctx, tmp_path)
    assert live_pack.provenance["source_cache_hashes"] == []


def test_no_prediction_invoked(monkeypatch, tmp_path):
    monkeypatch.setattr("abraxas.live.run.invoke_capability", _stub_invoke)
    import sys
    import types

    forecast = types.SimpleNamespace()

    def _boom(*_args, **_kwargs):
        raise AssertionError("Prediction invoked during live atlas")

    forecast.run_forecast = _boom
    sys.modules["abraxas.forecast"] = forecast
    _write_packet(tmp_path, "2025-01-01T00:00:00Z", "2025-01-08T00:00:00Z")
    config = LiveWindowConfig(window_size="7d", step_size="1d", retention=1)
    run_ctx = LiveRunContext(run_id="run", now_utc="2025-01-08T00:00:00Z")
    run_live_atlas(None, config, run_ctx, tmp_path)
