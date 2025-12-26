# Active Learning Loops v0.1 — Specification

**Status**: Implemented
**Version**: 0.1
**Created**: 2025-12-26
**Purpose**: Turn backtest failures into measured improvements via deterministic iteration

---

## Overview

**Active Learning Loops (ALL)** is a closed-loop learning system that transforms backtest failures (MISS/ABSTAIN) into deterministic improvement cycles.

**Core Doctrine**: "Abraxas learns only from its own mistakes, without loosening determinism."

**Non-Negotiable Rule**: No change is promoted unless it improves backtest rent in a sandbox.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  ACTIVE LEARNING LOOP                         │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Backtest MISS/ABSTAIN                                       │
│         ↓                                                     │
│  Failure Analysis (deterministic gap detection)              │
│         ↓                                                     │
│  Proposal Generation (bounded, ONE per failure)              │
│         ↓                                                     │
│  Sandbox Execution (historical data only)                    │
│         ↓                                                     │
│  Promotion Gate (strict criteria validation)                 │
│         ↓                                                     │
│  Version Bump + Provenance Ledger                            │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Component 1: Failure Analyzer

### Purpose
Auto-generate failure analysis artifacts when backtest returns MISS or high-confidence ABSTAIN.

### Trigger Conditions
- `BacktestResult.status == MISS`, OR
- `BacktestResult.status == ABSTAIN AND BacktestResult.confidence == HIGH`

### Analysis Strategy

**Deterministic gap detection only. No ML, no guessing.**

1. **Unmet Triggers**: Compare trigger expectations vs actual observations
   - For `term_seen`: Expected term count vs actual occurrences
   - For `mw_shift`: Expected MW shifts vs ledger entries
   - For `index_threshold`: Expected index values vs observed maxima

2. **Signal Gaps**: Quantify signal availability issues
   - `missing_events`: Events below `min_signal_count`
   - `denied_signals`: Signals filtered by SMEM/integrity gates
   - `missing_ledgers`: Required ledgers not found

3. **Integrity Conditions**: Snapshot of integrity metrics
   - `max_ssi`: Maximum SSI (Synthetic Source Index) observed
   - `synthetic_saturation`: Proportion of events flagged as synthetic

4. **Temporal Gaps**: Temporal dynamics analysis
   - `tau_latency_mean`: Mean τ latency in ms
   - `tau_phase_variance`: τ phase variance

5. **Hypothesis Generation**: Rule-based classification
   - `insufficient_signal_count`: Not enough events
   - `term_prediction_too_aggressive`: Term not observed
   - `mw_dynamics_underestimated`: MW shifts below threshold
   - `integrity_risk_exceeded`: SSI too high
   - `trigger_conditions_unmet`: Generic trigger failure

### Output Artifacts

**JSON**: `out/reports/failure_<case_id>_<run_id>.json`
```json
{
  "failure_id": "failure_case_term_emergence_001_run_20251220_120000",
  "case_id": "case_term_emergence_001",
  "run_id": "run_20251220_120000",
  "backtest_result": {
    "status": "MISS",
    "score": 0.0,
    "confidence": "HIGH"
  },
  "unmet_triggers": [
    {
      "kind": "term_seen",
      "expected": {"term": "digital doppelganger", "min_count": 2},
      "actual": {"count": 0}
    }
  ],
  "signal_gaps": {
    "missing_events": 0,
    "denied_signals": 12,
    "missing_ledgers": ["oracle_delta.jsonl"]
  },
  "integrity_conditions": {
    "max_ssi": 0.45,
    "synthetic_saturation": 0.23
  },
  "hypothesis": "term_prediction_too_aggressive",
  "suggested_adjustments": [
    "relax_min_count_threshold",
    "extend_evaluation_window"
  ]
}
```

**Markdown**: `out/reports/failure_<case_id>_<run_id>.md`
Human-readable summary of failure analysis.

**Ledger**: `out/learning_ledgers/failure_analyses.jsonl`
Hash-chained append-only ledger of all failure analyses.

---

## Component 2: Proposal Generator

### Purpose
Generate exactly ONE bounded proposal from a failure analysis.

### Proposal Types

1. **`threshold_adjustment`**: Relax or tighten an existing threshold
   - Example: Lower `term_seen` min_count from 2 to 1
   - Requires: Impact analysis on all affected cases

2. **`new_metric`** (v0.2): Propose a new metric
   - Example: Refined τ decay metric
   - Requires: Draft rent manifest

3. **`new_operator`** (v0.2): Propose a new operator
   - Example: Integrity-weighted MW nudge
   - Requires: Draft rent manifest + TER edges

### Generation Strategy

**Rule-based selection, no randomness.**

```python
if hypothesis == "term_prediction_too_aggressive":
    if actual_count == 0:
        # Term never appeared - may be too specific
        return ThresholdAdjustment("Consider term variants or longer window")
    elif actual_count < expected_count:
        # Near-miss - relax threshold
        return ThresholdAdjustment(f"Relax min_count from {expected} to {actual}")

elif hypothesis == "insufficient_signal_count":
    return ThresholdAdjustment("Extend evaluation window or relax min_signal_count")

elif hypothesis == "integrity_risk_exceeded":
    return ThresholdAdjustment("Adjust max_integrity_risk or add SSI filtering")
```

### Proposal Structure

**YAML**: `data/sandbox/proposals/<proposal_id>/proposal.yaml`
```yaml
proposal_id: "proposal_001_relax_term_threshold"
created_at: "2025-12-26T13:00:00Z"
source_failure_id: "failure_case_term_emergence_001_run_20251220_120000"

proposal_type: "threshold_adjustment"

change_description: |
  Relax term_seen min_count threshold from 2 to 1 for term emergence cases.
  Analysis shows 0 occurrences but high related-term clustering suggests
  near-miss rather than true negative.

affected_components:
  - "data/backtests/cases/case_term_emergence_001.yaml"

expected_delta:
  improved_cases: ["case_term_emergence_001"]
  regression_risk: []
  backtest_pass_rate_delta: +0.15  # From 0.67 to 0.82

validation_plan:
  sandbox_cases: ["case_term_emergence_001"]
  protected_cases: []
  stabilization_runs: 3
```

---

## Component 3: Sandbox Execution

### Purpose
Execute proposal in isolated sandbox against historical data only.

### Sandbox Scope

**Historical snapshots only**:
- Run against past signal events (already stored)
- Run against past ledgers (immutable)
- No new predictions, no live data
- No side effects - in-memory modification only

### Execution Flow

1. **Load Proposal** from `data/sandbox/proposals/<proposal_id>/`
2. **Run Baseline**: Evaluate affected cases WITHOUT proposal
3. **Run with Proposal**: Apply changes in-memory and re-evaluate
4. **Compare Results**: Calculate before/after delta
5. **Generate Report**: Write sandbox report with metrics

### Sandbox Report

**JSON**: `data/sandbox/proposals/<proposal_id>/sandbox_<run_id>.json`
```json
{
  "sandbox_run_id": "sandbox_proposal_001_20251226_140000",
  "proposal_id": "proposal_001_relax_term_threshold",
  "executed_at": "2025-12-26T14:00:00Z",

  "baseline": {
    "backtest_pass_rate": 0.67,
    "hit_count": 2,
    "miss_count": 1,
    "abstain_count": 0,
    "avg_score": 0.67
  },

  "proposal": {
    "backtest_pass_rate": 0.82,
    "hit_count": 3,
    "miss_count": 0,
    "abstain_count": 0,
    "avg_score": 0.82
  },

  "delta": {
    "pass_rate_delta": +0.15,
    "hit_count_delta": +1,
    "regression_count": 0
  },

  "cost_delta": {
    "time_ms_delta": +5.2,
    "memory_kb_delta": +128
  },

  "case_details": [
    {
      "case_id": "case_term_emergence_001",
      "baseline_status": "MISS",
      "proposal_status": "HIT",
      "improved": true
    }
  ],

  "promotion_eligible": true
}
```

---

## Component 4: Promotion Gate

### Purpose
Validate strict criteria and promote only proven improvements.

### Promotion Criteria

A proposal may be promoted **ONLY IF** all criteria are met:

1. **Improvement Threshold**
   - `pass_rate_delta >= 0.10` (≥10% improvement)
   - At least one failed case now passes

2. **No Regressions**
   - `regression_count == 0` on ALL cases
   - No previously-passing case now fails

3. **Cost Bounds**
   - `time_ms_delta <= 100ms` (or 20% of baseline)
   - `memory_kb_delta <= 1024KB` (or 20% of baseline)

4. **Stabilization**
   - Proposal passes sandbox on N consecutive runs (default: 3)
   - No variance in results across runs (variance < 5%)

### Promotion Actions

If all criteria met:

1. **Merge Change**
   - If threshold adjustment: Update backtest case YAML
   - If new metric/operator: Merge manifest to canonical registry

2. **Version Bump**
   - Increment version in affected components
   - Update provenance metadata

3. **Ledger Entry**
   ```json
   {
     "type": "promotion",
     "proposal_id": "proposal_001",
     "source_failure_id": "failure_case_term_emergence_001_run_20251220_120000",
     "promoted_at": "2025-12-26T15:00:00Z",
     "improvement_delta": {
       "pass_rate_delta": 0.15,
       "cost_delta": {"time_ms": 5.2, "memory_kb": 128}
     },
     "provenance_note": "Relaxed term_seen threshold based on failure analysis",
     "ledger_sha256": "abc123..."
   }
   ```

4. **Failure Resolution**
   - Link failure_id → proposal_id → promotion_id
   - Mark failure as "resolved"
   - Write `PROMOTED.json` marker to proposal directory

---

## CLI Commands

### 1. Analyze Failures

```bash
python -m abraxas.cli.learning analyze-failures \
  --backtest-ledger out/backtest_ledgers/backtest_runs.jsonl \
  --min-confidence MED \
  --output-dir out/reports
```

**Output**: Failure analysis artifacts for all MISS/ABSTAIN results

### 2. Generate Proposal

```bash
python -m abraxas.cli.learning generate-proposal \
  --failure-report out/reports/failure_case_term_emergence_001_run_20251220_120000.json \
  --strategy bounded
```

**Output**: Proposal YAML in `data/sandbox/proposals/<proposal_id>/`

### 3. Run Sandbox

```bash
python -m abraxas.cli.learning run-sandbox \
  --proposal-id proposal_001_relax_term_threshold \
  --runs 3
```

**Output**: Sandbox reports showing before/after comparison

### 4. Promote

```bash
python -m abraxas.cli.learning promote \
  --proposal-id proposal_001 \
  --strict true
```

**Output**: Promotion entry in `out/learning_ledgers/promotions.jsonl` (if eligible)

### 5. Full Loop

```bash
python -m abraxas.cli.learning run-loop \
  --backtest-ledger out/backtest_ledgers/backtest_runs.jsonl \
  --auto-promote false
```

**Output**: End-to-end cycle: analyze → propose → sandbox → (manual review) → promote

---

## Integration with Existing Systems

### Backtest System Integration

**Minimal patch to `abraxas/backtest/evaluator.py`:**

```python
def evaluate_case(
    case: BacktestCase,
    enable_learning: bool = False,  # NEW: opt-in learning
    run_id: str = "manual"
) -> BacktestResult:
    # ... existing evaluation logic ...

    result = BacktestResult(...)

    # NEW: Auto-trigger failure analysis
    if enable_learning:
        if result.status == BacktestStatus.MISS or \
           (result.status == BacktestStatus.ABSTAIN and result.confidence == Confidence.HIGH):
            try:
                from abraxas.learning.failure_analyzer import analyze_backtest_failure
                analyze_backtest_failure(case, result, events, ledgers)
            except Exception as e:
                result.notes.append(f"Warning: Failure analysis error: {e}")

    return result
```

**Usage**:
```python
# Without learning (default)
result = evaluate_case(case)

# With learning enabled
result = evaluate_case(case, enable_learning=True, run_id="run_20251226")
```

### Rent Enforcement

No changes required. Promoted proposals create new manifests that go through standard rent-check.

---

## Determinism Guarantees

1. **Failure Analysis**: Deterministic gap detection, no inference
2. **Proposal Generation**: Rule-based selection, no randomness
3. **Sandbox Execution**: Historical data only, reproducible
4. **Promotion Gate**: Fixed criteria, boolean logic
5. **Ledger Recording**: Hash-chained, canonical JSON

**No ML. No vibes. Just disciplined iteration.**

---

## Evolution Path

### v0.1 (This Release)
✅ Failure analysis for MISS/ABSTAIN
✅ Bounded proposal generation (ONE per failure)
✅ Sandbox execution with before/after
✅ Promotion gate with strict criteria
✅ CLI for manual control
✅ 8 passing tests

### v0.2 (Future)
- Multi-proposal comparison (A/B sandbox)
- Automatic promotion (if criteria met + auto-promote flag)
- Proposal chaining (failure → proposal → sandbox → new failure → refine)
- Cost-benefit optimization (maximize improvement / cost)
- New metric/operator proposal types

### v0.3 (Future)
- Meta-learning (which proposal strategies work best)
- Drift-aware proposals (detect regime shifts)
- Adversarial testing (stress test proposals)
- Continuous learning mode (monitor → analyze → propose → validate loop)

---

## What This Enables

### Before Active Learning
- Backtest failures required manual diagnosis
- No systematic improvement process
- Changes made without validation
- No provenance linking failure → fix

### After Active Learning
- **Failures automatically analyzed** with deterministic diagnosis
- **Proposals bounded and validated** in sandbox
- **Changes only promoted if proven** via backtest improvement
- **Full provenance** from failure → proposal → sandbox → promotion
- **Closed loop** - system learns from own mistakes

---

## Why This Matters

**Most systems learn from data they don't control:**
- External datasets
- Crowd labels
- Web scraping
- API calls

**Abraxas learns from its own, time-stamped spine:**
- Backtest ledger (what worked/didn't)
- Failure artifacts (why it didn't work)
- Sandbox results (what would fix it)
- Promotion ledger (what was deployed)

**This is self-restraint at scale.**

---

## Testing

**Test Suite**: `tests/test_learning_system.py`

8 comprehensive tests covering:
1. ✅ Failure analyzer creation
2. ✅ Unmet trigger identification
3. ✅ Signal gap analysis
4. ✅ Proposal generation for threshold adjustments
5. ✅ Sandbox proposal loading
6. ✅ Promotion criteria validation (passing case)
7. ✅ Promotion criteria validation (regression rejection)
8. ✅ Ledger hash chain integrity

**All tests passing.**

---

**End of Specification**
