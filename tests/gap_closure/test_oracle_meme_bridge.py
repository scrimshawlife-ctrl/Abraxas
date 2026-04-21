from __future__ import annotations

from abraxas.runes.gap_closure.bridge_oracle_meme import build_oracle_meme_bridge_packet


def test_oracle_meme_bridge_packet() -> None:
    packet = build_oracle_meme_bridge_packet(
        {"run_id": "RUN-GAP-FIRST-0001", "input_hash": "b" * 64, "status": "COMPLETE"}
    )
    assert packet["schema_version"] == "oracle_meme_bridge_packet.v1"
    assert packet["promotion_recommendation"] == "HOLD"
