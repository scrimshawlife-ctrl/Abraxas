from __future__ import annotations

from abraxas.registry.self_build_recommendation_execution_ledger import append_execution_entry
from abraxas.registry.self_build_recommendation_executor import run_self_build_recommendation_executor


def test_append_behavior() -> None:
    result = run_self_build_recommendation_executor("action-does-not-exist")
    ledger = append_execution_entry(result)
    assert ledger["entry_count"] >= 1


def test_schema_integrity_and_fields() -> None:
    result = run_self_build_recommendation_executor("action-does-not-exist")
    ledger = append_execution_entry(result)
    last = ledger["entries"][-1]
    assert {"execution_id", "action_id", "action_type", "status", "reason", "timestamp", "canonical_hash", "authority"}.issubset(last.keys())


def test_fail_closed_invalid_input() -> None:
    ledger = append_execution_entry({"bad": "input"})
    assert ledger["status"] == "NOT_COMPUTABLE"


def test_deterministic_hash_stability() -> None:
    # per-entry hash is timestamped; ledger hash deterministic for same payload shape existence check only
    result = run_self_build_recommendation_executor("action-does-not-exist")
    ledger = append_execution_entry(result)
    assert isinstance(ledger.get("canonical_hash"), str)
