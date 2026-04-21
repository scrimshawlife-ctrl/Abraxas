from __future__ import annotations

from abraxas.runes.gap_closure.bridge_oracle_forecast import build_oracle_forecast_bridge_packet


def test_oracle_forecast_bridge_packet() -> None:
    packet = build_oracle_forecast_bridge_packet(
        {"run_id": "RUN-GAP-FIRST-0001", "input_hash": "a" * 64, "status": "COMPLETE"}
    )
    assert packet["schema_version"] == "oracle_forecast_bridge_packet.v1"
    assert packet["promotion_recommendation"] == "HOLD"
