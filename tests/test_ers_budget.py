from abraxas.ers import Budget, DeterministicScheduler
from abraxas.ers.bindings import bind_callable


def test_ers_budget_skips_when_exhausted():
    s = DeterministicScheduler()

    def f1(ctx): return 1
    def f2(ctx): return 2

    s.add(bind_callable(name="t1", lane="forecast", priority=0, cost_ops=2, fn=f1))
    s.add(bind_callable(name="t2", lane="forecast", priority=1, cost_ops=2, fn=f2))

    out = s.run_tick(
        tick=0,
        budget_forecast=Budget(ops=2, entropy=0),
        budget_shadow=Budget(ops=0, entropy=0),
        context={},
    )

    assert out["results"]["t1"].status in ("ok", "error")
    assert out["results"]["t2"].status == "skipped_budget"
