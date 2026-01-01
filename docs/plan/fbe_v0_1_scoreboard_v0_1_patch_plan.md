# FBE v0.1 + Scoreboard v0.1 — Patch Plan

**Status**: Active Development
**Version**: 0.1
**Created**: 2025-12-26
**Purpose**: Add dynamic probabilistic forecasting (branches + probability mass) with accuracy tracking

---

## Doctrine

**"Forecasts are not predictions—they are disciplined probability distributions over future states, updated only by eligible evidence, scored ruthlessly against outcomes."**

**FBE (Forecast Branch Ensemble)** = Probabilistic forecasting system with:
1. **Branches**: Distinct future scenarios with probability mass
2. **Horizons**: 72H, 30D, 90D, 1Y, 2Y, 5Y
3. **Deterministic Updates**: Only via eligible influences (SMEM/SIW-filtered)
4. **Integrity Dampening**: SSI reduces update strength from synthetic sources

**Scoreboard** = Accuracy measurement system:
1. **Brier Score**: (p - y)² for probability vs outcome
2. **Log Score**: -log(p) for observed outcomes
3. **Calibration**: Do 70% predictions happen 70% of the time?

---

## Where FBE Fits in Pipeline

```
Existing Pipeline:
SRR → SMEM/SIW → Domain Ledgers → τ/MW/Integrity → Tier Compiler → Backtest

NEW Pipeline Addition:
SRR → SMEM/SIW → Domain Ledgers → τ/MW/Integrity
                                        ↓
                                   [FBE Update]  ← Influence Events
                                        ↓
                            Ensemble State (branches + p)
                                        ↓
                                Tier Compiler (adds forecasts)
                                        ↓
                                    Backtest
                                        ↓
                            [Scoreboard] ← Observed Outcomes
                                        ↓
                            Accuracy Ledger (Brier/Log/Calibration)
```

**Integration Points**:
1. **After Domain Ledgers**: FBE reads MW/τ/Integrity snapshots as context
2. **Influence Events**: FBE updates use influence events from TER coupling (if available)
3. **Tier Output**: Forecasts embedded in psychonaut/analyst/enterprise reports
4. **Backtest**: Extended to evaluate branch outcomes and score predictions
5. **Scoreboard**: Aggregates scores by horizon, tracks calibration

---

## Probability Update Mechanics

### Deterministic Update Formula

For each influence event targeting a branch:

```python
# 1. Compute delta mass proposal
delta_base = influence_strength * branch_sensitivity  # e.g., 0.05 * 0.8 = 0.04

# 2. Dampen by integrity (SSI-based)
if source_has_high_SSI:
    ssi_factor = clamp(integrity_snapshot["SSI"], 0, 1)
    sensitivity = branch.manipulation_exposure.get("SSI_sensitivity", 0.5)
    damping = 1 - (ssi_factor * sensitivity)
    delta = delta_base * damping
else:
    delta = delta_base

# 3. Apply bounded delta
branch.p_new = clamp(branch.p_old + delta, 0, 1)

# 4. Renormalize all branches so sum(p) = 1.0
total = sum(b.p_new for b in branches)
for b in branches:
    b.p = b.p_new / total

# 5. Update confidence bands
band_width = base_band * (1 - evidence_quality)  # More evidence = tighter bands
branch.p_min = max(0, branch.p - band_width)
branch.p_max = min(1, branch.p + band_width)
```

**Constraints**:
- All deltas bounded: `|delta| <= max_delta_per_update` (e.g., 0.15)
- Renormalization preserves probability axioms
- No ML, no randomness—pure deterministic arithmetic
- Ledger records before/after for full auditability

### Influence Event Mapping

Mapping from influence targets to branch updates (conservative defaults):

| Influence Target | Affects Branch | Delta Direction |
|-----------------|----------------|-----------------|
| `MRI_push` | "shock", "base" | +0.05 (increase urgency) |
| `trust_surface_down` | "integrity-collapse" | +0.08 |
| `IRI_damp` | "conservative" | +0.06, "shock" -0.06 |
| `tau_latency_up` | ALL | Reduce delta strength by 0.5x |
| `evidence_pack` | target branch | +0.10 (strong evidence) |

**Integrity Dampening Example**:
```
Influence: MRI_push targeting "shock" branch (delta_base = +0.05)
SSI = 0.8 (high synthetic content)
Branch SSI_sensitivity = 0.7

damping = 1 - (0.8 * 0.7) = 1 - 0.56 = 0.44
delta_actual = 0.05 * 0.44 = 0.022

Result: Update is reduced by 56% due to integrity concerns
```

---

## What "Accuracy" Means

### Brier Score

**Formula**: `Brier = (p - y)²` where:
- `p` = predicted probability for outcome
- `y` = observed outcome (1 if occurred, 0 if not)

**Range**: [0, 1], lower is better
- Perfect forecast: 0.0
- Worst forecast: 1.0

**Example**:
```
Branch: "deepfake_spike_72h"
Predicted: p = 0.70
Observed: Spike occurred (y = 1)
Brier = (0.70 - 1)² = 0.09

Alternative:
Predicted: p = 0.30
Observed: No spike (y = 0)
Brier = (0.30 - 0)² = 0.09
```

### Log Score

**Formula**: `LogScore = -log(p)` where:
- `p` = probability assigned to observed outcome
- Use natural log (ln)

**Range**: [0, ∞], lower is better
- Perfect forecast (p=1): 0.0
- Terrible forecast (p→0): ∞

**Properties**:
- Heavily penalizes overconfidence (high p when wrong)
- Encourages well-calibrated probabilities

**Example**:
```
Branch: "propaganda_sustained_30d"
Predicted: p = 0.60 for "sustained"
Observed: Sustained (y = 1)
LogScore = -ln(0.60) = 0.51

Alternative (wrong):
Predicted: p = 0.20 for "sustained"
Observed: Sustained (y = 1)
LogScore = -ln(0.20) = 1.61 (worse!)
```

### Calibration Bins

**Question**: Do 70% predictions happen 70% of the time?

**Method**:
1. Group forecasts into probability bins (0-10%, 10-20%, ..., 90-100%)
2. For each bin, calculate actual outcome frequency
3. Compare predicted vs observed

**Example**:
```
Bin [60-70%]: 10 forecasts with avg p = 0.65
Observed outcomes: 7 out of 10 occurred
Observed frequency: 0.70
Calibration error: |0.65 - 0.70| = 0.05 (well-calibrated!)

Bin [80-90%]: 8 forecasts with avg p = 0.85
Observed outcomes: 5 out of 8 occurred
Observed frequency: 0.625
Calibration error: |0.85 - 0.625| = 0.225 (overconfident!)
```

**Perfect Calibration**: All bins have error ≈ 0

---

## Backtest Cases: Expansion for Branch Scoring

### Before (Backtest v0.1)

```yaml
case_id: "case_term_emergence_001"
triggers:
  any_of:
    - kind: "term_seen"
      params: {term: "deepfake", min_count: 2}
```

**Result**: HIT/MISS/ABSTAIN (binary evaluation)

### After (with FBE Integration)

```yaml
case_id: "case_branch_deepfake_spike_72h"

# Link to forecast branch
forecast_branch_ref:
  ensemble_id: "ensemble_deepfake_pollution_H72H_core_N1"
  branch_id: "branch_shock_deepfake_spike"
  predicted_p_at_ts: "2025-12-20T12:00:00Z"  # or "auto" for latest

# Same trigger evaluation as before
triggers:
  any_of:
    - kind: "term_seen"
      params: {term: "deepfake", min_count: 5}
    - kind: "index_threshold"
      params: {index: "SSI", gte: 0.7}

evaluation_window:
  start_ts: "2025-12-20T12:00:00Z"
  end_ts: "2025-12-23T12:00:00Z"  # 72h later
```

**Result**: HIT/MISS/ABSTAIN + **Scoring Contribution**:
```json
{
  "case_id": "case_branch_deepfake_spike_72h",
  "status": "HIT",
  "forecast_scoring": {
    "ensemble_id": "ensemble_deepfake_pollution_H72H_core_N1",
    "branch_id": "branch_shock_deepfake_spike",
    "predicted_p": 0.65,
    "observed": true,
    "brier_contribution": 0.1225,
    "log_contribution": 0.43
  }
}
```

### Scoreboard Aggregation

Backtest runs accumulate scoring contributions:

```json
{
  "score_id": "score_H72H_2025-12-26",
  "horizon": "H72H",
  "cases_scored": 15,
  "brier_avg": 0.18,
  "log_avg": 0.52,
  "calibration_bins": {
    "60-70%": {"predicted": 0.65, "observed": 0.70, "n": 10},
    "70-80%": {"predicted": 0.75, "observed": 0.72, "n": 8}
  },
  "coverage": {"hit": 12, "miss": 2, "abstain": 1},
  "abstain_rate": 0.067
}
```

---

## Horizon-Specific Semantics

| Horizon | Window | Branch Semantics | Trigger Granularity |
|---------|--------|------------------|---------------------|
| **H72H** | 72 hours | Event/spike forecasts | High: specific terms, indices |
| **H30D** | 30 days | Trend forecasts | Medium: term clusters, MW shifts |
| **H90D** | 90 days | Pattern forecasts | Medium: sustained trends |
| **H1Y** | 1 year | Regime forecasts | Low: structural shifts |
| **H2Y** | 2 years | Strategic forecasts | Low: institutional changes |
| **H5Y** | 5 years | Regime-like forecasts | Very low: paradigm shifts |

**5-Year Forecast Example**:
```yaml
ensemble_id: "ensemble_deepfake_pollution_H5Y_core_N1"
branches:
  - label: "conservative"
    p: 0.35
    description: "Current regulations hold; deepfakes remain detectable"
    triggers:
      - kind: "index_threshold"
        params: {index: "SSI", lte: 0.5}  # SSI stays low

  - label: "shock"
    p: 0.25
    description: "Deepfakes indistinguishable; trust collapse"
    triggers:
      - kind: "index_threshold"
        params: {index: "SSI", gte: 0.8}

  - label: "institutional-response"
    p: 0.40
    description: "Provenance infrastructure scales globally"
    triggers:
      - kind: "term_seen"
        params: {term: "content provenance", min_count: 1000}
```

**τ Window for 5Y**: 43,800 hours (5 years)
- Evaluation happens at 5-year mark
- Triggers check if conditions materialized during window
- Scoring uses p at forecast time vs observed outcome

---

## Why This Is Non-Commodity

### Standard Forecasting Platforms
- **Proprietary data**: Crowd wisdom from unknown sources
- **Opaque updates**: "Algorithm updated probabilities"
- **No provenance**: Can't trace why p changed
- **No integrity**: Vulnerable to manipulation
- **Generic**: Same system for sports, politics, markets

### Abraxas FBE
✅ **Local data only**: All signals from OSH batches (reproducible)
✅ **Deterministic updates**: Every p change traced to specific influence event
✅ **Full provenance**: Hash-chained ledgers from signal → influence → branch update
✅ **Integrity-aware**: SSI dampens updates from synthetic sources
✅ **Domain-specific**: Branches designed for information ecosystem dynamics
✅ **Replayable**: Full pipeline reproducible from ledgers
✅ **Backtested**: Every forecast scored against observed outcomes

**Audit Question**: "Why did p for 'deepfake_spike' go from 0.45 to 0.62?"

**Abraxas Answer**:
```
Branch Update Ledger Entry:
{
  "ts": "2025-12-20T14:00:00Z",
  "ensemble_id": "ensemble_deepfake_pollution_H72H_core_N1",
  "branch_id": "branch_shock_deepfake_spike",
  "p_before": 0.45,
  "p_after": 0.62,
  "delta_summary": {
    "influence_event_id": "ie_mri_push_run_20251220_140000",
    "influence_target": "MRI_push",
    "delta_base": 0.08,
    "ssi_damping": 0.85,  # SSI was 0.3 (low)
    "delta_applied": 0.068,
    "renormalization_factor": 1.02
  },
  "integrity_context": {
    "SSI": 0.3,
    "completeness": 0.85,
    "source": "OSH_batch_20251220_1200"
  },
  "prev_hash": "abc123...",
  "step_hash": "def456..."
}
```

**Standard Platform Answer**: "Market moved on new information."

---

## Architecture

```
abraxas/
├── forecast/
│   ├── __init__.py
│   ├── types.py              # Branch, EnsembleState, Horizon
│   ├── init.py               # default_ensemble_templates, init_ensemble_state
│   ├── update.py             # apply_influence_to_ensemble
│   ├── store.py              # load/save ensemble, ledger append
│   └── pipeline_step.py      # update_fbe_for_run
├── scoreboard/
│   ├── __init__.py
│   ├── types.py              # ForecastOutcome, ScoreResult
│   ├── scoring.py            # brier_score, log_score, calibration bins
│   └── ledger.py             # score ledger management

data/
├── forecast/
│   ├── topics_v0_1.yaml      # Topic configuration
│   └── ensembles/
│       └── <ensemble_id>.json  # Latest ensemble state (overwrite)
└── rent_manifests/
    └── metrics/
        ├── fbe_branch_ensemble.yaml
        └── scoreboard_accuracy.yaml

out/
├── forecast_ledgers/
│   └── branch_updates.jsonl  # Hash-chained branch probability updates
├── score_ledgers/
│   └── forecast_scores.jsonl  # Hash-chained accuracy scores
└── runs/<run_id>/
    ├── forecast/
    │   └── fbe_summary.json + .md
    └── scoreboard/
        └── score_summary.json + .md
```

---

## Integration Points

### 1. Tier Compiler

**Psychonaut** (`compiler/compile_psychonaut.py`):
```markdown
## Possible Futures (72h)

**Deepfake Pollution**
- Conservative (35%): Current detection holds
  - Changes mind if: SSI < 0.4
- Base (40%): Moderate increase in unverified content
  - Changes mind if: SSI 0.4-0.6
- Shock (25%): Detection overwhelmed, trust crisis
  - Changes mind if: SSI > 0.7, term "deepfake" seen 10+ times
```

**Analyst** (`compiler/compile_analyst.py`):
```markdown
| Topic | Branch | p | p_range | τ Window | Last Update |
|-------|--------|---|---------|----------|-------------|
| deepfake_pollution | conservative | 35% | 30-40% | 72h | MRI_damp (-0.05) |
| deepfake_pollution | shock | 25% | 20-30% | 72h | IRI_push (+0.03) |
```

**Enterprise** (`compiler/compile_enterprise.py`):
```markdown
## Risk-Weighted Forecast View

**High-Risk Branches (p > 15% AND severity > 0.7)**
- Deepfake Shock (25%, severity 0.9)
  - Triggers: SSI > 0.7, term cluster activation
  - Integrity note: 12% of signals filtered due to SSI > 0.6
  - Ledger anchor: branch_updates.jsonl@hash=def456...
```

### 2. Scheduler

**Updated `data/run_plans/daily_v0_1.yaml`**:
```yaml
steps:
  # ... existing steps (srr, smem, siw, tau, mw, integrity) ...

  - id: update_fbe
    enabled: true
    module: "abraxas.forecast.pipeline_step"
    function: "update_fbe_for_run"
    args:
      topics_config: "data/forecast/topics_v0_1.yaml"
      max_topics: 10

  - id: compile_tiers
    # ... existing ...

  - id: score_forecasts
    enabled: true
    module: "abraxas.scoreboard.pipeline_step"
    function: "score_forecasts_for_run"
    args:
      cases_dir: "data/backtests/cases"
      horizons: ["H72H", "H30D", "H90D", "H1Y", "H5Y"]
```

### 3. Backtest Evaluator

**Minimal patch to `abraxas/backtest/evaluator.py`**:
```python
def evaluate_case(case: BacktestCase, ...) -> BacktestResult:
    # ... existing trigger evaluation ...

    result = BacktestResult(...)

    # NEW: Branch scoring if forecast_branch_ref present
    if hasattr(case, 'forecast_branch_ref') and case.forecast_branch_ref:
        from abraxas.scoreboard.scoring import score_branch_outcome

        scoring = score_branch_outcome(
            ensemble_id=case.forecast_branch_ref.ensemble_id,
            branch_id=case.forecast_branch_ref.branch_id,
            predicted_p_at_ts=case.forecast_branch_ref.predicted_p_at_ts,
            observed=(result.status == BacktestStatus.HIT)
        )

        result.forecast_scoring = scoring

    return result
```

---

## Determinism Guarantees

1. **Ensemble Initialization**: Deterministic templates, hash-based IDs
2. **Probability Updates**: Pure arithmetic, no randomness
3. **Influence Mapping**: Fixed rules (documented in code)
4. **Integrity Dampening**: Deterministic formula (SSI × sensitivity)
5. **Renormalization**: Always preserves sum(p) = 1.0
6. **Scoring**: Exact mathematical formulas (Brier, log)
7. **Ledger Recording**: Hash-chained, canonical JSON

**No ML. No randomness. Fully replayable from ledgers.**

---

## Evolution Path

### v0.1 (This Patch)
✅ Branch ensemble with 3-7 branches per topic
✅ Deterministic probability updates via influence events
✅ SSI-based integrity dampening
✅ Brier + log scoring
✅ Calibration bin tracking
✅ Backtest integration for branch outcomes
✅ 6 horizons: H72H, H30D, H90D, H1Y, H2Y, H5Y

### v0.2 (Future)
- Semantic topic discovery (auto-generate ensembles from MW clusters)
- Branch splitting/merging based on evidence
- Multi-horizon consistency checks
- Ensemble comparison (A/B testing of branch structures)
- Correlation tracking across topics

### v0.3 (Future)
- Conditional forecasts ("If X happens, then p(Y) changes by...")
- Meta-forecasting (forecast accuracy of forecasts)
- Drift detection in calibration
- Active learning integration (failures → new branches)

---

## Constraints Met

✅ **Incremental Patch Only**: New modules, minimal changes to existing
✅ **Deterministic**: All updates rule-based, no ML
✅ **Append-Only Ledgers**: branch_updates.jsonl, forecast_scores.jsonl
✅ **No Network Calls**: All data from local OSH batches
✅ **Eligible Evidence Only**: Updates gated by SMEM/SIW
✅ **Integrity-Aware**: SSI dampens synthetic sources

---

**End of Patch Plan**
