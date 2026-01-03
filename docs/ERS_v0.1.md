# ERS v0.2 — Execution & Resource Scheduler

Deterministic tick scheduler for Abraxas with trace hashing and invariance verification.

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

## Trace Hashing & Invariance Gate (v0.2)

ERS now includes deterministic trace canonicalization and SHA-256 hashing for drift detection:

```python
from abraxas.ers import trace_hash_sha256, dozen_run_invariance_gate

# Hash a single trace
trace = out["trace"]
hash_value = trace_hash_sha256(trace)

# Run 12-run invariance gate
def make_trace(run_index: int):
    # Your deterministic trace generation
    return scheduler.run_tick(...)["trace"]

result = dozen_run_invariance_gate(make_trace=make_trace, runs=12)
if result.ok:
    print(f"PASS: All traces identical (hash: {result.expected_hash})")
else:
    print(f"FAIL: Drift detected at run {result.first_mismatch_index}")
    print(f"Divergence: {result.divergence}")
```

### Runnable Invariance Check

```bash
python -m scripts.ers_invariance_check
```

Output:
```
ERS INVARIANCE: PASS
hash: ae7e4fe3526ad0e133d2f46de48f5941e5cf24382490e9d25088d8920decfd16
```

### What This Gives You

1. **Drift Detection**: Catch non-deterministic behavior before it ships
2. **Stabilization Windows**: 12-run gate makes stability measurable (not vibes)
3. **Canonical Hashing**: SHA-256 provenance for every execution trace
4. **Divergence Reports**: When drift occurs, get exact event index + diff
5. **Governance Latch**: Prevents silent drift from "harmless" edits

The invariance gate enforces determinism at the scheduler level - if your tasks or runtime introduce non-determinism, the gate **will** catch it.

## Next Steps

- **AAL-Viz Integration**: Ingest trace events for visualization (TraceEvent → TrendPack.v0)
- **Promotion Lifecycle**: Bind metric promotion to tick-based canary windows
- **Extended Stabilization**: Multi-tick windows with budget variation testing
