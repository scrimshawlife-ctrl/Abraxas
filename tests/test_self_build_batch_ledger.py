from __future__ import annotations

from abraxas.registry.self_build_approval_setter import run_self_build_approval_setter
from abraxas.registry.self_build_batch_cycle import run_self_build_batch_cycle
from abraxas.registry.self_build_batch_ledger import append_batch_entry


def test_batch_ledger_appends_entry() -> None:
    run_self_build_approval_setter([], [])
    cycle = run_self_build_batch_cycle()
    ledger = append_batch_entry(cycle)
    assert ledger["schema_version"] == "SelfBuildBatchLedger.v1"
    assert ledger["entry_count"] >= 1


def test_batch_ledger_entry_has_required_fields() -> None:
    run_self_build_approval_setter([], [])
    cycle = run_self_build_batch_cycle()
    ledger = append_batch_entry(cycle)
    latest = ledger["entries"][-1]
    assert {"cycle_id", "status", "approvals", "applied_count", "score_feedback", "batch_cycle_hash", "post_validation", "authority"}.issubset(latest.keys())
    assert latest["authority"]["analysis_only"] is True


def test_batch_waiting_behavior_preserved_with_empty_approvals() -> None:
    run_self_build_approval_setter([], [])
    cycle = run_self_build_batch_cycle()
    assert cycle["status"] in {"WAITING_FOR_APPROVAL", "STOPPED_PREFLIGHT_NOT_GREEN"}
