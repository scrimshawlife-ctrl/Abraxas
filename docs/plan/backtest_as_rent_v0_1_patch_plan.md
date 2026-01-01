# Backtest-as-Rent v0.1 — Patch Plan

**Status**: Active Development
**Version**: 0.1
**Created**: 2025-12-26
**Purpose**: Make predictive claims provable via deterministic backtest evaluation

---

## What "Backtest-as-Rent" Means

**Doctrine**: Predictive modules must demonstrate forecast accuracy against historical data.

**Backtest Payment** = Proof that predictions:
1. **Were made** (timestamped forecast artifacts exist)
2. **Were specific** (triggers defined with deterministic criteria)
3. **Were validated** (outcomes observed in signal store + ledgers)
4. **Were accurate** (hit rate meets threshold)

**No backtest cases = No predictive claims.**

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Forecast Artifact (t=0)                     │
│  - Prediction made: "Term X will emerge within 72h"     │
│  - Stored: out/runs/<run_id>/reports/enterprise.json    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│             Backtest Case (YAML)                         │
│  - References forecast artifact                         │
│  - Defines triggers (term_seen, mw_shift, etc.)         │
│  - Defines evaluation window (start_ts → end_ts)        │
│  - Defines guardrails (min signal count, etc.)          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          Signal Store + Ledgers (t=0 to t+Δ)            │
│  - data/signals/events.jsonl                            │
│  - out/temporal_ledgers/*.jsonl                         │
│  - Indexed by timestamp                                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Backtest Evaluator                             │
│  - Loads case + forecast                                │
│  - Queries events/ledgers in window                     │
│  - Evaluates triggers deterministically                 │
│  - Applies guardrails (abstain if insufficient data)    │
│  - Returns: HIT|MISS|ABSTAIN|UNKNOWN                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          Backtest Ledger (Append-Only)                   │
│  - out/backtest_ledgers/backtest_runs.jsonl             │
│  - Records: case_id, status, score, confidence          │
│  - Hash-chained for integrity                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Rent Enforcement Check                         │
│  - Reads manifest.proof.backtest_cases                  │
│  - Computes pass rate from backtest ledger              │
│  - Fails if below threshold                             │
└─────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Backtest Case Schema

**Location**: `data/backtests/cases/*.yaml`

**Structure**:
```yaml
case_id: "case_term_emergence_001"
created_at: "2025-12-26T00:00:00Z"
description: "Verify term emergence prediction accuracy"

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

falsifiers:
  any_of:
    - kind: "integrity_vector"
      params:
        vector: "Authority Deepfake"
        min_score: 0.8  # If very high, prediction was noise

guardrails:
  min_signal_count: 10
  min_evidence_completeness: 0.7
  max_integrity_risk: 0.6

scoring:
  type: "binary"
  weights:
    trigger: 1.0
    falsifier: 1.0
    abstain: 0.2

provenance:
  required_ledgers: ["out/temporal_ledgers/oracle_delta.jsonl"]
  required_sources: ["OSH"]
  smem_version: "v0.3"
  siw_version: "v0.2"
```

**Trigger Types**:
- `term_seen`: Exact term match in events
- `mw_shift`: MW type shift detected in ledgers
- `tau_shift`: TAU velocity/phase change
- `integrity_vector`: Integrity vector score threshold
- `index_threshold`: Index value threshold (SSI, etc.)

### 2. Event Query Module

**File**: `abraxas/backtest/event_query.py`

**Functions**:
- `load_signal_events(time_min, time_max, source_labels=None)` → list[SignalEvent]
- `load_domain_ledgers(time_min, time_max)` → dict

**Data Sources**:
- `data/signals/events.jsonl` - Signal events indexed by timestamp
- `out/temporal_ledgers/*.jsonl` - Domain-specific ledgers

**Determinism**:
- Events sorted by (timestamp, event_id)
- Ledger entries sorted by timestamp
- No fuzzy matching

### 3. Trigger Evaluator

**File**: `abraxas/backtest/evaluator.py`

**Core Functions**:
- `evaluate_trigger(trigger: TriggerSpec, events, ledgers)` → TriggerResult
- `evaluate_case(case: BacktestCase)` → BacktestResult

**Trigger Evaluation**:

**A) term_seen**:
```python
# Search events.text for exact term (case-insensitive)
count = sum(1 for e in events if term.lower() in e.text.lower())
satisfied = count >= min_count
```

**B) mw_shift**:
```python
# Query oracle_delta ledger for mw_shifts
shifts = [e for e in ledger if e.get("mw_shifts", 0) > threshold]
satisfied = len(shifts) > 0
```

**C) integrity_vector**:
```python
# Query integrity ledger for vector scores
scores = [e["score"] for e in ledger if e["vector"] == target_vector]
satisfied = any(s >= min_score for s in scores)
```

**Guardrails**:
```python
if len(events) < guardrails.min_signal_count:
    return BacktestResult(status="ABSTAIN", confidence="LOW")
if integrity_risk > guardrails.max_integrity_risk:
    return BacktestResult(status="ABSTAIN", confidence="LOW")
```

**Result**:
```python
{
    "case_id": "case_001",
    "status": "HIT|MISS|ABSTAIN|UNKNOWN",
    "score": 1.0,  # binary or graded
    "satisfied_triggers": ["trigger_1"],
    "satisfied_falsifiers": [],
    "confidence": "HIGH|MED|LOW",
    "notes": ["Sufficient signal count", "All ledgers present"],
    "provenance": {
        "events_examined": 47,
        "ledgers_used": ["oracle_delta"],
        "event_hash": "abc123...",
        "ledger_hash": "def456..."
    }
}
```

### 4. Backtest Ledger

**File**: `out/backtest_ledgers/backtest_runs.jsonl`

**Entry Structure**:
```json
{
  "timestamp": "2025-12-26T13:00:00Z",
  "backtest_run_id": "backtest_20251226_130000",
  "case_id": "case_001",
  "status": "HIT",
  "score": 1.0,
  "confidence": "HIGH",
  "evaluation_window": {
    "start_ts": "2025-12-20T12:00:00Z",
    "end_ts": "2025-12-23T12:00:00Z"
  },
  "evidence_counts": {
    "events_examined": 47,
    "triggers_evaluated": 3,
    "falsifiers_evaluated": 1
  },
  "prev_hash": "abc123...",
  "step_hash": "def456..."
}
```

**Reports**:
- `out/reports/backtest_<run_id>.json` - Machine-readable
- `out/reports/backtest_<run_id>.md` - Human-readable

### 5. CLI Command

**File**: `abraxas/cli/backtest.py`

**Usage**:
```bash
python -m abraxas.cli.backtest \
  --cases data/backtests/cases \
  --time-max NOW \
  --emit-reports true \
  --strict false
```

**Flags**:
- `--cases PATH`: Directory containing case YAML files
- `--case-id ID`: Run specific case only
- `--since-days N`: Evaluate cases from last N days
- `--time-max TS`: Maximum timestamp for evaluation window
- `--strict BOOL`: Require all ledgers exist (default: false)
- `--write-ledgers BOOL`: Write to backtest ledger (default: true)
- `--emit-reports BOOL`: Generate MD/JSON reports (default: true)

**Output**:
```
============================================================
BACKTEST EVALUATION SUMMARY
============================================================
Cases Evaluated: 5
  HIT: 3 (60.0%)
  MISS: 1 (20.0%)
  ABSTAIN: 1 (20.0%)
  UNKNOWN: 0 (0.0%)

Top Failure Reasons:
  - Insufficient signal count: 1
  - Trigger not satisfied: 1

Reports written to: out/reports/backtest_20251226_130000.{json,md}
Ledger updated: out/backtest_ledgers/backtest_runs.jsonl
============================================================
```

### 6. Rent Integration

**File**: `abraxas/governance/rent_checks.py` (MINIMAL PATCH)

**New Check**:
```python
def check_backtest_threshold(manifest: Dict[str, Any], backtest_ledger_path: Path) -> List[str]:
    """
    Check that backtest pass rate meets threshold.

    Args:
        manifest: Rent manifest dict
        backtest_ledger_path: Path to backtest ledger

    Returns:
        List of error messages
    """
    errors = []

    # Check if backtest threshold declared
    thresholds = manifest.get("rent_claim", {}).get("thresholds", {})
    if "backtest_pass_rate_min" not in thresholds:
        return errors  # No backtest requirement

    min_pass_rate = thresholds["backtest_pass_rate_min"]

    # Check if backtest cases declared
    backtest_cases = manifest.get("proof", {}).get("backtest_cases", [])
    if not backtest_cases:
        errors.append("backtest_pass_rate_min declared but no backtest_cases in proof")
        return errors

    # Load backtest ledger
    if not backtest_ledger_path.exists():
        errors.append(f"Backtest ledger not found: {backtest_ledger_path}")
        return errors

    # Compute pass rate for declared cases
    results = load_backtest_results(backtest_ledger_path, backtest_cases)

    hits = sum(1 for r in results if r["status"] == "HIT")
    total = len(results)

    if total == 0:
        errors.append(f"No backtest results found for cases: {backtest_cases}")
        return errors

    pass_rate = hits / total

    if pass_rate < min_pass_rate:
        errors.append(
            f"Backtest pass rate {pass_rate:.2%} below threshold {min_pass_rate:.2%}"
        )

    return errors
```

**Schema Update**: `docs/specs/rent_manifest_schema.md`

Add optional field:
```yaml
proof:
  backtest_cases: ["case_001", "case_002"]  # Optional
```

### 7. Seed Backtest Cases

**Files**: `data/backtests/cases/bootstrap_*.yaml`

**Bootstrap Cases**:

1. **Term Emergence** (`bootstrap_term_emergence.yaml`)
   - Trigger: term_seen >= 2 within 72h
   - Template for term prediction validation

2. **Integrity Risk Escalation** (`bootstrap_integrity_risk.yaml`)
   - Trigger: SSI >= 0.7 OR vector score >= 0.6 within 7d
   - Template for integrity prediction validation

3. **MW Type Shift** (`bootstrap_mw_shift.yaml`)
   - Trigger: mw_shifts count >= 1 within 72h
   - Template for MW dynamics prediction

**Note**: Bootstrap cases use placeholder forecast refs. Replace with actual run_ids from your system.

---

## Integration with Rent Enforcement

**Manifest Example**:
```yaml
id: "predictive_term_analyzer"
kind: "metric"
domain: "MW"
description: "Predicts term emergence based on MW signal patterns"

# ... other fields ...

rent_claim:
  improves: ["prediction_accuracy", "term_discovery"]
  measurable_by: ["backtest_pass_rate"]
  thresholds:
    backtest_pass_rate_min: 0.70  # 70% hit rate required

proof:
  tests: ["tests/test_predictive_analyzer.py::test_accuracy"]
  golden_files: []
  ledgers_touched: ["out/temporal_ledgers/oracle_delta.jsonl"]
  backtest_cases: ["case_term_emergence_001", "case_term_emergence_002"]
```

**Rent Check Flow**:
1. Load manifest
2. Check if `backtest_pass_rate_min` in thresholds
3. If yes, load `backtest_cases` from proof
4. Read backtest ledger
5. Compute pass rate for those cases
6. Fail if below threshold

---

## Determinism Guarantees

1. **Event Ordering**: Stable sort by (timestamp, event_id)
2. **Trigger Evaluation**: Exact string matching (case-insensitive), no fuzzy NLP
3. **Ledger Queries**: Time-range filtered, deterministic ordering
4. **Scoring**: Fixed weights, no probabilistic components
5. **Hash Chaining**: Canonical JSON hashing for provenance

---

## What Backtests Can/Can't Prove

**CAN**:
- Term emergence timing
- Index threshold crossings
- Ledger-recorded events (MW shifts, TAU updates)
- Integrity vector scores

**CANNOT**:
- External web truth (no network calls)
- Subjective "accuracy" without ground truth
- Causality (only correlation)
- Generalization beyond observed window

**Abstain/Unknown Protect Integrity**:
- If signal count too low → ABSTAIN
- If required ledgers missing → UNKNOWN
- If integrity risk too high → ABSTAIN
- These prevent false confidence

---

## Evolution Path

### v0.1 (This Patch)
- Basic trigger types (term_seen, index_threshold)
- Binary scoring (HIT/MISS)
- Guardrails (min_signal_count)
- CLI + ledger + rent integration

### v0.2 (Future)
- Graded scoring (partial credit)
- More trigger types (correlation shifts, cascade patterns)
- Multi-run aggregation (precision/recall across runs)
- Backtest drift detection (degradation over time)

### v0.3 (Future)
- Adversarial cases (stress test predictions)
- Calibration curves (confidence vs accuracy)
- Backtest-as-metric (meta-evaluation)

---

## File Tree (New Files)

```
abraxas/
├── backtest/
│   ├── __init__.py
│   ├── event_query.py          # Load signal events + ledgers
│   ├── evaluator.py             # Trigger evaluation + scoring
│   └── schema.py                # Pydantic models for cases
├── cli/
│   └── backtest.py              # CLI command
└── governance/
    └── rent_checks.py           # PATCH: add check_backtest_threshold

data/
└── backtests/
    └── cases/
        ├── bootstrap_term_emergence.yaml
        ├── bootstrap_integrity_risk.yaml
        └── bootstrap_mw_shift.yaml

docs/
├── plan/
│   └── backtest_as_rent_v0_1_patch_plan.md
└── specs/
    ├── backtest_case_schema.md
    └── backtest_as_rent_v0_1.md

out/
├── backtest_ledgers/
│   └── backtest_runs.jsonl
└── reports/
    └── backtest_<run_id>.{json,md}

tests/
├── test_backtest_term_seen.py
├── test_backtest_integrity_vector.py
├── test_backtest_guardrails_abstain.py
├── test_backtest_ledger_chain.py
├── test_rent_check_backtest_threshold.py
└── golden/
    └── backtest/
        ├── term_seen_result.json
        └── integrity_vector_result.json
```

---

## Constraints Met

✅ **Incremental Patch Only**: New modules + minimal rent_checks.py patch
✅ **Deterministic**: Exact string matching, stable ordering, no ML
✅ **Append-only**: Backtest ledger is append-only with hash chaining
✅ **No network calls**: All data from local signal store + ledgers
✅ **Offline**: OSH batches already ingested and stored locally

---

## What This Buys Immediately

1. **Predictive claims become provable** - No hand-waving about "accuracy"
2. **Rent enforcement for forecasts** - Can't claim predictive power without backtest cases
3. **Non-commodity proof bundles** - Backtest results are unique to your corpus
4. **Integrity-aware evaluation** - Guardrails prevent false confidence
5. **Auditability** - Hash-chained backtest ledger provides provenance

---

## Next After Backtest-as-Rent

**Backtest Drift Detection**: Monitor backtest pass rates over time. If a previously-passing metric starts failing backtests, flag for investigation or deprecation.

**Adversarial Backtest Cases**: Create cases designed to fail if metric is overfitting or lacks robustness.

**Calibration Curves**: Plot confidence vs actual accuracy to ensure predictions are well-calibrated.

---

**End of Patch Plan**
