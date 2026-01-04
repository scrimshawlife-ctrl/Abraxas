from abraxas.ers import Budget, DeterministicScheduler
from abraxas.ers.bindings import bind_callable


def test_ers_forecast_runs_before_shadow():
    s = DeterministicScheduler()
    order = []

    def forecast(ctx):
        order.append("forecast")
        return True

    def shadow(ctx):
        order.append("shadow")
        return True

    s.add(bind_callable(name="shadow_task", lane="shadow", priority=0, cost_ops=1, fn=shadow))
    s.add(bind_callable(name="forecast_task", lane="forecast", priority=9, cost_ops=1, fn=forecast))

    _ = s.run_tick(
        tick=0,
        budget_forecast=Budget(ops=10, entropy=0),
        budget_shadow=Budget(ops=10, entropy=0),
        context={},
    )

    assert order == ["forecast", "shadow"]
