# Backtest-as-Rent v0.1 — Specification

**Version**: 0.1
**Status**: Active
**Created**: 2025-12-26
**Purpose**: Make predictive claims provable via deterministic historical validation

---

## Doctrine

**"Predictive modules must demonstrate forecast accuracy."**

Backtest-as-Rent extends the rent enforcement system by requiring predictive components to:

1. **Make specific predictions** (timestamped forecast artifacts)
2. **Define success criteria** (deterministic triggers)
3. **Validate against history** (signal events + ledgers)
4. **Meet accuracy thresholds** (pass rate >= declared minimum)

**No backtest cases = No predictive rent claims.**

---

## Architecture

### System Components

```
Forecast (t=0)  →  Backtest Case  →  Evaluation  →  Ledger  →  Rent Check
```

1. **Forecast Artifact**: Prediction recorded in timestamped report
2. **Backtest Case**: YAML file defining validation criteria
3. **Evaluation Engine**: Deterministic trigger matching against events/ledgers
4. **Backtest Ledger**: Append-only hash-chained result log
5. **Rent Check**: Validates pass rate meets manifest threshold

---

## What Backtests Prove

### CAN Prove (Deterministic):
- Term emergence timing (if term appears in signal store)
- Index threshold crossings (if recorded in ledgers)
- MW/TAU shifts (if recorded in ledgers)
- Integrity vector scores (if computed and logged)

### CANNOT Prove (Requires External Truth):
- Correctness against web/external sources (no network calls)
- Subjective accuracy without ground truth signals
- Causality (only correlation with observed data)
- Generalization beyond observed corpus

### Guardrails Protect Integrity:
- **Insufficient signals** → ABSTAIN (prevents false confidence)
- **Missing ledgers** → UNKNOWN (can't verify claims)
- **High integrity risk** → ABSTAIN (may be observing noise)

---

## Backtest Case Structure

### Required Fields

```yaml
case_id: str                    # Unique identifier
created_at: ISO8601             # Case creation timestamp
description: str                # What this validates

forecast_ref:                   # Link to forecast
  run_id: str
  artifact_path: str
  tier: "psychonaut"|"analyst"|"enterprise"

evaluation_window:              # Time range for validation
  start_ts: ISO8601             # Usually forecast timestamp
  end_ts: ISO8601               # start + delta (e.g., 72h)

triggers:                       # Success conditions
  any_of: [TriggerSpec...]      # At least one must satisfy

scoring:                        # How to score results
  type: "binary"
  weights: {trigger: 1.0, falsifier: 1.0, abstain: 0.2}
```

### Optional Fields

```yaml
falsifiers:                     # Failure conditions
  any_of: [TriggerSpec...]

guardrails:                     # When to abstain
  min_signal_count: int
  min_evidence_completeness: float
  max_integrity_risk: float

provenance:                     # Data requirements
  required_ledgers: [paths...]
  required_sources: [labels...]
```

---

## Trigger Types

### 1. term_seen

**Purpose**: Validate term emergence predictions

**Parameters**:
```yaml
kind: "term_seen"
params:
  term: "digital doppelganger"
  min_count: 2
  source_filter: ["OSH"]  # Optional
```

**Evaluation**:
- Case-insensitive substring match
- Counts occurrences in signal event text
- Deterministic ordering by (timestamp, event_id)

---

### 2. mw_shift

**Purpose**: Validate MW ontology change predictions

**Parameters**:
```yaml
kind: "mw_shift"
params:
  min_shifts: 1
  threshold: 0.5  # Minimum shift magnitude
```

**Evaluation**:
- Queries oracle_delta ledger for mw_shifts entries
- Counts shifts above threshold
- Requires oracle_delta ledger in time window

---

### 3. tau_shift

**Purpose**: Validate temporal alignment change predictions

**Parameters**:
```yaml
kind: "tau_shift"
params:
  min_velocity_delta: 0.1
```

**Evaluation**:
- Queries TAU ledger for velocity/phase changes
- Counts updates exceeding delta threshold
- Requires tau_ledger in time window

---

### 4. integrity_vector

**Purpose**: Validate integrity risk predictions

**Parameters**:
```yaml
kind: "integrity_vector"
params:
  vector: "Authority Deepfake"
  min_score: 0.6
```

**Evaluation**:
- Queries integrity ledger for vector scores
- Checks if any score >= min_score
- Requires integrity_ledger in time window

---

### 5. index_threshold

**Purpose**: Validate index crossing predictions

**Parameters**:
```yaml
kind: "index_threshold"
params:
  index: "SSI"
  gte: 0.7  # Greater-than-or-equal
```

**Evaluation**:
- Queries integrity ledger for index values
- Checks if any value crosses threshold
- Supports `gte` and `lte` thresholds

---

## Evaluation Status

### HIT
- At least one trigger satisfied (if `any_of`)
- All triggers satisfied (if `all_of`)
- No falsifiers satisfied
- Score: weights["trigger"] (default: 1.0)

### MISS
- No triggers satisfied, OR
- At least one falsifier satisfied
- Score: 0.0

### ABSTAIN
- Insufficient signal count
- Integrity risk too high
- Score: weights["abstain"] (default: 0.2)

### UNKNOWN
- Required ledgers missing
- Evidence completeness below threshold
- Score: 0.0

---

## Rent Integration

### Manifest Declaration

```yaml
# data/rent_manifests/metrics/predictive_analyzer.yaml

id: "predictive_term_analyzer"
kind: "metric"
domain: "MW"
description: "Predicts term emergence from MW signal patterns"

rent_claim:
  improves: ["prediction_accuracy", "term_discovery"]
  measurable_by: ["backtest_pass_rate"]
  thresholds:
    backtest_pass_rate_min: 0.70  # 70% of cases must HIT

proof:
  tests: ["tests/test_analyzer.py::test_accuracy"]
  golden_files: []
  ledgers_touched: ["out/temporal_ledgers/oracle_delta.jsonl"]
  backtest_cases:
    - "case_term_emergence_doppelganger_001"
    - "case_term_emergence_synthetic_001"
```

### Rent Check Execution

```bash
python -m abraxas.cli.rent_check --strict true
```

**Check Flow**:
1. Load manifest
2. Check if `backtest_pass_rate_min` in thresholds
3. If yes, load `backtest_cases` from proof
4. Query backtest ledger for latest results
5. Compute pass rate: hits / total
6. Fail if pass_rate < threshold

---

## Workflow

### 1. Make Prediction

Run Abraxas forecast:
```bash
python -m abraxas.cli.abx_run_v1_4 --tier enterprise
```

Produces: `out/runs/<run_id>/reports/enterprise.json`

### 2. Create Backtest Case

Copy template:
```bash
cp data/backtests/cases/bootstrap_term_emergence.yaml \
   data/backtests/cases/case_my_prediction_001.yaml
```

Update:
- `case_id`: Unique identifier
- `forecast_ref.run_id`: Your run ID
- `forecast_ref.artifact_path`: Path to forecast
- `evaluation_window`: Forecast time + delta
- `triggers`: What you predicted

### 3. Wait for Evaluation Window

Signal events and ledgers accumulate during window.

### 4. Run Backtest

```bash
python -m abraxas.cli.backtest --cases data/backtests/cases
```

Produces:
- `out/reports/backtest_<run_id>.{json,md}`
- Updates `out/backtest_ledgers/backtest_runs.jsonl`

### 5. Verify Rent

```bash
python -m abraxas.cli.rent_check --strict true
```

Checks backtest pass rate against manifest threshold.

---

## Determinism Guarantees

1. **Event Ordering**: Stable sort by (timestamp, event_id)
2. **Trigger Evaluation**: Exact string matching (case-insensitive), no fuzzy NLP
3. **Ledger Queries**: Time-range filtered, deterministic ordering
4. **Scoring**: Fixed weights, no probabilistic components
5. **Hash Chaining**: Canonical JSON hashing for ledger integrity

Given the same events + ledgers, evaluation produces identical results.

---

## Example: Complete Workflow

### Forecast Artifact

```json
// out/runs/run_20251220_120000/reports/enterprise.json
{
  "run_id": "run_20251220_120000",
  "tier": "enterprise",
  "timestamp": "2025-12-20T12:00:00Z",
  "predictions": [
    {
      "type": "term_emergence",
      "term": "digital doppelganger",
      "confidence": 0.78,
      "window": "72h"
    }
  ]
}
```

### Backtest Case

```yaml
# data/backtests/cases/case_doppelganger_001.yaml
case_id: "case_term_emergence_doppelganger_001"
created_at: "2025-12-20T12:00:00Z"
description: "Validate 'digital doppelganger' emergence prediction"

forecast_ref:
  run_id: "run_20251220_120000"
  artifact_path: "out/runs/run_20251220_120000/reports/enterprise.json"
  tier: "enterprise"

evaluation_window:
  start_ts: "2025-12-20T12:00:00Z"
  end_ts: "2025-12-23T12:00:00Z"  # 72h window

triggers:
  any_of:
    - kind: "term_seen"
      params:
        term: "digital doppelganger"
        min_count: 2

guardrails:
  min_signal_count: 10

scoring:
  type: "binary"
  weights:
    trigger: 1.0
```

### Backtest Result

```json
// out/reports/backtest_20251226_130000.json
{
  "backtest_run_id": "backtest_20251226_130000",
  "results": [
    {
      "case_id": "case_term_emergence_doppelganger_001",
      "status": "HIT",
      "score": 1.0,
      "confidence": "HIGH",
      "satisfied_triggers": ["term_seen_3"],
      "notes": [
        "Found 'digital doppelganger' 3 times (required: 2)"
      ],
      "provenance": {
        "events_examined": 47,
        "ledgers_loaded": ["oracle_delta"]
      }
    }
  ]
}
```

### Rent Manifest

```yaml
# data/rent_manifests/metrics/term_predictor.yaml
id: "enterprise_term_predictor"
rent_claim:
  thresholds:
    backtest_pass_rate_min: 0.70

proof:
  backtest_cases:
    - "case_term_emergence_doppelganger_001"
```

### Rent Check Result

```
============================================================
RENT ENFORCEMENT REPORT
============================================================
Manifests checked: 1
Total checks run: 7
Status: PASSED ✓

[enterprise_term_predictor] backtest_threshold: PASSED
  Pass rate: 100.00% (1/1 cases)
============================================================
```

---

## Evolution Path

### v0.1 (Current)
- Basic trigger types (term_seen, index_threshold, mw_shift, tau_shift, integrity_vector)
- Binary scoring (HIT/MISS/ABSTAIN/UNKNOWN)
- Guardrails (min_signal_count, min_evidence_completeness, max_integrity_risk)
- Hash-chained ledger
- Rent integration

### v0.2 (Future)
- Graded scoring (partial credit for near-misses)
- More trigger types (correlation shifts, cascade patterns)
- Multi-run aggregation (precision/recall across runs)
- Confidence calibration curves

### v0.3 (Future)
- Adversarial backtest cases (stress test predictions)
- Backtest drift detection (degradation over time)
- Backtest-as-metric (meta-evaluation of prediction systems)
- Automatic case generation from forecasts

---

## Related Documents

- [Backtest Case Schema](./backtest_case_schema.md) — Canonical YAML structure
- [Backtest-as-Rent Patch Plan](../plan/backtest_as_rent_v0_1_patch_plan.md) — Implementation roadmap
- [Rent Enforcement v0.1](./rent_enforcement_v0_1.md) — Rent system specification

---

## Summary

Backtest-as-Rent v0.1 makes predictive claims provable via deterministic offline validation.

**Key Properties**:
- **Deterministic**: Same events → same results
- **Offline**: No network calls, local signal store only
- **Provable**: Hash-chained ledger provides audit trail
- **Integrity-aware**: Guardrails prevent false confidence
- **Non-commodity**: Unique to your signal corpus

**No backtest cases = No predictive rent claims.**

Forecasts must demonstrate accuracy against history.

---

**End of Specification**
