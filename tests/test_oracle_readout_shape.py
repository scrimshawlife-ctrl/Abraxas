from __future__ import annotations

from abraxas.core.oracle_runner import OracleRunInputs
from abraxas.kernel.v2.engine import run_oracle_v2


def test_oracle_readout_has_all_sections():
    inputs = OracleRunInputs(
        day="2026-01-09",
        user={"location_label": "Los Angeles, CA", "tier": "psychonaut"},
        overlays_enabled={},
        tier_ctx={"tier": "psychonaut", "limits": {}, "flags": {}, "depth": {}},
        checkin=None,
    )
    out = run_oracle_v2(inputs)
    for key in (
        "header",
        "vector_mix",
        "kairos",
        "runic_weather",
        "gate_and_trial",
        "memetic_futurecast",
        "financials",
        "overlays",
        "provenance",
    ):
        assert key in out, f"Missing section: {key}"


def test_oracle_readout_overlays_packets_present_even_when_disabled():
    inputs = OracleRunInputs(
        day="2026-01-09",
        user={"location_label": "Los Angeles, CA"},
        overlays_enabled={},
        tier_ctx={"tier": "psychonaut", "limits": {}, "flags": {}, "depth": {}},
        checkin=None,
    )
    out = run_oracle_v2(inputs)
    assert "packets" in out["overlays"]
    assert isinstance(out["overlays"]["packets"], dict)
