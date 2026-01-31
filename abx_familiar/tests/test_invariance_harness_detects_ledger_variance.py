from abx_familiar.ledger.in_memory_store import InMemoryAppendOnlyStore
from abx_familiar.runtime.familiar_runtime import FamiliarRuntime
from abx_familiar.governance.invariance_harness import run_invariance_harness


def test_invariance_harness_fails_when_ledger_makes_outputs_time_dependent():
    store = InMemoryAppendOnlyStore()
    rt = FamiliarRuntime(ledger_store=store)

    ctx = {
        "run_id": "r_inv_time",
        "stabilization_enabled": True,
        "stabilization_window_size": 12,
        "summoner": {
            "task_id": "t_ok",
            "tier_scope": "Academic",
            "mode": "Analyst",
            "requested_ops": [],
            "constraints": {"x": 1},
        },
    }

    report = run_invariance_harness(runtime=rt, context=ctx, runs_required=3)
    assert report.passed is False
    assert report.reason == "hash_mismatch"
    # Expect at least one mismatch keyed on ledger_entry
    assert any(m["key"] == "ledger_entry" for m in report.mismatches)
