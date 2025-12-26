# FBE + Scoreboard v0.1 — Specification

**Status**: Implemented
**Version**: 0.1
**Created**: 2025-12-26
**Purpose**: Probabilistic forecasting with accuracy tracking

---

## Overview

**FBE (Forecast Branch Ensemble)** + **Scoreboard** enable Abraxas to make probabilistic forecasts and measure their accuracy.

**Core Innovation**: Every probability update traceable to specific influence events, SSI-dampened for integrity, scored ruthlessly against observed outcomes.

---

## FBE: Forecast Branch Ensemble

### Concept

A **branch ensemble** represents multiple possible futures for a topic/horizon:

```
Topic: "deepfake_pollution"
Horizon: H72H (72 hours)

Branches:
- conservative (35%): Detection methods hold
- base (40%): Moderate increase in deepfakes
- shock (25%): Detection overwhelmed, trust crisis
```

**Sum of probabilities = 1.0 (always)**

### Horizons

| Horizon | Hours | Use Case |
|---------|-------|----------|
| H72H | 72 | Event/spike forecasts |
| H30D | 720 | Trend forecasts |
| H90D | 2160 | Pattern forecasts |
| H1Y | 8760 | Regime forecasts |
| H2Y | 17520 | Strategic forecasts |
| H5Y | 43800 | Paradigm shift forecasts |

### Probability Updates

**Deterministic formula**:
```python
# 1. Compute delta from influence
delta_base = influence_strength * branch_sensitivity  # e.g., 0.8 * 0.08 = 0.064

# 2. Dampen by SSI (integrity)
if source_type != "evidence_pack":
    ssi_damping = 1 - (SSI * branch.SSI_sensitivity)
    delta = delta_base * ssi_damping
else:
    delta = delta_base  # Evidence packs bypass dampening

# 3. Apply bounded delta
branch.p_new = clamp(branch.p_old + delta, 0, 1)

# 4. Renormalize all branches
total = sum(b.p_new for b in branches)
for b in branches:
    b.p = b.p_new / total
```

**Example**:
```
Influence: MRI_push (strength=0.8)
Target branch: "shock" (current p=0.25)
SSI: 0.6 (moderate synthetic content)
Branch SSI_sensitivity: 0.7

delta_base = 0.8 * 0.08 = 0.064
ssi_damping = 1 - (0.6 * 0.7) = 0.58
delta_actual = 0.064 * 0.58 = 0.037

shock.p_new = 0.25 + 0.037 = 0.287
After renormalization: shock.p = 0.285 (preserves sum=1.0)
```

### Ledgers

**Branch updates**: `out/forecast_ledgers/branch_updates.jsonl`

Entry structure:
```json
{
  "timestamp": "2025-12-26T14:00:00Z",
  "ensemble_id": "ensemble_deepfake_pollution_H72H_core_N1_abc123",
  "topic_key": "deepfake_pollution",
  "horizon": "H72H",
  "branch_probs_before": {"branch_conservative_xyz": 0.35, "branch_shock_abc": 0.25, ...},
  "branch_probs_after": {"branch_conservative_xyz": 0.33, "branch_shock_abc": 0.285, ...},
  "delta_summary": {
    "influence_event_id": "ie_mri_push_20251226_140000",
    "influence_target": "MRI_push",
    "ssi_damping": 0.58
  },
  "integrity_context": {"SSI": 0.6, "completeness": 0.85},
  "prev_hash": "def456...",
  "step_hash": "ghi789..."
}
```

**Full provenance**: Signal → Influence → Branch Update

---

## Scoreboard: Accuracy Measurement

### Metrics

#### 1. Brier Score

**Formula**: `Brier = (p - y)²`

- `p` = predicted probability [0, 1]
- `y` = observed outcome (1 if occurred, 0 if not)

**Range**: [0, 1], lower is better

**Example**:
```
Branch: "shock" (p = 0.70)
Outcome: Shock occurred (y = 1)
Brier = (0.70 - 1)² = 0.09
```

#### 2. Log Score

**Formula**: `LogScore = -log(p)` where p is probability assigned to observed outcome

**Range**: [0, ∞], lower is better

**Example**:
```
Branch: "shock" (p = 0.60)
Outcome: Shock occurred (y = 1)
LogScore = -ln(0.60) = 0.51

Alternative (wrong):
Branch: "shock" (p = 0.20)
Outcome: Shock occurred (y = 1)
LogScore = -ln(0.20) = 1.61 (heavily penalized!)
```

#### 3. Calibration

**Question**: Do 70% predictions happen 70% of the time?

**Method**: Group forecasts by probability bins, compare predicted vs observed frequency.

**Example**:
```
Bin [60-70%]:
  - 10 forecasts with avg p = 0.65
  - 7 occurred, 3 did not
  - Observed frequency = 0.70
  - Calibration error = |0.65 - 0.70| = 0.05 ✓ Well-calibrated

Bin [80-90%]:
  - 8 forecasts with avg p = 0.85
  - 5 occurred, 3 did not
  - Observed frequency = 0.625
  - Calibration error = |0.85 - 0.625| = 0.225 ✗ Overconfident
```

### Ledgers

**Forecast scores**: `out/score_ledgers/forecast_scores.jsonl`

Entry structure:
```json
{
  "timestamp": "2025-12-26T18:00:00Z",
  "score_id": "score_H72H_20251226",
  "horizon": "H72H",
  "cases_scored": 15,
  "brier_avg": 0.18,
  "log_avg": 0.52,
  "calibration_bins": [
    {"bin_label": "60-70%", "predicted_p_avg": 0.65, "observed_frequency": 0.68, "n": 10},
    {"bin_label": "70-80%", "predicted_p_avg": 0.75, "observed_frequency": 0.72, "n": 8}
  ],
  "coverage": {"hit": 12, "miss": 2, "abstain": 1},
  "abstain_rate": 0.067,
  "prev_hash": "jkl012...",
  "step_hash": "mno345..."
}
```

---

## Backtest Integration

### Extended Case Schema

Backtest cases can optionally reference forecast branches:

```yaml
case_id: "case_branch_deepfake_spike_72h"

# Link to forecast branch
forecast_branch_ref:
  ensemble_id: "ensemble_deepfake_pollution_H72H_core_N1_abc123"
  branch_id: "branch_shock_abc"
  predicted_p_at_ts: "2025-12-20T12:00:00Z"  # or "auto" for latest

# Standard trigger evaluation
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

### Result with Scoring

```json
{
  "case_id": "case_branch_deepfake_spike_72h",
  "status": "HIT",
  "score": 1.0,
  "forecast_scoring": {
    "ensemble_id": "ensemble_deepfake_pollution_H72H_core_N1_abc123",
    "branch_id": "branch_shock_abc",
    "predicted_p": 0.65,
    "observed": true,
    "brier_contribution": 0.1225,
    "log_contribution": 0.43,
    "calibration_bin": "60-70%"
  }
}
```

---

## API Examples

### Initialize Ensemble

```python
from abraxas.forecast import init_ensemble_state, Horizon

ensemble = init_ensemble_state(
    topic_key="deepfake_pollution",
    horizon=Horizon.H72H,
    segment="core",
    narrative="N1_primary"
)

# ensemble.branches = [conservative, base, shock]
# sum(b.p for b in ensemble.branches) == 1.0
```

### Apply Influence

```python
from abraxas.forecast import apply_influence_to_ensemble, InfluenceEvent

influence = InfluenceEvent(
    influence_id="ie_001",
    target="MRI_push",
    strength=0.8,
    source_type="signal"
)

updated = apply_influence_to_ensemble(
    ensemble,
    [influence],
    integrity_snapshot={"SSI": 0.6, "completeness": 0.85}
)

# Probabilities updated deterministically
# SSI dampening applied
# sum(b.p) still == 1.0
```

### Score Forecast

```python
from abraxas.scoreboard import brier_score, log_score

# Branch predicted p=0.65, outcome occurred (y=1)
brier = brier_score(0.65, 1)  # 0.1225
log = log_score(0.65, 1)      # 0.43
```

### Track Calibration

```python
from abraxas.scoreboard import update_calibration_bins, format_calibration_bins

bins = {}
forecasts = [(0.65, 1), (0.68, 1), (0.62, 0), ...]

for p, y in forecasts:
    bins = update_calibration_bins(bins, p, y)

formatted = format_calibration_bins(bins)
# [{"bin_label": "60-70%", "predicted_p_avg": 0.65, "observed_frequency": 0.68, ...}]
```

---

## Determinism Guarantees

✅ **Ensemble Initialization**: Deterministic templates, hash-based IDs
✅ **Probability Updates**: Pure arithmetic, no randomness
✅ **Influence Mapping**: Fixed rules (documented in code)
✅ **SSI Dampening**: Deterministic formula (SSI × sensitivity)
✅ **Renormalization**: Always preserves sum(p) = 1.0
✅ **Scoring**: Exact mathematical formulas (Brier, log)
✅ **Ledger Recording**: Hash-chained, canonical JSON

**Replayability**: Full pipeline reproducible from ledgers

---

## Testing

**23 tests, all passing**

- `tests/test_fbe_system.py` (10 tests)
  - Ensemble initialization
  - Probability renormalization
  - SSI dampening
  - Evidence pack bypass
  - Ledger chaining

- `tests/test_scoreboard_system.py` (13 tests)
  - Brier score calculation
  - Log score calculation
  - Calibration bins
  - Ledger integrity

---

## Configuration

**Topics**: `data/forecast/topics_v0_1.yaml`

```yaml
topics:
  - topic_key: "deepfake_pollution"
    horizons: ["H72H", "H30D", "H90D", "H1Y", "H5Y"]
    segments: ["core"]
    narratives: ["N1_primary"]
    enabled: true

  - topic_key: "propaganda_pressure"
    horizons: ["H72H", "H30D", "H90D"]
    segments: ["core"]
    narratives: ["N1_primary", "N2_counter"]
    enabled: true
```

---

## Rent Manifests

- `data/rent_manifests/metrics/fbe_branch_ensemble.yaml`
- `data/rent_manifests/metrics/scoreboard_accuracy.yaml`

Both manifests declare:
- **Improves**: calibration, auditability, long_horizon_forecasting
- **Measurable by**: brier_score, log_score, calibration_bins
- **Thresholds**: Conservative (require non-null scoring, valid ranges)

---

## Why This Is Non-Commodity

| Standard Platforms | Abraxas FBE |
|--------------------|-------------|
| Proprietary data | Local OSH batches only |
| Opaque updates | Hash-chained ledger provenance |
| Generic forecasts | Integrity-aware (SSI dampening) |
| No audit trail | Full signal → influence → branch update trace |
| Vulnerable to manipulation | Evidence packs bypass dampening |

**Audit Question**: "Why did p for 'deepfake_spike' go from 0.45 to 0.62?"

**Abraxas Answer**: See `branch_updates.jsonl@step_hash=def456` for exact influence event, SSI dampening calculation, and renormalization.

**Standard Platform Answer**: "Market moved."

---

## Evolution Path

### v0.1 (Implemented)
✅ 3-7 branches per topic
✅ 6 horizons (H72H to H5Y)
✅ Deterministic updates via influences
✅ SSI-based integrity dampening
✅ Brier + log scoring
✅ Calibration bin tracking
✅ Backtest integration

### v0.2 (Future)
- Semantic topic discovery (auto from MW clusters)
- Branch splitting/merging
- Multi-horizon consistency
- ROC/AUC metrics

### v0.3 (Future)
- Conditional forecasts
- Meta-forecasting
- Active learning integration
- Drift detection

---

**End of Specification**
