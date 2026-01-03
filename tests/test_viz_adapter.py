"""
Tests for abraxas.viz adapter (ERS trace → TrendPack transformation).
"""

from abraxas.ers import Budget, DeterministicScheduler
from abraxas.ers.bindings import bind_callable
from abraxas.viz import ers_trace_to_trendpack


def test_ers_trace_to_trendpack_structure():
    """Test that TrendPack has expected structure."""
    s = DeterministicScheduler()

    def f(ctx): return {"ok": True}
    def g(ctx): return {"shadow": True}

    s.add(bind_callable(name="oracle:signal", lane="forecast", priority=0, cost_ops=5, fn=f))
    s.add(bind_callable(name="shadow:sei", lane="shadow", priority=0, cost_ops=2, fn=g))

    out = s.run_tick(
        tick=0,
        budget_forecast=Budget(ops=10, entropy=0),
        budget_shadow=Budget(ops=10, entropy=0),
        context={},
    )

    trendpack = ers_trace_to_trendpack(
        trace=out["trace"],
        run_id="TEST-001",
        tick=0,
        provenance={"engine": "test"},
    )

    # Verify structure
    assert trendpack["version"] == "0.1"
    assert trendpack["run_id"] == "TEST-001"
    assert trendpack["tick"] == 0
    assert trendpack["provenance"]["engine"] == "test"
    assert "timeline" in trendpack
    assert "budget" in trendpack
    assert "errors" in trendpack
    assert "skipped" in trendpack
    assert "stats" in trendpack


def test_trendpack_timeline_ordering():
    """Test that timeline preserves execution order."""
    s = DeterministicScheduler()

    order = []

    def a(ctx):
        order.append("a")
        return True

    def b(ctx):
        order.append("b")
        return True

    s.add(bind_callable(name="task_a", lane="forecast", priority=0, cost_ops=1, fn=a))
    s.add(bind_callable(name="task_b", lane="forecast", priority=1, cost_ops=1, fn=b))

    out = s.run_tick(
        tick=0,
        budget_forecast=Budget(ops=10, entropy=0),
        budget_shadow=Budget(ops=10, entropy=0),
        context={},
    )

    trendpack = ers_trace_to_trendpack(trace=out["trace"], run_id="TEST-002", tick=0)

    # Timeline should match execution order
    assert len(trendpack["timeline"]) == 2
    assert trendpack["timeline"][0]["task"] == "task_a"
    assert trendpack["timeline"][1]["task"] == "task_b"


def test_trendpack_budget_tracking():
    """Test budget aggregation by lane."""
    s = DeterministicScheduler()

    def f(ctx): return True
    def g(ctx): return True

    s.add(bind_callable(name="forecast_task", lane="forecast", priority=0, cost_ops=5, cost_entropy=2, fn=f))
    s.add(bind_callable(name="shadow_task", lane="shadow", priority=0, cost_ops=3, cost_entropy=1, fn=g))

    out = s.run_tick(
        tick=0,
        budget_forecast=Budget(ops=10, entropy=5),
        budget_shadow=Budget(ops=10, entropy=5),
        context={},
    )

    trendpack = ers_trace_to_trendpack(trace=out["trace"], run_id="TEST-003", tick=0)

    # Budget should aggregate by lane
    assert trendpack["budget"]["forecast"]["spent_ops"] == 5
    assert trendpack["budget"]["forecast"]["spent_entropy"] == 2
    assert trendpack["budget"]["shadow"]["spent_ops"] == 3
    assert trendpack["budget"]["shadow"]["spent_entropy"] == 1


def test_trendpack_error_extraction():
    """Test error event extraction."""
    s = DeterministicScheduler()

    def error_task(ctx):
        raise ValueError("Test error")

    def ok_task(ctx):
        return True

    s.add(bind_callable(name="failing_task", lane="forecast", priority=0, cost_ops=1, fn=error_task))
    s.add(bind_callable(name="ok_task", lane="forecast", priority=1, cost_ops=1, fn=ok_task))

    out = s.run_tick(
        tick=0,
        budget_forecast=Budget(ops=10, entropy=0),
        budget_shadow=Budget(ops=10, entropy=0),
        context={},
    )

    trendpack = ers_trace_to_trendpack(trace=out["trace"], run_id="TEST-004", tick=0)

    # Should extract error events
    assert len(trendpack["errors"]) == 1
    assert trendpack["errors"][0]["task"] == "failing_task"
    assert trendpack["errors"][0]["lane"] == "forecast"
    assert trendpack["stats"]["errors"] == 1


def test_trendpack_skipped_budget_tracking():
    """Test skipped_budget event tracking."""
    s = DeterministicScheduler()

    def f(ctx): return True
    def g(ctx): return True

    s.add(bind_callable(name="task1", lane="forecast", priority=0, cost_ops=8, fn=f))
    s.add(bind_callable(name="task2", lane="forecast", priority=1, cost_ops=5, fn=g))

    out = s.run_tick(
        tick=0,
        budget_forecast=Budget(ops=10, entropy=0),
        budget_shadow=Budget(ops=10, entropy=0),
        context={},
    )

    trendpack = ers_trace_to_trendpack(trace=out["trace"], run_id="TEST-005", tick=0)

    # task2 should be skipped due to budget
    assert len(trendpack["skipped"]) == 1
    assert trendpack["skipped"][0]["task"] == "task2"
    assert trendpack["stats"]["skipped"] == 1


def test_trendpack_stats_accuracy():
    """Test stats aggregation accuracy."""
    s = DeterministicScheduler()

    def f(ctx): return True
    def g(ctx): return True
    def h(ctx): raise ValueError("error")

    s.add(bind_callable(name="forecast1", lane="forecast", priority=0, cost_ops=1, fn=f))
    s.add(bind_callable(name="forecast2", lane="forecast", priority=1, cost_ops=1, fn=h))
    s.add(bind_callable(name="shadow1", lane="shadow", priority=0, cost_ops=1, fn=g))

    out = s.run_tick(
        tick=0,
        budget_forecast=Budget(ops=10, entropy=0),
        budget_shadow=Budget(ops=10, entropy=0),
        context={},
    )

    trendpack = ers_trace_to_trendpack(trace=out["trace"], run_id="TEST-006", tick=0)

    # Stats should match
    assert trendpack["stats"]["total_events"] == 3
    assert trendpack["stats"]["forecast_events"] == 2
    assert trendpack["stats"]["shadow_events"] == 1
    assert trendpack["stats"]["errors"] == 1
    assert trendpack["stats"]["ok_events"] == 2
