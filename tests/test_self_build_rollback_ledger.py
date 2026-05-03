from __future__ import annotations

from abraxas.registry.self_build_rollback_ledger import append_rollback_entry


def test_rollback_ledger_append() -> None:
    entry = {
        "mutation_id": "test",
        "target_path": "out/test.json",
        "pre_rollback_hash": "a",
        "restored_hash": "b",
        "approval": True,
        "status": "ROLLED_BACK",
        "failure_reason": None,
        "post_validation": {
            "validator": "PASS",
            "operator_health": "GREEN",
            "invariance": True,
        },
        "timestamp": 1.0,
        "commit": "abc",
    }
    ledger = append_rollback_entry(entry)
    assert ledger["entry_count"] >= 1
    assert "rollback_id" in ledger["entries"][-1]
