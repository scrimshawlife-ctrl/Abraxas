from abx_familiar.runtime.familiar_runtime import FamiliarRuntime
from abx_familiar.governance.invariance_harness import run_invariance_harness


def test_invariance_harness_passes_when_runtime_is_deterministic():
    # Use a fresh runtime with NO ledger store to avoid run-to-run variance
    rt = FamiliarRuntime()

    ctx = {
        "run_id": "r_inv",
        "summoner": {
            "task_id": "t_ok",
            "tier_scope": "Academic",
            "mode": "Analyst",
            "requested_ops": [],
            "constraints": {"x": 1},
        },
    }

    report = run_invariance_harness(runtime=rt, context=ctx, runs_required=12)
    assert report.passed is True
    assert report.reason == "hash_equal"
