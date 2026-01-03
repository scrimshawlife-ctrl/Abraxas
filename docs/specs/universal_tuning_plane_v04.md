# Universal Tuning Plane v0.4 - Architecture Specification

**Version**: 0.4  
**Status**: Foundation Implemented  
**Date**: 2026-01-03

## Overview

The Universal Tuning Plane (UTP) v0.4 provides deterministic, evidence-based optimization across all Abraxas subsystems under unified budget constraints.

## Core Principle

**One optimization surface. All modules. Provable gains.**

## Architecture Layers

### Layer 1: Universal Budget Vector (UBV)

Cross-module resource measurement and enforcement:

```python
@dataclass
class UniversalBudgetVector:
    cpu_ms: BudgetDimension
    io_write_bytes: BudgetDimension
    io_read_bytes: BudgetDimension
    network_calls: BudgetDimension
    network_bytes: BudgetDimension
    latency_p95_ms: BudgetDimension
    storage_growth_bytes: BudgetDimension
    decodo_calls: BudgetDimension
    risk_score: BudgetDimension  # Determinism + drift proxy
    measurement_window: MeasurementWindow
    run_ids: list[str]
    ledger_hashes: list[str]
```

Each `BudgetDimension`:
- `measured`: Actual value from perf ledger
- `budget`: Soft limit (warning)
- `hard_limit`: Hard constraint (blocks promotion)

### Layer 2: Portfolio Tuning IR

Extends Performance Tuning Plane v0.1 to cover all subsystems:

```python
@dataclass
class PortfolioTuningIR:
    ir_version: "0.4"
    ubv: UniversalBudgetVector
    module_knobs: {
        "perf": PerfKnobs,        # Wraps PerfTuningIR knobs
        "acquisition": AcquisitionKnobs,
        "pipeline": PipelineKnobs,
        "atlas": AtlasKnobs
    }
    provenance: PortfolioProvenance
```

**Module Knobs**:

**A) perf** (from Performance Tuning Plane v0.1):
- `codec_policy`: CodecPolicy (default/hot/cold)
- `zstd_level_hot`: int (1-6)
- `zstd_level_cold`: int (3-22)
- `dict_enabled`: bool
- `dict_retrain_policy`: DictRetrainPolicy
- `hot_cache_days`: int
- `cold_archive_after_days`: int

**B) acquisition**:
- `batch_window_preferred`: list[BatchWindow] (ordered)
- `max_requests_per_run`: int
- `cache_only_fallback`: bool
- `decodo_policy`: DecododoPolicy

**C) pipeline**:
- `window_granularity`: list[Granularity] (weekly/daily)
- `retention_days_live_mode`: int
- `lazy_load_packets`: bool
- `max_in_memory_bytes`: int

**D) atlas** (export/render - pure operations, knobs affect batching only):
- `export_granularity`: Granularity
- `delta_sampling_policy`: DeltaSamplingPolicy | None

### Layer 3: Unified Objective Function

**Components**:
1. **Efficiency Score** (maximize):
   - Compression ratio
   - Cache hit rate
   - Deduplication rate

2. **Speed Score** (maximize):
   - Inverse of latency_p95
   - Inverse of cpu_ms

3. **Stability Score** (maximize):
   - Determinism pass rate
   - Drift-free rate
   - Budget satisfaction rate

4. **Violation Penalty** (minimize):
   - Hard constraint violations → -∞
   - Soft budget overruns → penalty

**Objective**:
```
score = efficiency * w1 + speed * w2 + stability * w3 - violations * w4
```

Weights are constants, fully logged.

### Layer 4: Portfolio Optimizer

**Algorithm**: Fixed-order grid search

**Steps**:
1. Enumerate knob combinations (bounded grid)
2. For each combination:
   - Predict UBV deltas (heuristic)
   - Compute projected objective
   - Check constraint satisfaction
3. Select best satisfying candidate
4. Return candidate + proofs

**Determinism guarantee**:
- Same measured UBV → same proposal
- No randomness, no ML
- Stable knob ordering

### Layer 5: Universal Rent Gates

**Promotion requires ALL**:

1. **No determinism failures** (12-run hash invariance where applicable)
2. **UBV budgets satisfied** (all dimensions within limits)
3. **Major rent gain** (at least ONE):
   - storage_growth reduced ≥ 10%, OR
   - network_calls reduced ≥ 15%, OR
   - latency_p95 improved ≥ 10%
4. **No major regressions**:
   - cpu_ms not worse than +15%
   - cache_hit_rate not worse
   - compression_ratio not worse
5. **Provenance chain valid** (all hashes match)

### Layer 6: Atomic Apply

**Mechanism**:
1. Write manifest: `.aal/tuning/portfolio/<date>/portfolio_tuning_<ts>_<run>.json`
2. Atomic pointer update: `.aal/tuning/portfolio/ACTIVE.json`
3. Subsystem readers:
   - Performance: reads `ACTIVE.module_knobs.perf`
   - Acquisition: reads `ACTIVE.module_knobs.acquisition`
   - Pipeline: reads `ACTIVE.module_knobs.pipeline`
   - Atlas: reads `ACTIVE.module_knobs.atlas`

**Canary mode**:
- Writes to `CANARY.json` instead of `ACTIVE.json`
- Runs N cycles in shadow
- Collects before/after UBV
- Promotion decision via rent gates

**Rollback**:
- Creates backup before changes
- Can revert to previous ACTIVE
- No partial states possible

### Layer 7: ABX-Runes (Portfolio Level)

**Five portfolio runes**:

**ϟ₂₉ UBV_SUMMARIZE**:
- Reads perf ledger + CAS stats + acquisition stats
- Computes measured UBV
- Returns: ubv, summary_hash, provenance

**ϟ₃₀ PORTFOLIO_TUNE_PROPOSE**:
- Inputs: measured UBV, run_ctx
- Runs portfolio optimizer
- Returns: candidate IR, predicted deltas, constraint proofs

**ϟ₃₁ PORTFOLIO_TUNE_CANARY**:
- Inputs: candidate IR, run_ctx
- Writes to CANARY.json
- Returns: canary_path, ir_hash

**ϟ₃₂ PORTFOLIO_TUNE_PROMOTE**:
- Inputs: ubv_before, ubv_after, run_ctx
- Checks universal rent gates
- If pass: promotes CANARY → ACTIVE
- Returns: promoted (bool), gate_results, rationale

**ϟ₃₃ PORTFOLIO_TUNE_REVOKE**:
- Inputs: run_ctx
- Reverts to previous ACTIVE
- Returns: revoked (bool), errors

## Integration with Existing Systems

### Performance Tuning Plane v0.1
- PerfTuningIR becomes `PortfolioTuningIR.module_knobs.perf`
- Perf rent gates become part of universal gates
- Backward compatible: compression router can read nested perf knobs

### ERS Scheduler
- UBV budgets map to ERS constraints
- Hard limits enforce ERS compliance
- Risk score tracks ERS violations

### Provenance System
- All UBV measurements include ledger hashes
- Portfolio IR includes provenance chain
- Rent gate decisions fully logged

## Workflow Example

```bash
# 1. Measure current state
ubv = summarize_ubv(window_hours=168)

# 2. Propose optimization
proposal = propose_portfolio_tuning(ubv_measured=ubv)

# 3. Deploy to canary
canary_result = apply_portfolio_canary(proposal.ir)

# 4. Run workload in canary mode
# (system runs with CANARY configuration)

# 5. Measure canary state
ubv_canary = summarize_ubv(window_hours=24, canary_mode=True)

# 6. Check rent gates
verdict = check_portfolio_gates(ubv_before=ubv, ubv_after=ubv_canary)

# 7. Promote if gates pass
if verdict.passed:
    promote_portfolio_tuning(ubv_before=ubv, ubv_after=ubv_canary)
else:
    revoke_portfolio_tuning()
```

## Implementation Status

### ✅ Completed (Foundation)
- Universal Budget Vector (UBV) schema
- Budget dimension tracking
- UBV violation detection
- Summary documentation

### 🚧 In Progress (Full Implementation)
- PortfolioTuningIR complete schema
- Portfolio optimizer (deterministic grid search)
- Portfolio objectives (unified scoring)
- Universal rent gates
- ABX-Runes (portfolio level)
- Subsystem wiring

### 📋 Planned (Future Extensions)
- Hot/cold cache enforcement
- Manifest-first discovery engine
- Multi-objective Pareto optimization
- Adaptive budget allocation
- Cross-run learning (deterministic)

## Design Principles

1. **Determinism First**: Same inputs → same outputs, always
2. **Evidence-Based**: All tuning from measured metrics, never guesses
3. **Canary-First**: Shadow deployment before production
4. **Rent-Gated**: Complexity must prove value
5. **Atomic Apply**: No partial configurations
6. **Reversible**: Always have rollback path
7. **Provenance-Tracked**: SHA-256 hashes everywhere
8. **ABX-Runes Only**: All operations via runes

## Future: Manifest-First Discovery

Next evolution: deterministic bulk endpoint discovery

**Problem**: Sites block scraping, but expose bulk datasets (sometimes)

**Solution**: Manifest-first search
1. Detect blocked endpoint
2. Search for manifest/catalog endpoints (bounded, deterministic)
3. Cache manifest → bulk endpoints
4. Future pulls use bulk API (never scrape again)

**Constraints**:
- Bounded search (max N requests)
- Deterministic search order
- Respect robots.txt
- Cache all discoveries
- Provenance-tracked

This becomes an `acquisition.manifest_discovery_policy` knob in PortfolioTuningIR.

---

**End of Specification**

*Universal Tuning Plane v0.4 makes performance optimization a provable, deterministic system property.*
