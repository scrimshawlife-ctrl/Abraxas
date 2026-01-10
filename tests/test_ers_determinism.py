from abraxas.ers import Budget, DeterministicScheduler
from abraxas.ers.bindings import bind_callable


def test_ers_deterministic_order_and_trace():
    s1 = DeterministicScheduler()
    s2 = DeterministicScheduler()

    def a(ctx): return "A"
    def b(ctx): return "B"
    def c(ctx): return "C"

    # Add in different insertion patterns but enforce stable key ordering by (lane, priority, name).
    s1.add(bind_callable(name="b", lane="forecast", priority=1, cost_ops=1, fn=b))
    s1.add(bind_callable(name="a", lane="forecast", priority=1, cost_ops=1, fn=a))
    s1.add(bind_callable(name="c", lane="shadow", priority=0, cost_ops=1, fn=c))

    s2.add(bind_callable(name="a", lane="forecast", priority=1, cost_ops=1, fn=a))
    s2.add(bind_callable(name="b", lane="forecast", priority=1, cost_ops=1, fn=b))
    s2.add(bind_callable(name="c", lane="shadow", priority=0, cost_ops=1, fn=c))

    out1 = s1.run_tick(
        tick=0,
        budget_forecast=Budget(ops=10, entropy=0),
        budget_shadow=Budget(ops=10, entropy=0),
        context={},
    )
    out2 = s2.run_tick(
        tick=0,
        budget_forecast=Budget(ops=10, entropy=0),
        budget_shadow=Budget(ops=10, entropy=0),
        context={},
    )

    trace1 = [(e.lane, e.task, e.status) for e in out1["trace"]]
    trace2 = [(e.lane, e.task, e.status) for e in out2["trace"]]
    assert trace1 == trace2
