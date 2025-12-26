# Abraxas Metric Governance

**Version**: 1.0
**Status**: Production
**Compatibility**: Abraxas v1.4+

---

## Overview

Strict, anti-hallucination governance system for emergent metrics in Abraxas.

**Philosophy**: Treat emergent metrics as hypotheses that must earn promotion via reproducible evidence. No symbolic coherence alone. No post-hoc success criteria.

---

## NON-NEGOTIABLE LAWS

### 1. Metrics are Contracts, not Ideas
Every metric must be:
- Reproducible from declared inputs
- Declare falsifiable outcomes

### 2. Candidate-First Lifecycle
- No emergent metric enters the canonical registry directly
- All emergent metrics start in the Candidate Registry
- Must pass promotion gates to reach canonical status

### 3. Promotion Requires Evidence Bundle
Promotion is **FORBIDDEN** unless:
- A signed evidence bundle exists
- Its hash matches the ledger entry
- All referenced outcome ledger slices exist and hashes match

### 4. Complexity Pays Rent
A promoted metric must demonstrate:
- **Measurable lift**: Error reduction OR calibration improvement OR manipulation-risk discrimination
- **Ablation survival**: Removal degrades objective scores beyond epsilon

### 5. Stabilization Window Required
- Candidate metrics must survive N cycles (default 5) with consistent performance
- Performance variance must be below threshold (default 0.05)
- Must pass drift tests (performance under perturbed inputs)

---

## Architecture

### Registries

**Candidate Registry** (`registry/metrics_candidate.json`):
- All emergent metrics start here
- Status lifecycle: PROPOSED → SHADOW → SCORED → STABILIZING → READY → PROMOTED/REJECTED/MERGED

**Canonical Registry** (`data/simulation/metrics.json`):
- Production metrics that have earned promotion
- Integrated with simulation architecture

### Promotion Ledger (Append-Only)

**`ledger/metric_promotions.jsonl`**:
- JSONL format (one entry per line)
- Each entry records promotion/rejection decision
- Includes evidence bundle hash, test results, lift metrics

**`ledger/metric_promotions_chain.jsonl`**:
- Hash chain for tamper detection
- Each entry includes: `{timestamp, metric_id, decision, prev_hash, signature}`
- Signature = SHA-256(prev_hash + entry_json_c14n)

---

## Promotion Gates (ALL Required)

### Gate 1: Provenance
**Required Fields**:
- `metric_id`: Unique identifier
- `description`: What this metric measures (min 10 chars)
- `units`: Measurement units
- `valid_range`: {min, max}
- `dependencies`: Other metrics this depends on
- `compute_fn`: Reference to computation function/formula
- `input_sources`: [{source, hash}, ...] - all inputs declared with SHA-256 hashes

**Failure Conditions**:
- Any required field missing or empty
- `valid_range.min >= valid_range.max`
- `input_sources` empty or missing hashes

### Gate 2: Falsifiability
**Required Fields**:
- `predictions_influenced`: Variable IDs this metric influences (non-empty)
- `disconfirmation_criteria`: What would reduce confidence
- `evaluation_window`: Timesteps for evaluation (positive integer)

**Failure Conditions**:
- `predictions_influenced` empty (metric "cannot be wrong")
- `disconfirmation_criteria` empty
- `evaluation_window <= 0`

### Gate 3: Non-Redundancy
**Tests**:
- Compute Pearson correlation with all canonical metrics
- Compute mutual information (discretized approximation)
- Identify nearest metrics (top 3 by correlation)

**Thresholds**:
- `max_corr_threshold`: 0.85 (default)
- If `max_corr >= 0.85`: FAIL (redundant)

**Outcome**:
- PASS: Not redundant, proceed
- FAIL with high correlation: REJECT or MERGE with existing metric

### Gate 4: Rent Payment
**Lift Metrics Computed**:
- `forecast_error_delta` (negative = improvement)
- `brier_delta` (negative = improvement)
- `calibration_delta` (positive = improvement)
- `misinfo_auc_delta` (positive = improvement)
- `world_media_divergence_explained_delta` (positive = improvement)

**Thresholds** (default, conservative):
- `forecast_error_delta <= -0.02` (2% error reduction) OR
- `brier_delta <= -0.01` (1% Brier reduction) OR
- `calibration_delta >= 0.05` (5% calibration improvement) OR
- `misinfo_auc_delta >= 0.03` (3% AUC improvement) OR
- `world_media_divergence_explained_delta >= 0.05` (5% variance explained)

**Failure Condition**:
- None of the above thresholds met

### Gate 5: Ablation
**Test**:
- Run evaluation with metric enabled vs disabled
- Compute degradation when candidate is removed

**Degradation Metrics**:
- `forecast_error_degradation`: Should be positive (error increases when removed)
- `brier_degradation`: Should be positive
- `calibration_degradation`: Should be positive (quality decreases)
- `auc_degradation`: Should be positive

**Threshold**:
- `epsilon = 0.01` (default)
- At least ONE degradation metric must exceed epsilon

**Failure Condition**:
- All degradation metrics <= epsilon (metric is useless)

### Gate 6: Stabilization
**Requirements**:
- `cycles_required`: Default 5 consecutive evaluation cycles
- `variance_threshold`: Default 0.05
- Drift test: Performance in last 3 cycles vs first 3 cycles must not degrade >10%

**Tests**:
- Performance variance across cycles < threshold
- Drift test passed

**Failure Conditions**:
- Insufficient cycles completed
- Performance variance >= threshold
- Drift test failed

---

## Candidate Metric Statuses

```
PROPOSED → SHADOW → SCORED → STABILIZING → READY → PROMOTED/REJECTED/MERGED
```

- **PROPOSED**: Initial submission, awaiting shadow deployment
- **SHADOW**: Running in shadow mode (observing only, not influencing)
- **SCORED**: Initial evaluation complete, results recorded
- **STABILIZING**: In stabilization window (N cycles)
- **READY**: Passed all gates, awaiting promotion decision
- **PROMOTED**: Moved to canonical registry
- **REJECTED**: Failed gates, not promoted
- **MERGED**: Redundant, merged with existing canonical metric

---

## CLI Commands

### Propose Candidate
```bash
python -m abraxas.metrics.cli propose registry/examples/candidate_METRIC_ID.json
```

Creates candidate entry in registry with status=PROPOSED.

### Evaluate Candidate
```bash
python -m abraxas.metrics.cli evaluate METRIC_ID
```

Runs all 6 promotion gates, generates evidence bundle, updates status.

**Output**:
- Gate pass/fail results
- Lift metrics
- Redundancy scores
- Stabilization scores
- Evidence bundle saved to `ledger/evidence_METRIC_ID.json`

### Promote Candidate
```bash
python -m abraxas.metrics.cli promote METRIC_ID
```

**Prerequisites**:
- Candidate status must be READY
- Evidence bundle must exist
- Hash chain must verify

**Actions**:
- Creates promotion ledger entry
- Appends to hash chain
- Moves metric to canonical registry
- Updates candidate status to PROMOTED

---

## Evidence Bundle

Required for promotion. Contains:

```json
{
  "metric_id": "METRIC_ID",
  "timestamp": "2025-12-26T00:00:00Z",
  "sim_version": "1.0.0",
  "seeds_used": [42, 43, 44, 45, 46],
  "outcome_ledger_slice_hashes": ["hash1", "hash2", "hash3"],
  "test_results": {
    "provenance": true,
    "falsifiability": true,
    "redundancy": true,
    "rent_payment": true,
    "ablation": true,
    "stabilization": true
  },
  "lift_metrics": {
    "forecast_error_delta": -0.03,
    "brier_delta": -0.01,
    "calibration_delta": 0.06,
    "misinfo_auc_delta": 0.04,
    "world_media_divergence_explained_delta": 0.07
  },
  "redundancy_scores": {
    "max_corr": 0.45,
    "mutual_info": 0.12,
    "nearest_metric_ids": ["METRIC_A", "METRIC_B"]
  },
  "stabilization_scores": {
    "cycles_required": 5,
    "cycles_passed": 6,
    "drift_tests_passed": 2,
    "performance_variance": 0.02
  },
  "ablation_results": {
    "forecast_error_degradation": 0.03,
    "brier_degradation": 0.015,
    "calibration_degradation": 0.04,
    "auc_degradation": 0.02
  }
}
```

**Evidence Bundle Hash**: SHA-256 of canonical JSON representation (sorted keys, stable float formatting).

---

## Promotion Ledger Entry

```json
{
  "timestamp": "2025-12-26T01:00:00Z",
  "metric_id": "MEDIA_COMPETITION_MISINFO_PRESSURE",
  "candidate_version": "0.1.0",
  "sim_version": "1.0.0",
  "seeds_used": [42, 43, 44, 45, 46],
  "evidence_bundle_hash": "abc123...",
  "tests_run": {
    "provenance": true,
    "falsifiability": true,
    "redundancy": true,
    "rent_payment": true,
    "ablation": true,
    "stabilization": true
  },
  "lift_metrics": { ... },
  "redundancy_scores": { ... },
  "stabilization": { ... },
  "decision": "PROMOTED",
  "rationale": "All gates passed. Measurable lift demonstrated. Ablation survival confirmed. Stabilization achieved.",
  "prev_hash": "000000...",
  "signature": "def456..."
}
```

**Signature Computation**: `SHA-256(prev_hash + canonicalized_entry_json)`

---

## Hash Chain Verification

```python
from abraxas.metrics import PromotionLedger

ledger = PromotionLedger()
is_valid = ledger.verify_chain()

if not is_valid:
    raise RuntimeError("Promotion ledger hash chain is invalid (possible tampering)")
```

**Chain Integrity Rules**:
- First entry: `prev_hash = "0" * 64` (genesis)
- Each subsequent entry: `prev_hash = SHA-256(previous_entry_without_signature)`
- Signature: `SHA-256(prev_hash + current_entry_canonical_json)`

---

## Example Workflow

### 1. Propose Candidate
```bash
python -m abraxas.metrics.cli propose registry/examples/candidate_MEDIA_COMPETITION_MISINFO_PRESSURE.json
```

Output:
```
✓ Proposed candidate metric: MEDIA_COMPETITION_MISINFO_PRESSURE
  Status: PROPOSED
  Version: 0.1.0
```

### 2. Evaluate Candidate
```bash
python -m abraxas.metrics.cli evaluate MEDIA_COMPETITION_MISINFO_PRESSURE
```

Output:
```
=== Promotion Gate Results ===
  Provenance:     ✓ PASS
  Falsifiability: ✓ PASS
  Redundancy:     ✓ PASS
  Rent Payment:   ✓ PASS
  Ablation:       ✓ PASS
  Stabilization:  ✓ PASS

✓ All gates PASSED - candidate is READY for promotion

Evidence bundle saved: ledger/evidence_MEDIA_COMPETITION_MISINFO_PRESSURE.json
Evidence hash: abc123def456...
```

### 3. Promote Candidate
```bash
python -m abraxas.metrics.cli promote MEDIA_COMPETITION_MISINFO_PRESSURE
```

Output:
```
✓ Promoted MEDIA_COMPETITION_MISINFO_PRESSURE to canonical registry
  Evidence hash: abc123def456...
  Ledger entry signature: def789abc012...
  Chain verified: True
```

---

## Integration with Simulation Architecture

**Variable Coupling**:
- Candidate metrics must declare `target_sim_variables`
- Must specify `required_rune_bindings` (ABX-Runes for coupling)
- Simulation variables referenced must exist in SimVar Registry

**Outcome Ledger Integration**:
- Evidence bundles must reference outcome ledger slices by hash
- `outcome_ledger_slice_hashes` must match existing ledger entries
- Provides audit trail from raw simulation outputs to promotion decision

**Provenance Chain**:
```
Simulation Run (seed X)
    ↓ produces
Outcome Ledger Entry (hash Y)
    ↓ referenced by
Evidence Bundle (hash Z)
    ↓ referenced by
Promotion Ledger Entry (signature W)
    ↓ verifies via
Hash Chain
```

---

## Testing

```bash
# Run all metric governance tests
pytest tests/test_metric_governance.py

# Run hash chain tests
pytest tests/test_promotion_ledger_chain.py
```

**Test Coverage**:
- All 6 gates with pass/fail cases
- Hash chain integrity and tamper detection
- Evidence bundle hash determinism
- Ledger append-only enforcement

---

## References

- Implementation: `abraxas/metrics/`
- Schema: `schemas/metric_candidate.schema.json`
- Example: `registry/examples/candidate_MEDIA_COMPETITION_MISINFO_PRESSURE.json`
- Tests: `tests/test_metric_governance.py`, `tests/test_promotion_ledger_chain.py`
