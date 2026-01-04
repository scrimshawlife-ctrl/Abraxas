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

### Canonical Runtime Tick Orchestrator (Recommended)

Use the canonical `abraxas.runtime.tick` orchestrator which handles ERS execution + artifact emission:

```python
from abraxas.runtime import abraxas_tick

# Define your pipeline functions
def run_signal(ctx):
    # Your signal extraction logic
    return {"signal": "detected"}

def run_compress(ctx):
    # Your compression logic
    return {"compressed": True}

def run_overlay(ctx):
    # Your overlay logic
    return {"overlay": "applied"}

# Optional: define shadow tasks
shadow_tasks = {
    "anagram": run_anagram_detector,
    "sei": run_sei_metric,
}

# Execute tick with automatic artifact emission
result = abraxas_tick(
    tick=0,
    run_id="RUN-001",
    mode="production",
    context={"input": "data"},
    artifacts_dir="./out",
    run_signal=run_signal,
    run_compress=run_compress,
    run_overlay=run_overlay,
    run_shadow_tasks=shadow_tasks,
)

# Artifacts automatically written with SHA-256 provenance:
# ./out/viz/RUN-001/000000.trendpack.json
# ./out/run_index/RUN-001/000000.runindex.json
# ./out/manifests/RUN-001.manifest.json

print(f"TrendPack: {result['artifacts']['trendpack']}")
print(f"TrendPack SHA-256: {result['artifacts']['trendpack_sha256']}")
print(f"RunIndex: {result['artifacts']['runindex']}")
print(f"RunIndex SHA-256: {result['artifacts']['runindex_sha256']}")
```

The runtime orchestrator owns:
- **ERS scheduler execution**: Deterministic task ordering
- **Artifact emission**: TrendPack + RunIndex with SHA-256 provenance
- **Manifest ledger**: Append-only per-run artifact tracking
- **Structured output**: Results + remaining budgets + artifact refs with hashes

### Direct ERS Usage (Advanced)

For custom integration, use ERS directly:

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

## Provenance-Sealed Artifacts

Every tick produces provenance-sealed artifacts with SHA-256 hashing:

### Artifact Types

**1. TrendPack (visualization format)**
```json
{
  "version": "0.1",
  "run_id": "RUN-001",
  "tick": 0,
  "provenance": {"engine": "abraxas", "mode": "production", "ers": "v0.2"},
  "timeline": [...],
  "budget": {...},
  "errors": [],
  "skipped": [],
  "stats": {...}
}
```

**2. RunIndex (artifact index)**
```json
{
  "schema": "RunIndex.v0",
  "run_id": "RUN-001",
  "tick": 0,
  "refs": {"trendpack": "/path/to/trendpack.json"},
  "hashes": {"trendpack_sha256": "a1b2c3..."},
  "tags": [],
  "provenance": {"engine": "abraxas", "mode": "production"}
}
```

**3. Manifest (per-run ledger)**
```json
{
  "schema": "Manifest.v0",
  "run_id": "RUN-001",
  "records": [
    {
      "tick": 0,
      "kind": "trendpack",
      "schema": "TrendPack.v0",
      "path": "/path/to/trendpack.json",
      "sha256": "a1b2c3...",
      "bytes": 1234,
      "extra": {"mode": "production", "ers": "v0.2"}
    },
    {
      "tick": 0,
      "kind": "runindex",
      "schema": "RunIndex.v0",
      "path": "/path/to/runindex.json",
      "sha256": "d4e5f6...",
      "bytes": 567,
      "extra": {"mode": "production"}
    }
  ]
}
```

### Directory Structure

```
artifacts_dir/
├── viz/
│   └── RUN-001/
│       ├── 000000.trendpack.json
│       ├── 000001.trendpack.json
│       └── ...
├── run_index/
│   └── RUN-001/
│       ├── 000000.runindex.json
│       ├── 000001.runindex.json
│       └── ...
└── manifests/
    └── RUN-001.manifest.json
```

### Provenance Guarantees

1. **Deterministic JSON**: Stable serialization (sorted keys, fixed separators)
2. **SHA-256 Hashing**: Every artifact includes provenance hash
3. **Append-Only Manifest**: Per-run ledger with deterministic sort
4. **Content Integrity**: TrendPack hash verifies content, RunIndex verifies references

### Usage

```python
from abraxas.runtime import abraxas_tick

result = abraxas_tick(...)

# Access artifacts with hashes
trendpack_path = result["artifacts"]["trendpack"]
trendpack_hash = result["artifacts"]["trendpack_sha256"]

# Verify artifact integrity
import hashlib, json
with open(trendpack_path, 'rb') as f:
    computed_hash = hashlib.sha256(f.read()).hexdigest()
assert computed_hash == trendpack_hash  # Integrity verified
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

## TrendPack Format (v0.1)

ERS traces are automatically converted to TrendPack format by the runtime orchestrator. TrendPack is a queryable, denormalized format optimized for visualization ingestion.

### Structure

```json
{
  "version": "0.1",
  "run_id": "RUN-001",
  "tick": 0,
  "provenance": {
    "engine": "abraxas",
    "mode": "production",
    "ers": "v0.2"
  },
  "timeline": [
    {
      "task": "oracle:signal",
      "lane": "forecast",
      "status": "ok",
      "cost_ops": 10,
      "cost_entropy": 0,
      "meta": {}
    }
  ],
  "budget": {
    "forecast": {
      "spent_ops": 30,
      "spent_entropy": 0
    },
    "shadow": {
      "spent_ops": 4,
      "spent_entropy": 0
    }
  },
  "errors": [],
  "skipped": [],
  "stats": {
    "total_events": 5,
    "forecast_events": 3,
    "shadow_events": 2,
    "errors": 0,
    "skipped": 0,
    "ok_events": 5
  }
}
```

### Use Cases

TrendPack supports:
- **Lane Timelines**: Visualize forecast vs shadow execution order
- **Budget Heat Maps**: Track `skipped_budget` events and resource exhaustion
- **Error Cluster Detection**: Isolate error events with lane/task context
- **Task Cost Analysis**: Aggregate ops/entropy costs per lane
- **Stats Summary**: Quick metrics for dashboard displays

### Viz Adapter (Pure Transformer)

The `abraxas.viz` module provides pure data transformations (no rendering logic):

```python
from abraxas.viz import ers_trace_to_trendpack

trendpack = ers_trace_to_trendpack(
    trace=scheduler_output["trace"],
    run_id="RUN-001",
    tick=0,
    provenance={"engine": "abraxas"},
)
```

This is Abraxas-owned emission, not external viz code. The transformer stays pure - it reshapes data without opinions about visualization frameworks.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│  External Viz Tools (AAL-Viz, Grafana, etc.)               │
│  ↑ Consumes TrendPack JSON artifacts                        │
└─────────────────────────────────────────────────────────────┘
                            ↑
┌─────────────────────────────────────────────────────────────┐
│  abraxas.runtime.tick — Canonical Orchestrator              │
│  • ERS execution                                            │
│  • Artifact emission (TrendPack)                            │
│  • Structured output                                        │
└─────────────────────────────────────────────────────────────┘
           ↑                              ↑
┌──────────────────────┐      ┌──────────────────────────────┐
│  abraxas.ers         │      │  abraxas.viz                 │
│  • DeterministicSch  │      │  • ers_trace_to_trendpack    │
│  • Trace hashing     │      │  (Pure transformer)          │
│  • Invariance gate   │      │                              │
└──────────────────────┘      └──────────────────────────────┘
```

**Strict Separation**:
- **ERS**: Pure scheduler (no IO, no artifacts)
- **Viz**: Pure transformer (no rendering, no opinions)
- **Runtime**: Orchestration + artifact emission (owns where/when)

## Next Steps

- **Artifact Manifest Hash**: SHA-256 hash of TrendPack + run index emission
- **Promotion Lifecycle**: Bind metric promotion to tick-based canary windows
- **Extended Stabilization**: Multi-tick windows with budget variation testing
- **Run Index**: Queryable index of all ticks for a run_id
