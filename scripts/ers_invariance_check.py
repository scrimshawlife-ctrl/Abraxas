"""
Local invariance check runner.

Usage:
  python -m scripts.ers_invariance_check
"""

from abraxas.ers import Budget, DeterministicScheduler
from abraxas.ers.bindings import bind_callable
from abraxas.ers.invariance import dozen_run_invariance_gate


def main() -> int:
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
    if not res.ok:
        print("ERS INVARIANCE: FAIL")
        print("expected:", res.expected_hash)
        print("hashes:", res.hashes)
        print("first mismatch run:", res.first_mismatch_index)
        print("divergence:", res.divergence)
        return 1

    print("ERS INVARIANCE: PASS")
    print("hash:", res.expected_hash)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
