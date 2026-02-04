from webpanel.models import AbraxasSignalPacket
from webpanel.osl_v2 import build_input_envelope_for_hash, stable_hash


def _packet(timestamp_utc: str, payload: dict) -> AbraxasSignalPacket:
    return AbraxasSignalPacket(
        signal_id="sig-hash",
        timestamp_utc=timestamp_utc,
        tier="psychonaut",
        lane="canon",
        payload=payload,
        confidence={"score": "0.5"},
        provenance_status="complete",
        invariance_status="pass",
        drift_flags=["drift_a"],
        rent_status="paid",
        not_computable_regions=[{"region_id": "r1", "reason_code": "missing"}],
    )


def test_stable_hash_deterministic_for_key_order():
    left = {"b": 2, "a": 1}
    right = {"a": 1, "b": 2}
    assert stable_hash(left) == stable_hash(right)


def test_input_envelope_hash_ignores_timestamps():
    payload = {"alpha": {"beta": 1}}
    packet_a = _packet("2026-02-03T00:00:00+00:00", payload)
    packet_b = _packet("2026-02-04T00:00:00+00:00", payload)

    hash_a = stable_hash(build_input_envelope_for_hash(packet_a))
    hash_b = stable_hash(build_input_envelope_for_hash(packet_b))
    assert hash_a == hash_b


def test_input_envelope_hash_changes_on_payload():
    packet_a = _packet("2026-02-03T00:00:00+00:00", {"alpha": {"beta": 1}})
    packet_b = _packet("2026-02-03T00:00:00+00:00", {"alpha": {"beta": 2}})

    hash_a = stable_hash(build_input_envelope_for_hash(packet_a))
    hash_b = stable_hash(build_input_envelope_for_hash(packet_b))
    assert hash_a != hash_b
