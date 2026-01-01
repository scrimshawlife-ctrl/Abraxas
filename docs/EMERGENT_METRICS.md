# Abraxas Emergent Metrics & Shadow Evaluation System

## Overview

The Emergent Metrics system extends Abraxas Metric Governance to allow new metrics to **emerge** from simulation outputs without hallucination, self-reference, or symbolic bias.

**CRITICAL PRINCIPLES:**

1. **Emergence ≠ Promotion**: The system may PROPOSE metrics. Only governance may PROMOTE metrics.
2. **Shadow-Only Until Proven**: Candidate metrics MUST run in SHADOW mode. Shadow metrics may observe and log values only. Shadow metrics MUST NOT influence state transitions or predictions.
3. **Evidence Beats Symbolism**: Symbolic coherence alone is insufficient. Promotion requires ledger-verifiable evidence bundles.

## Architecture

### Components

```
abraxas/metrics/
├── emergence.py       # Metric proposal engine (analyzes residuals/divergence)
├── evidence.py        # Evidence bundle creation and verification
├── thresholds.py      # Deterministic evaluation thresholds
└── alive.py           # Existing ALIVE metric wrapper

abraxas/sim/
└── ledger.py          # Outcome ledger with shadow metric logging

registry/
├── metrics.json                # Canonical metrics (promoted)
├── metrics_candidate.json      # Candidate metrics (proposed/shadow/scored)
└── metric_candidate.schema.json # JSON schema for candidates

evidence/
└── <metric_id>/
    └── <bundle_id>.json        # Evidence bundles for promotion

.aal/ledger/
├── outcomes.jsonl              # Simulation outcome ledger
└── metric_promotions.jsonl     # Promotion decision ledger
```

### Lifecycle States

```
PROPOSED → SHADOW → SCORED → STABILIZING → READY → MERGED
                                            ↓
                                        REJECTED
```

- **PROPOSED**: Candidate identified from ledger analysis
- **SHADOW**: Running in observe-only mode (no state feedback)
- **SCORED**: Evaluation complete (lift/redundancy/ablation computed)
- **STABILIZING**: Undergoing stability testing across multiple cycles
- **READY**: Promotion-eligible (evidence bundle created, gates passed)
- **MERGED**: Promoted to canonical status
- **REJECTED**: Failed evaluation criteria

## Non-Negotiable Laws

### 1. Emergence ≠ Promotion

```python
# ✓ ALLOWED: Proposing a candidate metric
emergence = MetricEmergence()
candidates = emergence.run_emergence()
emergence.write_candidates(candidates)  # Writes to metrics_candidate.json

# ✗ FORBIDDEN: Direct promotion without governance
# candidates[0]['status'] = 'MERGED'  # NEVER DO THIS
```

### 2. Shadow-Only Until Proven

```python
# ✓ ALLOWED: Shadow metric execution
ledger.append_outcome(
    cycle=cycle,
    canonical_metrics={"world_divergence": 0.5},  # Affects state
    shadow_metrics={"metric_res_abc123": 0.3}     # Observe-only
)

# ✗ FORBIDDEN: Using shadow metric in state transition
# state.next_value = compute(shadow_metrics['metric_res_abc123'])  # NEVER
```

### 3. Evidence Beats Symbolism

```python
# ✓ ALLOWED: Promotion with evidence bundle
evidence_system = EvidenceBundle()
bundle = evidence_system.create_bundle(
    metric_id="metric_res_abc123",
    candidate_spec=candidate,
    ledger_slice=ledger_entries,
    evaluation_results=eval_results,
    registry_snapshots=snapshots,
    seeds=[42, 43, 44]
)

if bundle['promotion_eligible']:
    # Use governance CLI to promote
    # python -m abraxas.cli.metrics_governance promote metric_res_abc123 bundle_id

# ✗ FORBIDDEN: Promotion without evidence
# "The metric seems good" → REJECTED
```

## Runtime Integration Order (MANDATORY)

```python
# 1. Load canonical registries
canonical_metrics = load_metrics_registry("registry/metrics.json")
rune_registry = load_rune_registry("abraxas/runes/registry.json")

# 2. Load candidate registry
candidate_registry = load_metrics_registry("registry/metrics_candidate.json")

# 3. Validate all schemas + rune bindings
validate_all_schemas()

# 4. Run canonical simulation step
canonical_outputs = run_simulation_step(canonical_metrics, rune_registry)

# 5. Compute shadow metrics (observe-only)
shadow_outputs = {}
for candidate in candidate_registry['candidates']:
    if candidate['status'] in ['SHADOW', 'SCORED', 'STABILIZING']:
        shadow_outputs[candidate['metric_id']] = compute_shadow_metric(candidate)

# 6. Append outcome ledger entry
ledger.append_outcome(
    cycle=cycle,
    canonical_metrics=canonical_outputs,
    shadow_metrics=shadow_outputs,  # NEVER fed back to step 4
    rune_bindings=active_runes,
    seed=seed
)

# 7. Periodically run evaluation + stabilization jobs
if cycle % EVAL_INTERVAL == 0:
    run_evaluation_pipeline()

# 8. Promotion only via governance CLI
# (never automated)
```

## Safety Rules

### Hard Failures

The system MUST hard fail if:

1. **Shadow metric attempts to mutate state**
   ```python
   if shadow_metric_id in state_transition_inputs:
       raise SecurityError("Shadow metric used in state transition")
   ```

2. **Promoted metric lacks evidence bundle**
   ```python
   if metric['status'] == 'MERGED' and not metric['evidence_bundle_hash']:
       raise IntegrityError("Promoted metric missing evidence bundle")
   ```

3. **Thresholds modified without ledger entry**
   ```python
   # All threshold changes must be logged
   if thresholds_modified and not ledger_entry_exists:
       raise ProvenanceError("Threshold modification without ledger")
   ```

## Usage Examples

### 1. Propose Candidate Metrics

```python
from abraxas.metrics.emergence import MetricEmergence

emergence = MetricEmergence(
    ledger_path=".aal/ledger/outcomes.jsonl",
    output_path="registry/metrics_candidate.json"
)

# Analyze ledger for unexplained patterns
candidates = emergence.run_emergence(limit=1000)

# Write proposals (does NOT promote)
emergence.write_candidates(candidates)

print(f"Proposed {len(candidates)} candidate metrics")
```

### 2. Run Shadow Metrics

```python
from abraxas.sim.ledger import OutcomeLedger

ledger = OutcomeLedger()

# Load candidate registry
with open("registry/metrics_candidate.json") as f:
    candidate_data = json.load(f)

# Compute shadow metrics (observe-only)
shadow_metrics = {}
for candidate in candidate_data['candidates']:
    if candidate['status'] == 'SHADOW':
        # Compute metric (implementation depends on candidate spec)
        value = compute_candidate_metric(candidate)
        shadow_metrics[candidate['metric_id']] = value

# Log to ledger (shadow metrics separate from canonical)
ledger.append_outcome(
    cycle=cycle,
    canonical_metrics=canonical_metrics,
    shadow_metrics=shadow_metrics,
    rune_bindings=active_runes,
    seed=seed
)
```

### 3. Create Evidence Bundle

```python
from abraxas.metrics.evidence import EvidenceBundle

evidence_system = EvidenceBundle(evidence_dir="evidence")

# Collect evaluation results
evaluation_results = {
    "lift": {
        "mae_delta": 0.03,
        "brier_delta": 0.015,
        "misinfo_auc_delta": 0.02
    },
    "redundancy": {
        "max_correlation": 0.72
    },
    "ablation": {
        "performance_drop": 0.08
    },
    "stability": {
        "stable_cycles": 7,
        "coefficient_variation": 0.09,
        "drift_detection_rate": 0.65
    }
}

# Create bundle
bundle = evidence_system.create_bundle(
    metric_id="metric_res_abc123",
    candidate_spec=candidate,
    ledger_slice=ledger_entries,
    evaluation_results=evaluation_results,
    registry_snapshots=snapshots,
    seeds=[42, 43, 44, 45, 46]
)

# Write to disk
bundle_path = evidence_system.write_bundle(bundle)

print(f"Evidence bundle: {bundle['bundle_id']}")
print(f"Promotion eligible: {bundle['promotion_eligible']}")
```

### 4. Promote Metric (Governance CLI)

```bash
# List candidates
python -m abraxas.cli.metrics_governance list

# List evidence bundles
python -m abraxas.cli.metrics_governance evidence

# Verify evidence bundle
python -m abraxas.cli.metrics_governance verify metric_res_abc123 bundle_id_xyz

# Promote to canonical (requires evidence bundle)
python -m abraxas.cli.metrics_governance promote metric_res_abc123 bundle_id_xyz
```

## Deterministic Thresholds

All evaluation thresholds are defined in `abraxas/metrics/thresholds.py`:

```python
MAX_REDUNDANCY_CORR = 0.85              # Max correlation with existing metrics
MIN_FORECAST_ERROR_DELTA = 0.02         # Min forecast improvement (2%)
MIN_BRIER_DELTA = 0.01                  # Min Brier score improvement
MIN_MISINFO_AUC_DELTA = 0.03           # Min AUC improvement
MIN_ABLATION_DAMAGE = 0.05              # Min performance drop when removed
MIN_STABILITY_CYCLES = 5                # Min stable cycles required
MAX_STABILITY_VARIANCE = 0.10           # Max coefficient of variation
MIN_DRIFT_SENSITIVITY = 0.60            # Min drift detection rate
MIN_COMPOSITE_SCORE = 0.70              # Min composite score for promotion
```

**CRITICAL**: Modifying thresholds requires ledger documentation.

## Hypothesis Types

```python
RESIDUAL_EXPLAINER      # Explains unexplained variance in existing metrics
REDUNDANCY_SPLITTER     # Decomposes redundant metrics
MANIPULATION_DETECTOR   # Detects adversarial manipulation
COUPLING_BRIDGE         # Bridges divergence between correlated metrics
TEMPORAL_CORRELATE      # Captures temporal dynamics
```

## Promotion Gates

A metric must pass ALL gates to be promotion-eligible:

1. **non_redundant**: `max_correlation < 0.85`
2. **forecast_lift**: Meaningful forecast improvement
3. **ablation_proof**: Performance degrades when metric is removed
4. **stability_verified**: Stable across multiple cycles
5. **drift_robust**: Detects synthetic drift events

## Worked Example

See `examples/emergent_metrics_example.py` for a complete end-to-end demonstration:

```bash
python examples/emergent_metrics_example.py
```

This example:
1. Generates synthetic ledger with unexplained variance
2. Proposes candidate metric from residual analysis
3. Runs metric in SHADOW mode for 50 cycles
4. Evaluates but does NOT promote

## Testing

```bash
# Verify shadow isolation
python -c "
from abraxas.sim.ledger import OutcomeLedger
ledger = OutcomeLedger('.aal/ledger/outcomes.jsonl')
assert ledger.verify_shadow_isolation(), 'Shadow isolation violated!'
print('✓ Shadow isolation verified')
"

# Run worked example
python examples/emergent_metrics_example.py
```

## Compliance

This system operates under:
- **SEED** (determinism, provenance, entropy minimization)
- **ABX-Core** (explicit assumptions, modular logic, measurable rent payment)
- **ABX-Runes** as the only legal coupling layer

All operations are deterministic and append-only (ledger immutability).
