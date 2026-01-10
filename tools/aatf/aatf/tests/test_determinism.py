from aatf.provenance import deterministic_hash


def test_deterministic_hash_is_stable():
    payload = {"a": 1, "b": [2, 3]}
    assert deterministic_hash(payload) == deterministic_hash(payload)
