# ERS v0.1 — Execution & Resource Scheduler

Deterministic tick scheduler for Abraxas.

## Design Laws
- No wall-clock time.
- No randomness.
- Stable ordering:
  (lane_order, priority, name, insertion_index)
- Shadow lane is observation-only; forecast lane is primary.

## API
Create scheduler, add tasks, run ticks.

```python
from abraxas.ers import Budget, DeterministicScheduler
from abraxas.ers.bindings import bind_callable

s = DeterministicScheduler()
s.add(bind_callable(name="oracle:signal", lane="forecast", priority=0, cost_ops=5, fn=lambda ctx: {}))
s.add(bind_callable(name="shadow:sei", lane="shadow", priority=0, cost_ops=1, fn=lambda ctx: {}))

out = s.run_tick(
  tick=0,
  budget_forecast=Budget(ops=50, entropy=0),
  budget_shadow=Budget(ops=10, entropy=0),
  context={}
)
```

## Output
- `results`: TaskResult per task name
- `trace`: TraceEvent list suitable for later AAL-Viz ingestion
- `remaining`: remaining budgets per lane

## Integration with Abraxas

Replace your existing cycle/tick function with ERS-based execution:

```python
from abraxas.ers import Budget, DeterministicScheduler
from abraxas.ers.bindings import bind_callable

def abraxas_tick(context: dict, tick: int):
    s = DeterministicScheduler()

    # forecast lane (primary execution)
    s.add(bind_callable(name="oracle:signal", lane="forecast", priority=0, cost_ops=10, fn=run_signal))
    s.add(bind_callable(name="oracle:compress", lane="forecast", priority=1, cost_ops=10, fn=run_compress))
    s.add(bind_callable(name="oracle:overlay", lane="forecast", priority=2, cost_ops=10, fn=run_overlay))

    # shadow lane (observation-only)
    s.add(bind_callable(name="shadow:anagram", lane="shadow", priority=0, cost_ops=2, fn=run_anagram_shadow))
    s.add(bind_callable(name="shadow:sei", lane="shadow", priority=1, cost_ops=1, fn=run_sei_shadow))

    out = s.run_tick(
        tick=tick,
        budget_forecast=Budget(ops=50, entropy=0),
        budget_shadow=Budget(ops=20, entropy=0),
        context=context,
    )

    # Store trace as canonical execution artifact
    store_trace(out["trace"])

    return out
```

## Benefits

1. **Deterministic Execution**: Same inputs → same outputs, always
2. **Budget Enforcement**: Explicit resource limits prevent runaway computation
3. **Lane Separation**: Shadow metrics never block forecast operations
4. **Stable Ordering**: Tasks execute in predictable order regardless of insertion sequence
5. **Trace Provenance**: Every execution produces auditable trace suitable for AAL-Viz
6. **Stabilization Windows**: Run N ticks with fixed budgets → compare trace hashes for invariance

## Next Steps

- **Trace Hashing**: Add SHA-256 hashing of trace events for drift detection
- **12-Run Invariance Gate**: Stabilization windows measured in scheduled runs
- **AAL-Viz Integration**: Ingest trace events for visualization
- **Promotion Lifecycle**: Bind metric promotion to tick-based canary windows
