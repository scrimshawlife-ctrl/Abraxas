from __future__ import annotations

import json

from abraxas.signal.exporter import emit_signal_packet
from abraxas.util.canonical_hash import canonical_hash


def test_emit_signal_packet_defaults():
    payload = {"kind": "unit_test"}
    packet = emit_signal_packet(
        payload=payload,
        tier="academic",
        lane="canon",
        confidence=None,
        provenance_status=None,
        invariance_status=None,
        drift_flags=None,
        rent_status=None,
        not_computable_regions=None,
        run_id="run-1",
        timestamp_utc="2026-02-03T00:00:00+00:00",
    )

    assert packet["signal_id"] == f"sig_{canonical_hash({'run_id': 'run-1'})[:16]}"
    assert packet["tier"] == "academic"
    assert packet["lane"] == "canon"
    assert packet["payload"] == payload
    assert packet["confidence"] == {}
    assert packet["provenance_status"] == "partial"
    assert packet["invariance_status"] == "not_evaluated"
    assert packet["drift_flags"] == []
    assert packet["rent_status"] == "not_applicable"
    assert packet["not_computable_regions"] == []

    serialized = json.dumps(packet, sort_keys=True)
    round_trip = json.loads(serialized)
    assert round_trip["signal_id"] == packet["signal_id"]

    try:
        from webpanel.models import AbraxasSignalPacket
    except Exception:
        return

    AbraxasSignalPacket.model_validate(packet)
