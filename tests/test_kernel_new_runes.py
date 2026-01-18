"""Kernel routing tests for newly wired runes."""

from __future__ import annotations

import pytest

from abx.kernel import invoke
from abraxas.runes.handlers.ser_run import run_scenario_envelope
from abraxas.runes.handlers.weather_generate import generate_weather


def _weather_payload():
    return {
        "compression_event": {
            "domain": "general",
            "compression_pressure": 0.6,
            "observed_frequency": 4,
            "replacement_direction_vector": {"humor": 0.2},
        },
        "time_window": {"start_utc": "2025-01-01T00:00:00Z", "end_utc": "2025-01-02T00:00:00Z"},
        "config": {"half_life_per_event_hours": 6.0},
    }


def _ser_payload():
    return {
        "priors": {"MRI": 0.4, "IRI": 0.2, "tau_memory": 0.8, "tau_latency": 0.3},
        "signals": {
            "weather": {"primary_weather": "MW-02"},
            "dm_snapshot": {"mri": 12.0, "iri": 8.0},
            "almanac_snapshot": {"entries": 3},
            "notes": "deterministic",
            "source_count": 2,
            "timestamp_utc": "2025-01-01T00:00:00Z",
        },
        "seed": {"seed": 1234},
        "config": {"run_id": "ser-test", "timestamp_utc": "2025-01-01T00:00:00Z"},
    }


def test_handlers_deterministic():
    weather_payload = _weather_payload()
    result_a = generate_weather(weather_payload)
    result_b = generate_weather(weather_payload)
    assert result_a == result_b

    ser_payload = _ser_payload()
    result_a = run_scenario_envelope(ser_payload)
    result_b = run_scenario_envelope(ser_payload)
    assert result_a == result_b


def test_kernel_routes_new_runes():
    weather = invoke("weather.generate", _weather_payload())
    assert weather["rune_id"] == "weather.generate"
    assert "weather_report" in weather["result"]

    ser = invoke("ser.run", _ser_payload())
    assert ser["rune_id"] == "ser.run"
    assert "envelope" in ser["result"]

    ingest = invoke(
        "daemon.ingest",
        {"source_config": {"source": "test"}, "poll_interval": {"seconds": 5}, "config": {}},
    )
    assert ingest["rune_id"] == "daemon.ingest"
    assert ingest["result"]["ingest_log"]["status"] == "plan_only"

    deploy = invoke(
        "edge.deploy_orin",
        {"target_profile": {"device": "orin"}, "release_artifacts": {"version": "1.0.0"}, "config": {}},
    )
    assert deploy["rune_id"] == "edge.deploy_orin"
    assert deploy["result"]["deploy_receipt"]["status"] == "plan_only"


def test_kernel_policy_gate(monkeypatch):
    from abx import kernel

    monkeypatch.setattr(kernel, "load_policy", lambda: {"allow_runes": []})
    with pytest.raises(PermissionError):
        invoke("weather.generate", _weather_payload())
