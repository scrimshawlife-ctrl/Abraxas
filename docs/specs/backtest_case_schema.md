# Backtest Case Schema — Canonical Specification

**Version**: 0.1
**Status**: Canonical
**Created**: 2025-12-26
**Purpose**: Define structure of backtest cases for forecast validation

---

## Overview

A **Backtest Case** is a YAML file that defines how to validate a past forecast against observed events and ledger data.

Backtest cases enable deterministic, offline evaluation of predictive claims without requiring network access or external ground truth.

---

## File Format

**Location**: `data/backtests/cases/*.yaml`

**Naming Convention**: `<category>_<description>_<sequence>.yaml`
- Examples: `term_emergence_001.yaml`, `integrity_risk_escalation_001.yaml`

---

## Schema

```yaml
case_id: str                    # Unique identifier (e.g., "case_term_emergence_001")
created_at: ISO8601             # Case creation timestamp
description: str                # Human-readable description

forecast_ref:                   # Reference to forecast artifact
  run_id: str                   # Simulation run ID
  artifact_path: str            # Path to forecast artifact (e.g., out/runs/<run_id>/reports/enterprise.json)
  tier: str                     # "psychonaut" | "analyst" | "enterprise"

evaluation_window:              # Time window for evaluation
  start_ts: ISO8601             # Start timestamp (usually forecast timestamp)
  end_ts: ISO8601               # End timestamp (start + delta, e.g., 72h)

triggers:                       # Conditions that indicate "HIT"
  any_of: list[TriggerSpec]     # At least one must be satisfied
  all_of: list[TriggerSpec]     # All must be satisfied (optional)

falsifiers:                     # Conditions that indicate "MISS"
  any_of: list[TriggerSpec]     # At least one invalidates forecast (optional)

guardrails:                     # When to abstain or downweight
  min_signal_count: int         # Minimum events required
  min_evidence_completeness: float  # Minimum fraction of required ledgers present (0.0-1.0)
  max_integrity_risk: float     # Maximum SSI or integrity score tolerated

scoring:                        # How to score results
  type: str                     # "binary" | "graded"
  weights: dict                 # Weights for trigger/falsifier/abstain

provenance:                     # Required data sources
  required_ledgers: list[str]   # Ledger paths that must exist
  required_sources: list[str]   # Source labels required (e.g., ["OSH", "media"])
  smem_version: str             # SMEM version used for forecast
  siw_version: str              # SIW version used for forecast
```

---

## TriggerSpec

A `TriggerSpec` defines a deterministic condition to evaluate against events or ledgers.

```yaml
kind: str                       # Trigger type
params: dict                    # Type-specific parameters
```

### Trigger Types

#### 1. `term_seen`

**Purpose**: Check if a specific term appears in signal events.

**Parameters**:
```yaml
kind: "term_seen"
params:
  term: str                     # Exact term to search for (case-insensitive)
  min_count: int                # Minimum occurrences required
  source_filter: list[str]      # Optional: Filter by source labels (e.g., ["OSH"])
```

**Evaluation**:
```python
count = sum(1 for event in events
            if term.lower() in event.text.lower()
            and (not source_filter or event.source in source_filter))
satisfied = count >= min_count
```

**Example**:
```yaml
triggers:
  any_of:
    - kind: "term_seen"
      params:
        term: "digital doppelganger"
        min_count: 2
        source_filter: ["OSH"]
```

---

#### 2. `mw_shift`

**Purpose**: Check if MW type shifts occurred in oracle ledger.

**Parameters**:
```yaml
kind: "mw_shift"
params:
  min_shifts: int               # Minimum number of shifts required
  shift_type: str               # Optional: Specific shift type (e.g., "categorical", "intensity")
  threshold: float              # Optional: Minimum shift magnitude
```

**Evaluation**:
```python
shifts = [entry for entry in oracle_delta_ledger
          if entry.get("mw_shifts", 0) >= threshold]
satisfied = len(shifts) >= min_shifts
```

**Example**:
```yaml
triggers:
  any_of:
    - kind: "mw_shift"
      params:
        min_shifts: 1
        threshold: 0.5
```

---

#### 3. `tau_shift`

**Purpose**: Check if TAU velocity/phase changes occurred.

**Parameters**:
```yaml
kind: "tau_shift"
params:
  min_velocity_delta: float     # Minimum velocity change
  min_phase_delta: float        # Minimum phase change (optional)
```

**Evaluation**:
```python
tau_updates = [entry for entry in tau_ledger
               if abs(entry.get("velocity_delta", 0)) >= min_velocity_delta]
satisfied = len(tau_updates) > 0
```

**Example**:
```yaml
triggers:
  any_of:
    - kind: "tau_shift"
      params:
        min_velocity_delta: 0.1
```

---

#### 4. `integrity_vector`

**Purpose**: Check if integrity vector score exceeds threshold.

**Parameters**:
```yaml
kind: "integrity_vector"
params:
  vector: str                   # Vector name (e.g., "Authority Deepfake")
  min_score: float              # Minimum score required (0.0-1.0)
```

**Evaluation**:
```python
scores = [entry["score"] for entry in integrity_ledger
          if entry.get("vector") == vector]
satisfied = any(score >= min_score for score in scores)
```

**Example**:
```yaml
triggers:
  any_of:
    - kind: "integrity_vector"
      params:
        vector: "Authority Deepfake"
        min_score: 0.6
```

---

#### 5. `index_threshold`

**Purpose**: Check if an index (SSI, etc.) crosses threshold.

**Parameters**:
```yaml
kind: "index_threshold"
params:
  index: str                    # Index name (e.g., "SSI", "TDI")
  gte: float                    # Greater-than-or-equal threshold (optional)
  lte: float                    # Less-than-or-equal threshold (optional)
```

**Evaluation**:
```python
index_values = [entry[index] for entry in integrity_ledger
                if index in entry]
if gte is not None:
    satisfied = any(v >= gte for v in index_values)
if lte is not None:
    satisfied = any(v <= lte for v in index_values)
```

**Example**:
```yaml
triggers:
  any_of:
    - kind: "index_threshold"
      params:
        index: "SSI"
        gte: 0.7
```

---

## Guardrails

Guardrails prevent false confidence by requiring minimum evidence quality.

### `min_signal_count`

Minimum number of signal events in evaluation window.

```yaml
guardrails:
  min_signal_count: 10
```

**If violated**: Status → `ABSTAIN`, Confidence → `LOW`

### `min_evidence_completeness`

Minimum fraction of required ledgers that must exist.

```yaml
guardrails:
  min_evidence_completeness: 0.7  # At least 70% of ledgers must be present
```

**If violated**: Status → `ABSTAIN` or `UNKNOWN`

### `max_integrity_risk`

Maximum tolerable integrity risk (SSI or vector score).

```yaml
guardrails:
  max_integrity_risk: 0.6  # If SSI > 0.6, abstain
```

**If violated**: Status → `ABSTAIN`, Confidence → `LOW`

---

## Scoring

### Binary Scoring

```yaml
scoring:
  type: "binary"
  weights:
    trigger: 1.0      # Full credit if trigger satisfied
    falsifier: 1.0    # Full deduction if falsifier satisfied
    abstain: 0.2      # Partial credit for abstain (prevents gaming)
```

**Formula**:
```python
if status == "HIT":
    score = weights["trigger"]
elif status == "MISS":
    score = 0.0
elif status == "ABSTAIN":
    score = weights["abstain"]
else:  # UNKNOWN
    score = 0.0
```

### Graded Scoring (Future)

```yaml
scoring:
  type: "graded"
  weights:
    trigger: 1.0
    falsifier: -0.5
    confidence_multiplier: true
```

---

## Provenance

Tracks data sources required for evaluation.

```yaml
provenance:
  required_ledgers:
    - "out/temporal_ledgers/oracle_delta.jsonl"
    - "out/temporal_ledgers/integrity_ledger.jsonl"
  required_sources:
    - "OSH"
    - "media"
  smem_version: "v0.3"
  siw_version: "v0.2"
```

**Validation**:
- If any `required_ledgers` missing and `guardrails.min_evidence_completeness` not met → Status `UNKNOWN`
- Version mismatches logged in backtest result notes

---

## Example: Complete Backtest Case

```yaml
case_id: "case_term_emergence_doppelganger_001"
created_at: "2025-12-26T00:00:00Z"
description: "Validate prediction that 'digital doppelganger' term would emerge within 72 hours"

forecast_ref:
  run_id: "run_20251220_120000"
  artifact_path: "out/runs/run_20251220_120000/reports/enterprise.json"
  tier: "enterprise"

evaluation_window:
  start_ts: "2025-12-20T12:00:00Z"
  end_ts: "2025-12-23T12:00:00Z"  # 72-hour window

triggers:
  any_of:
    - kind: "term_seen"
      params:
        term: "digital doppelganger"
        min_count: 2
        source_filter: ["OSH"]

falsifiers:
  any_of:
    - kind: "integrity_vector"
      params:
        vector: "Authority Deepfake"
        min_score: 0.8  # High score suggests noise/manipulation

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
  required_ledgers:
    - "out/temporal_ledgers/oracle_delta.jsonl"
    - "out/temporal_ledgers/integrity_ledger.jsonl"
  required_sources: ["OSH"]
  smem_version: "v0.3"
  siw_version: "v0.2"
```

---

## Validation Rules

1. **case_id** must be unique across all cases
2. **evaluation_window.end_ts** must be > **start_ts**
3. **triggers** must have at least one of `any_of` or `all_of`
4. **forecast_ref.artifact_path** should exist (warning if missing)
5. **guardrails** values must be non-negative
6. **scoring.type** must be `"binary"` or `"graded"`
7. **trigger kinds** must be recognized types

---

## Determinism Guarantees

1. **Exact String Matching**: No fuzzy NLP, only case-insensitive substring match
2. **Stable Ordering**: Events sorted by (timestamp, event_id)
3. **No Randomness**: All thresholds and weights are fixed
4. **Reproducible**: Same events + ledgers → same result

---

## What Backtest Cases Can/Cannot Prove

### CAN Prove:
- Term emergence timing (if term appears in signal store)
- Index threshold crossings (if recorded in ledgers)
- MW/TAU shifts (if recorded in ledgers)
- Integrity vector scores (if computed and logged)

### CANNOT Prove:
- External web truth (no network calls)
- Subjective "correctness" without ground truth signals
- Causality (only correlation with observed data)
- Generalization beyond observed corpus

### Abstain Protects Integrity:
- Low signal count → Cannot evaluate confidently
- Missing ledgers → Cannot verify claims
- High integrity risk → May be observing noise/manipulation

---

## Related Documents

- [Backtest-as-Rent Patch Plan](../plan/backtest_as_rent_v0_1_patch_plan.md)
- [Backtest-as-Rent Specification](./backtest_as_rent_v0_1.md)

---

**End of Schema Specification**
