# Abraxas Examples

## Emergent Metrics Example

`emergent_metrics_example.py` demonstrates the full lifecycle of the Abraxas Emergent Metrics & Shadow Evaluation system.

### What it does

1. **Generates Synthetic Ledger**: Creates 100 simulation cycles with intentional unexplained variance in `world_media_divergence` (weekly spike pattern)

2. **Runs Emergence Analysis**: Analyzes the ledger to detect patterns and propose candidate metrics

3. **Executes Shadow Metrics**: Runs the candidate metric in SHADOW mode for 50 cycles (observe-only, no state feedback)

4. **Verifies Shadow Isolation**: Confirms that shadow metrics never affect canonical metrics

5. **Evaluates Performance**: Computes lift, redundancy, ablation, and stability metrics

6. **Creates Evidence Bundle**: Generates cryptographically sealed evidence bundle with evaluation results

### Run the example

```bash
python examples/emergent_metrics_example.py
```

### Expected output

```
======================================================================
Abraxas Emergent Metrics: Shadow Evaluation Example
======================================================================

[1/5] Generating synthetic outcome ledger...
✓ Generated 100 cycles with unexplained variance in world_media_divergence

[2/5] Running metric emergence analysis...
✓ Emergence analysis complete: 1 candidate(s) proposed
  Metric ID: metric_res_abc123...
  Hypothesis: residual_explainer
  Description: Explains high variance in world_media_divergence (CV=0.42)
  Status: PROPOSED

[3/5] Running shadow metric execution...
✓ Running shadow metric 'metric_res_abc123...' for 50 cycles
  Shadow metric mean: 0.378
  Shadow metric std dev: 0.142

[4/5] Verifying shadow metric isolation...
✓ Shadow isolation verified: shadow metrics do NOT affect canonical metrics

[5/5] Evaluating shadow metric performance...
✓ Evaluating shadow metric 'metric_res_abc123...'
  Lift Metrics:
    MAE Delta: 0.030
    Brier Delta: 0.015
  Redundancy Metrics:
    Max Correlation: 0.72
  Ablation:
    Performance Drop: 0.08
  Stability:
    Stable Cycles: 7
    CV: 0.09

✓ Creating evidence bundle for 'metric_res_abc123...'
  Bundle ID: metric_res_abc123_20251226_123456
  Composite Score: 0.742
  Promotion Eligible: True
  Gates Passed:
    non_redundant: ✓
    forecast_lift: ✓
    ablation_proof: ✓
    stability_verified: ✓
    drift_robust: ✓
  Bundle written to: evidence_example/metric_res_abc123/.../bundle.json

======================================================================
Summary
======================================================================
Candidate Metric: metric_res_abc123...
Hypothesis Type: residual_explainer
Status: PROPOSED → SHADOW (not promoted)
Shadow Cycles Executed: 50
Evidence Bundle Created: Yes
Promotion Eligible: True

NOTE: Metric remains in SHADOW status. Promotion requires governance approval.
======================================================================
```

### Key takeaways

- **Emergence ≠ Promotion**: The metric is proposed and evaluated but NOT automatically promoted
- **Shadow Isolation**: Shadow metrics are logged separately and never affect state transitions
- **Evidence-Based**: Promotion requires verifiable evidence bundles with cryptographic hashes
- **Deterministic**: All thresholds and evaluations are explicit and reproducible

### Next steps

To promote the metric (in a real scenario):

```bash
# Verify the evidence bundle
python -m abraxas.cli.metrics_governance verify metric_res_abc123 bundle_id_xyz

# Promote to canonical (requires governance approval)
python -m abraxas.cli.metrics_governance promote metric_res_abc123 bundle_id_xyz
```

See `docs/EMERGENT_METRICS.md` for full documentation.

---

## Neon-Genie Integration Example

`neon_genie_integration.py` shows how to invoke the Neon-Genie adapter and handle the external overlay being unavailable.

### Run the example

```bash
python examples/neon_genie_integration.py
```

### Expected output (when overlay is missing)

```
Neon-Genie unavailable: Neon-Genie overlay not yet integrated (stub mode)
```
