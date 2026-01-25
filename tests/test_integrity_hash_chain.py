from __future__ import annotations

from abraxas.metrics.hashutil import hash_json, verify_hash_chain


def test_hash_chain_validation():
    entry_one = {"run_id": "run_001", "payload": {"signal": 1.0}, "prev_hash": "0" * 64}
    entry_two_payload = {"run_id": "run_002", "payload": {"signal": 2.0}}
    entry_two = {
        **entry_two_payload,
        "prev_hash": hash_json({k: v for k, v in entry_one.items() if k != "signature"}),
    }

    assert verify_hash_chain([entry_one, entry_two]) is True


def test_hash_chain_break_detection():
    entry_one = {"run_id": "run_001", "payload": {"signal": 1.0}, "prev_hash": "0" * 64}
    entry_two = {"run_id": "run_002", "payload": {"signal": 2.0}, "prev_hash": "bad"}

    assert verify_hash_chain([entry_one, entry_two]) is False
