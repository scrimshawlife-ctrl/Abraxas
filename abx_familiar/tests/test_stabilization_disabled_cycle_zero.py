from abx_familiar.ledger.in_memory_store import InMemoryAppendOnlyStore
from abx_familiar.runtime.familiar_runtime import FamiliarRuntime


def test_stabilization_disabled_cycle_is_zero():
    store = InMemoryAppendOnlyStore()
    rt = FamiliarRuntime(ledger_store=store)

    ctx = {
        "run_id": "r_no_stab",
        "summoner": {
            "task_id": "t_ok",
            "tier_scope": "Psychonaut",
            "mode": "Oracle",
            "requested_ops": [],
            "constraints": {},
        },
    }

    a = rt.execute(ctx)
    e = a["ledger_entry"]
    assert e.stabilization_cycle == 0
