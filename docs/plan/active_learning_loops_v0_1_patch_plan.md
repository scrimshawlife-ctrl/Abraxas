# Active Learning Loops v0.1 — Patch Plan

**Status**: Active Development
**Version**: 0.1
**Created**: 2025-12-26
**Purpose**: Turn backtest failures into measured improvements via deterministic iteration

---

## Doctrine

**"Abraxas learns only from its own mistakes, without loosening determinism."**

**Active Learning Loop (ALL)** = Closed feedback system that:
1. **Detects** failures (MISS/ABSTAIN backtests)
2. **Analyzes** root causes (deterministic diagnosis)
3. **Proposes** bounded changes (one at a time)
4. **Validates** in sandbox (historical data only)
5. **Promotes** only if proven (backtest rent improves)

**No change is promoted unless it improves backtest rent in a sandbox.**

---

## The Loop (Deterministic)

```
Backtest MISS/ABSTAIN
         ↓
  Failure Analysis
         ↓
  Proposal Generation (bounded)
         ↓
  Sandbox Execution (historical only)
         ↓
  Promotion Gate (strict criteria)
         ↓
  Version Bump + Provenance Ledger
```

---

## Component 1: Failure Analysis Artifact

### Trigger

Auto-generated when:
- Backtest case returns `MISS`
- Backtest case returns `ABSTAIN` with `confidence: HIGH`

### Analysis Contents

```json
{
  "failure_id": "failure_<case_id>_<run_id>",
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
      "term": "digital doppelganger",
      "expected_count": 2,
      "actual_count": 0
    }
  ],
  "hit_falsifiers": [],
  "signal_gaps": {
    "missing_events": 47,  // Below min_signal_count
    "denied_signals": 12,  // Filtered by SMEM
    "missing_ledgers": ["oracle_delta.jsonl"]
  },
  "integrity_conditions": {
    "max_ssi": 0.45,
    "synthetic_saturation": 0.23
  },
  "temporal_gaps": {
    "tau_latency_mean": 127.3,  // ms
    "tau_phase_variance": 0.08
  },
  "hypothesis": "term_prediction_too_aggressive",
  "suggested_adjustments": [
    "relax_min_count_threshold",
    "extend_evaluation_window",
    "add_signal_source_diversity"
  ]
}
```

### Storage

- **JSON**: `out/reports/failure_<case_id>_<run_id>.json`
- **Markdown**: `out/reports/failure_<case_id>_<run_id>.md`
- **Ledger**: `out/learning_ledgers/failure_analyses.jsonl`

### Generation

```python
# abraxas/learning/failure_analyzer.py

def analyze_backtest_failure(
    case: BacktestCase,
    result: BacktestResult,
    events: List[SignalEvent],
    ledgers: Dict[str, List[Dict[str, Any]]]
) -> FailureAnalysis:
    """
    Deterministic failure analysis.

    No ML, no guessing. Just:
    - What was expected (triggers)
    - What was observed (events/ledgers)
    - What was missing (gap analysis)
    """
```

---

## Component 2: Proposal Generator

### Bounded Generation Rules

From a failure analysis, propose **exactly ONE** of:

1. **New Metric**
   - Example: Refined τ decay metric
   - Requires: Draft rent manifest
   - Must declare: Expected delta on failed case

2. **New Operator**
   - Example: Integrity-weighted MW nudge
   - Requires: Draft rent manifest + TER edges
   - Must declare: Expected delta on failed case

3. **Threshold Adjustment**
   - Example: Lower term_seen min_count from 2 to 1
   - Requires: Impact analysis on all cases using that threshold
   - Must declare: Expected improvement + regression risk

### Proposal Structure

```yaml
# sandbox/proposals/<proposal_id>/proposal.yaml

proposal_id: "proposal_001_relax_term_threshold"
created_at: "2025-12-26T13:00:00Z"
source_failure_id: "failure_case_term_emergence_001_run_20251220_120000"

proposal_type: "threshold_adjustment"  # or "new_metric" | "new_operator"

change_description: |
  Relax term_seen min_count threshold from 2 to 1 for term emergence cases.
  Analysis shows 0 occurrences but high related-term clustering suggests
  near-miss rather than true negative.

affected_components:
  - "data/backtests/cases/case_term_emergence_001.yaml"
  - "data/backtests/cases/case_term_emergence_002.yaml"

expected_delta:
  improved_cases: ["case_term_emergence_001"]
  regression_risk: ["case_term_emergence_003"]  # May now false-positive
  backtest_pass_rate_delta: +0.15  # From 0.67 to 0.82

rent_manifest_draft:  # If new metric/operator
  id: "relaxed_term_threshold_v1"
  kind: "threshold_adjustment"
  # ... rest of manifest

validation_plan:
  sandbox_cases: ["case_term_emergence_001", "case_term_emergence_002", "case_term_emergence_003"]
  protected_cases: []  # Cases that must not regress
  stabilization_runs: 3
```

### Generation Strategy

```python
# abraxas/learning/proposal_generator.py

def generate_proposal(failure: FailureAnalysis) -> Proposal:
    """
    Deterministic proposal generation.

    Rules:
    1. If unmet_trigger: consider threshold relaxation
    2. If signal_gaps.missing_events: consider window extension
    3. If integrity_conditions.max_ssi high: consider integrity filter
    4. If temporal_gaps large: consider tau adjustment

    Select ONE proposal with highest expected improvement.
    """
```

---

## Component 3: Sandbox Execution

### Sandbox Scope

**Historical snapshots only**:
- Run against past signal events (already stored)
- Run against past ledgers (immutable)
- No new predictions, no live data

### Execution Flow

1. **Load Proposal**
2. **Apply Change** (in-memory only)
3. **Re-run Backtest Cases** (affected + protected)
4. **Compare Before/After**:
   - Pass rate delta
   - Score delta per case
   - Cost delta (time/memory)
5. **Generate Sandbox Report**

### Sandbox Report Structure

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

### Storage

- `sandbox/proposals/<proposal_id>/sandbox_report_<run_id>.json`
- `out/learning_ledgers/sandbox_runs.jsonl`

---

## Component 4: Promotion Gate

### Strict Criteria

A proposal may be promoted **only if**:

1. **Improvement Threshold**
   - `pass_rate_delta >= declared_threshold` (e.g., ≥0.10 or 10%)
   - At least one failed case now passes

2. **No Regressions**
   - `regression_count == 0` on protected cases
   - No previously-passing case now fails

3. **Cost Bounds**
   - `time_ms_delta <= manifest.cost_model.time_ms_expected * 0.20` (≤20% increase)
   - `memory_kb_delta <= manifest.cost_model.memory_kb_expected * 0.20`

4. **Stabilization**
   - Proposal passes sandbox on N consecutive runs (default: 3)
   - No variance in results across runs

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

---

## Architecture

```
abraxas/
├── learning/
│   ├── __init__.py
│   ├── failure_analyzer.py      # Generate failure artifacts
│   ├── proposal_generator.py    # Bounded proposal generation
│   ├── sandbox_runner.py         # Execute proposals in sandbox
│   ├── promotion_gate.py         # Validate promotion criteria
│   └── schema.py                 # Pydantic models
├── cli/
│   └── learning.py               # CLI for learning loop
└── backtest/
    └── evaluator.py              # PATCH: Auto-trigger failure analysis

data/
└── sandbox/
    └── proposals/
        └── <proposal_id>/
            ├── proposal.yaml
            ├── sandbox_report_<run_id>.json
            └── rent_manifest_draft.yaml  # If new metric/operator

out/
├── reports/
│   └── failure_<case_id>_<run_id>.{json,md}
└── learning_ledgers/
    ├── failure_analyses.jsonl
    ├── sandbox_runs.jsonl
    └── promotions.jsonl

docs/
├── plan/
│   └── active_learning_loops_v0_1_patch_plan.md
└── specs/
    └── active_learning_loops_v0_1.md
```

---

## CLI Commands

### 1. Analyze Failures

```bash
python -m abraxas.cli.learning analyze-failures \
  --backtest-ledger out/backtest_ledgers/backtest_runs.jsonl \
  --min-confidence MED
```

Generates failure artifacts for all MISS/ABSTAIN results.

### 2. Generate Proposals

```bash
python -m abraxas.cli.learning generate-proposals \
  --failure-id failure_case_term_emergence_001_run_20251220_120000 \
  --strategy bounded
```

Creates ONE proposal from failure analysis.

### 3. Run Sandbox

```bash
python -m abraxas.cli.learning run-sandbox \
  --proposal-id proposal_001_relax_term_threshold \
  --runs 3
```

Executes proposal in sandbox N times for stabilization.

### 4. Promote

```bash
python -m abraxas.cli.learning promote \
  --proposal-id proposal_001 \
  --strict true
```

Validates criteria and promotes if eligible.

### 5. Full Loop (End-to-End)

```bash
python -m abraxas.cli.learning run-loop \
  --backtest-ledger out/backtest_ledgers/backtest_runs.jsonl \
  --auto-promote false
```

Runs full cycle: analyze → propose → sandbox → (manual review) → promote

---

## Determinism Guarantees

1. **Failure Analysis**: Deterministic gap detection, no inference
2. **Proposal Generation**: Rule-based selection, no randomness
3. **Sandbox Execution**: Historical data only, reproducible
4. **Promotion Gate**: Fixed criteria, boolean logic
5. **Ledger Recording**: Hash-chained, canonical JSON

**No ML. No vibes. Just disciplined iteration.**

---

## Integration with Existing Systems

### Backtest System

**MINIMAL PATCH** to `abraxas/backtest/evaluator.py`:

```python
def evaluate_case(case: BacktestCase) -> BacktestResult:
    # ... existing logic ...

    result = BacktestResult(...)

    # NEW: Auto-trigger failure analysis
    if result.status in [BacktestStatus.MISS] or \
       (result.status == BacktestStatus.ABSTAIN and result.confidence == Confidence.HIGH):
        from abraxas.learning.failure_analyzer import analyze_and_write_failure
        analyze_and_write_failure(case, result, events, ledgers)

    return result
```

### Rent Enforcement

No changes required. Promoted proposals create new manifests that go through standard rent-check.

---

## Constraints Met

✅ **Incremental Patch Only**: New modules + minimal backtest evaluator patch
✅ **Deterministic**: Rule-based, no ML, reproducible
✅ **Append-Only**: All ledgers hash-chained
✅ **No Rewrites**: Existing systems untouched
✅ **Bounded**: Exactly ONE proposal per failure

---

## What This Enables

### Before Active Learning:
- Backtest failures required manual diagnosis
- No systematic improvement process
- Changes made without validation
- No provenance linking failure → fix

### After Active Learning:
- **Failures automatically analyzed** with deterministic diagnosis
- **Proposals bounded and validated** in sandbox
- **Changes only promoted if proven** via backtest improvement
- **Full provenance** from failure → proposal → sandbox → promotion
- **Closed loop** - system learns from own mistakes

---

## Why This Matters

**Most systems learn from data they don't control.**
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

## Evolution Path

### v0.1 (This Patch)
- Failure analysis for MISS/ABSTAIN
- Bounded proposal generation (ONE per failure)
- Sandbox execution with before/after
- Promotion gate with strict criteria
- CLI for manual control

### v0.2 (Future)
- Multi-proposal comparison (A/B sandbox)
- Automatic promotion (if criteria met + auto-promote flag)
- Proposal chaining (failure → proposal → sandbox → new failure → refine)
- Cost-benefit optimization (maximize improvement / cost)

### v0.3 (Future)
- Meta-learning (which proposal strategies work best)
- Drift-aware proposals (detect regime shifts)
- Adversarial testing (stress test proposals)
- Continuous learning mode (monitor → analyze → propose → validate loop)

---

## Next After Active Learning

**Drift Detection v0.1**:
- Detect when pass rates decay over time
- Detect narrative regime shifts
- Auto-widen τ or tighten integrity gates
- Flag when world changed faster than model

At that point, Abraxas has:
- **Governance** (rent enforcement)
- **Validation** (backtest-as-rent)
- **Learning** (active learning loops)
- **Adaptation** (drift detection)

= **Symbolic intelligence with self-restraint**

---

**End of Patch Plan**
