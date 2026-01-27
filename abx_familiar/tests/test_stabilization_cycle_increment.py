from abx_familiar.ledger.in_memory_store import InMemoryAppendOnlyStore
from abx_familiar.runtime.familiar_runtime import FamiliarRuntime


def test_stabilization_cycle_increments_with_prior_entry():
    store = InMemoryAppendOnlyStore()
    rt = FamiliarRuntime(ledger_store=store)

    # First run (no prior entry): cycle should become 1 when enabled
    ctx1 = {
        "run_id": "r1",
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
    a1 = rt.execute(ctx1)
    e1 = a1["ledger_entry"]
    assert e1.prior_run_id is None
    assert e1.stabilization_cycle == 1

    # Second run: cycle should increment to 2, prior_run_id should link
    ctx2 = {
        "run_id": "r2",
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
    a2 = rt.execute(ctx2)
    e2 = a2["ledger_entry"]
    assert e2.prior_run_id == "r1"
    assert e2.stabilization_cycle == 2
    assert e2.delta_summary in {"hash_equal", "hash_mismatch", "prior_missing", "current_missing", "both_missing"}
