from abraxas.ers import Budget, DeterministicScheduler
from abraxas.ers.bindings import bind_callable
from abraxas.ers.invariance import dozen_run_invariance_gate


def test_dozen_run_invariance_gate_passes_for_deterministic_trace():
    s = DeterministicScheduler()

    def f(ctx): return {"ok": True}
    def g(ctx): return {"shadow": True}

    s.add(bind_callable(name="oracle:signal", lane="forecast", priority=0, cost_ops=1, fn=f))
    s.add(bind_callable(name="shadow:sei", lane="shadow", priority=0, cost_ops=1, fn=g))

    def make_trace(_i: int):
        out = s.run_tick(
            tick=0,
            budget_forecast=Budget(ops=10, entropy=0),
            budget_shadow=Budget(ops=10, entropy=0),
            context={},
        )
        return out["trace"]

    res = dozen_run_invariance_gate(make_trace=make_trace, runs=12)
    assert res.ok is True
    assert len(res.hashes) == 12
    # All hashes should be identical
    assert len(set(res.hashes)) == 1


def test_dozen_run_invariance_gate_detects_drift():
    """Test that the gate catches non-deterministic behavior."""
    counter = {"value": 0}

    def make_trace_with_drift(_i: int):
        # Create a new scheduler each time to simulate fresh run
        s = DeterministicScheduler()

        def non_deterministic_task(ctx):
            # Deliberately non-deterministic - throws error on even runs
            counter["value"] += 1
            if counter["value"] % 2 == 0:
                raise ValueError("Drift induced")
            return {"ok": True}

        s.add(bind_callable(name="task", lane="forecast", priority=0, cost_ops=1, fn=non_deterministic_task))

        out = s.run_tick(
            tick=0,
            budget_forecast=Budget(ops=10, entropy=0),
            budget_shadow=Budget(ops=10, entropy=0),
            context={},
        )
        return out["trace"]

    res = dozen_run_invariance_gate(make_trace=make_trace_with_drift, runs=12)
    assert res.ok is False
    assert res.first_mismatch_index == 1  # Second run should differ
    assert res.divergence is not None
    assert res.divergence["event_index"] == 0  # First event differs
    # Check that status differs (ok vs error)
    diff = res.divergence["diff"]
    assert diff["a"]["status"] != diff["b"]["status"]
