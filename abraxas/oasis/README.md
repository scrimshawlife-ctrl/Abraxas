# Operator Auto-Synthesis (OAS) System

## Overview

OAS is the Operator Auto-Synthesis system for Abraxas. It automatically discovers, validates, stabilizes, and canonizes new operators from streaming Decodo data, integrating them into the Slang Emergence Engine (SEE).

## Architecture

OAS follows a **Eurorack modular** design pattern: each component is a module with clear input/output schemas and registry interfaces.

### Pipeline Flow

```
Decodo Stream
    ↓
[Collector] → ResonanceFrames
    ↓
[SEE] → SlangClusters
    ↓
[Miner] → MinedPatterns
    ↓
[Proposer] → OperatorCandidates
    ↓
[Validator] → ValidationReports
    ↓
[Stabilizer] → StabilizationStates
    ↓
[Canonizer] → CanonDecisions
    ↓
[Registry] → Canonical Operators
    ↓
[SEE] uses new operators
```

## Components

### 1. Collector (`collector.py`)
- **Input**: Decodo events
- **Output**: Sorted ResonanceFrames
- **Purpose**: Normalize and order incoming data deterministically

### 2. Miner (`miner.py`)
- **Input**: SlangClusters, ResonanceFrames
- **Output**: MinedPatterns (co-occurrence, drift, phonetic)
- **Purpose**: Extract candidate operator patterns from clusters

### 3. Proposer (`proposer.py`)
- **Input**: MinedPatterns
- **Output**: OperatorCandidates with full provenance
- **Purpose**: Convert patterns to structured operator proposals

### 4. Validator (`validator.py`)
- **Input**: OperatorCandidate, test data, existing operators
- **Output**: ValidationReport with metrics
- **Purpose**: Evaluate candidates against held-out data
- **Metrics**:
  - Entropy (Shannon entropy of classifications)
  - False classification rate

### 5. Stabilizer (`stabilizer.py`)
- **Input**: OperatorCandidate, ValidationReports
- **Output**: StabilizationState
- **Purpose**: Ensure N cycles of consistent improvement
- **Default**: 3 cycles required, 80% consistency threshold

### 6. Canonizer (`canonizer.py`)
- **Input**: OperatorCandidate, ValidationReport, StabilizationState
- **Output**: CanonDecision
- **Purpose**: Apply adoption gates and make final decision

### 7. Ledger (`ledger.py`)
- **Format**: Append-only JSONL at `.aal/ledger/oasis_operators.jsonl`
- **Purpose**: Immutable audit trail of all OAS decisions

### 8. Registry (`registry_ext.py`)
- **Format**: Versioned JSON at `.aal/registry/operators.json`
- **Purpose**: Store canonical operators with rollback support

## Adoption Gates

All candidates must pass these gates to become canonical:

### 1. Validation Gate
- Metrics must improve:
  - `entropy_delta <= -0.05` (5% reduction)
  - `false_classification_delta <= -0.10` (10% reduction)

### 2. Stabilization Gate
- Requires N consistent validation cycles (default: 3)
- Consistency threshold: 80% (default)

### 3. Complexity Gate
- Added complexity must reduce applied metrics
- Prevents operators that don't justify their cost

### 4. Non-Poisoning Gate
- Rejects candidates with problematic patterns
- Checks for slurs, harassment, hate speech markers
- Hook interface for production classifiers

## Determinism Guarantees

OAS provides deterministic execution:

1. **Seeded RNG**: Where randomness needed, uses deterministic seeds
2. **Stable Ordering**: All collections sorted by deterministic keys
3. **Pure Functions**: Transformations are pure where possible
4. **Canonical JSON**: All hashing uses sorted keys
5. **Provenance**: Every decision includes full provenance chain

## Provenance Model

Every artifact includes a `ProvenanceBundle`:

```python
ProvenanceBundle(
    inputs=[ProvenanceRef(...)],      # Input artifact references
    transforms=["transform1", ...],    # Applied transformations
    metrics={"metric": value},         # Computed metrics
    created_at=datetime,               # Timestamp
    created_by="oasis_component",      # Creator component
)
```

## Configuration

Config file: `.aal/config/oasis.json`

```json
{
  "stabilization_cycles_required": 3,
  "min_entropy_delta": -0.05,
  "min_false_cringe_delta": -0.10,
  "max_time_regression_pct": 10,
  "quarantine_mode": true
}
```

## Usage

### CLI

Run full pipeline:
```bash
python -m abraxas.cli.oasis_cli run --input tests/fixtures/decodo_events_small.json
```

Inspect ledger:
```bash
python -m abraxas.cli.oasis_cli ledger --summary
python -m abraxas.cli.oasis_cli ledger --tail 10
```

Inspect registry:
```bash
python -m abraxas.cli.oasis_cli registry --status canonical
```

### Programmatic

```python
from abraxas.slang.engine import SlangEngine
from abraxas.oasis.collector import OASCollector

# Initialize with OAS enabled
engine = SlangEngine(enable_oasis=True)

# Process frames
frames = collector.collect_from_events(events)
clusters = engine.process_frames(frames)

# Trigger OAS cycle (discovers new operators)
engine.trigger_oasis_cycle(frames, clusters)

# Operators automatically reloaded
```

## Rollback Procedure

If a canonical operator causes issues:

1. **Identify operator**: Check ledger for operator_id
   ```bash
   python -m abraxas.cli.oasis_cli ledger --tail 50 | grep operator_id
   ```

2. **Demote to legacy**:
   ```python
   from abraxas.core.registry import OperatorRegistry
   from abraxas.oasis.registry_ext import OASRegistryExtension

   registry = OperatorRegistry()
   ext = OASRegistryExtension(registry)
   ext.demote_to_legacy("operator_id")
   ```

3. **Reload engine**:
   ```python
   engine.reload_operators()
   ```

4. **Verify**: Check that operator no longer active
   ```bash
   python -m abraxas.cli.oasis_cli registry --status canonical
   ```

## Adding New Validation Metrics

To add a new validation metric:

1. **Add metric computation** to `abraxas/core/metrics.py`:
   ```python
   def compute_new_metric(data: list) -> float:
       # Your computation
       return metric_value
   ```

2. **Update validator** (`abraxas/oasis/validator.py`):
   ```python
   def _compute_metrics(self, frames, operators):
       # ... existing metrics ...
       new_metric = compute_new_metric(predictions)
       return {
           "entropy": entropy,
           "false_classification_rate": false_rate,
           "new_metric": new_metric,  # Add here
       }
   ```

3. **Update configuration** (`.aal/config/oasis.json`):
   ```json
   {
       "min_entropy_delta": -0.05,
       "min_new_metric_delta": -0.15
   }
   ```

4. **Update canonizer gate** if needed for adoption decisions

## Testing

Run OAS tests:
```bash
pytest tests/test_oasis_models.py -v
pytest tests/test_oasis_pipeline_determinism.py -v
pytest tests/test_oasis_golden_ctd_candidate.py -v
```

## Design Principles

1. **Determinism First**: Every run on same data produces same results
2. **Provenance Everything**: Full audit trail for every decision
3. **Complexity Tax**: New operators must justify their complexity with metrics
4. **Eurorack Modularity**: Clear interfaces, composable components
5. **Canon Safety**: Multiple gates prevent low-quality operators
6. **Rollback Ready**: All changes are versioned and reversible

## Future Extensions

- Dynamic operator instantiation from registry
- Multi-cycle stabilization with statistical analysis
- Production non-poisoning classifier integration
- Distributed validation across multiple data slices
- Operator performance monitoring and auto-deprecation
- A/B testing framework for operator comparison

## References

- Core provenance: `abraxas/core/provenance.py`
- Operator protocol: `abraxas/slang/operators/base.py`
- Built-in CTD operator: `abraxas/slang/operators/builtin_ctd.py`
- Slang engine integration: `abraxas/slang/engine.py`
