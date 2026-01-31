from abx_familiar.canary.canary_runner_v0 import run_canary


def test_canary_runner_passes_in_pure_mode():
    r = run_canary(5)
    assert r["passed"] is True
    assert r["reason"] == "hash_equal"
