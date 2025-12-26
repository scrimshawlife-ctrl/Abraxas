# Rent Enforcement v0.1 — Patch Plan

**Status**: Active Development
**Version**: 0.1
**Created**: 2025-12-26
**Purpose**: Make "complexity must pay rent" machine-checkable

---

## What "Rent" Means Operationally

**Doctrine**: Every new metric, operator, or artifact added to Abraxas must justify its existence.

**Rent Payment** = Proof that the added complexity:
1. **Improves** something measurable (replayability, auditability, prediction calibration, etc.)
2. **Costs** something quantifiable (time, compute, entropy, memory)
3. **Proves** itself via tests, golden files, or ledger deltas

**No manifest = No merge.**

If a component cannot declare what it improves, what it costs, and how it's proven, it doesn't belong in the system.

---

## How Manifests Are Stored

Manifests are YAML files stored in domain-specific directories:

```
data/rent_manifests/
├── metrics/          # MetricRentManifest files
├── operators/        # OperatorRentManifest files
└── artifacts/        # ArtifactRentManifest files
```

Each manifest is a declaration file that answers:
- **What**: ID, description, domain
- **Inputs/Outputs**: What it consumes/produces
- **Cost Model**: Expected time, memory, I/O
- **Rent Claim**: What it improves and how that's measurable
- **Proof**: Tests, golden files, ledgers touched

---

## What the Gate Checks

The rent enforcement gate (`abx rent-check`) validates:

### 1. **Structural Validation**
- All required fields present
- Cost model fields non-negative
- Domain values valid
- Version format correct

### 2. **Test Coverage**
- All declared tests exist (discoverable by pytest)
- Tests can be run (though gate doesn't run them)
- Golden files exist or are created by tests

### 3. **Ledger Declaration**
- Ledgers touched are declared
- Ledger paths follow conventions

### 4. **Operator-Specific Checks**
- TER edges claimed are subset of actual TER graph
- Operator edges don't conflict

### 5. **Cost Bounds** (optional)
- If prior run receipts exist, compare observed vs expected costs
- Warn if actual costs exceed declared costs by >2x

---

## How to Add a New Module Without Pain

### 5-Step Process

#### 1. **Implement** your metric/operator/artifact
Write the code as usual. Follow existing patterns.

#### 2. **Add Tests + Golden Files**
```python
# tests/test_my_new_metric.py
def test_my_metric_computation():
    result = compute_my_metric(sample_input)
    assert result.passes_threshold

def test_my_metric_golden():
    result = compute_my_metric(canonical_input)
    # Compare against golden/my_metric_output.json
```

#### 3. **Create Manifest**
```yaml
# data/rent_manifests/metrics/my_metric.yaml
id: "my_metric"
kind: "metric"
domain: "TAU"
description: "Measures temporal alignment quality"
owner_module: "abraxas.metrics.tau.my_metric"
inputs: ["tau_signal", "mw_terms"]
outputs: ["my_metric_score"]
cost_model:
  time_ms_expected: 50
  memory_kb_expected: 1024
  io_expected: "read"
rent_claim:
  improves: ["prediction_calibration", "auditability"]
  measurable_by: ["backtest_pass_rate", "golden_test"]
  thresholds:
    backtest_pass_rate_min: 0.70
proof:
  tests: ["tests/test_my_new_metric.py::test_my_metric_computation",
          "tests/test_my_new_metric.py::test_my_metric_golden"]
  golden_files: ["tests/golden/metrics/my_metric_output.json"]
  ledgers_touched: ["out/temporal_ledgers/tau_ledger.jsonl"]
version: "0.1"
created_at: "2025-12-26"
```

#### 4. **Run rent-check**
```bash
python -m abraxas.cli.rent_check --strict true
```

Fix any validation errors. The gate will tell you exactly what's missing.

#### 5. **Merge**
Once rent-check passes, your PR is mergeable.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Developer adds code                   │
│                  + tests + manifest YAML                 │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│           abraxas.governance.rent_manifest_loader        │
│  • Loads all manifests from data/rent_manifests/        │
│  • Validates schema (required fields, types)            │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│             abraxas.governance.rent_checks               │
│  • check_tests_exist(manifest)                          │
│  • check_golden_files_declared(manifest)                │
│  • check_ledgers_declared(manifest)                     │
│  • check_cost_model_present(manifest)                   │
│  • check_operator_edges_declared(manifest)              │
│  • check_expected_cost_bounds(manifest, receipts)       │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  RentCheckReport                         │
│  • passed: bool                                          │
│  • failures: list[dict]                                  │
│  • warnings: list[dict]                                  │
│  • provenance: dict                                      │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                CLI: abx rent-check                       │
│  • Prints summary to console                            │
│  • Writes report to out/reports/rent_check_<ts>.json    │
│  • Exit code 0 if passed, 1 if failed                   │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
                    CI Gate (optional)
```

---

## Integration Points

### Run Receipt Hook
`abraxas/artifacts/daily_run_receipt.py` gains a new section:
```json
{
  "rent_metrics": {
    "count_manifests_by_kind": {"metric": 12, "operator": 8, "artifact": 5},
    "declared_ledgers": ["tau_ledger.jsonl", "mw_ledger.jsonl"],
    "declared_tests": 47,
    "last_backtest_pass_rate": 0.78,
    "last_delta_counts": {
      "new_terms": 3,
      "mw_shifts": 2,
      "tau_updates": 5
    }
  }
}
```

This ties **claims** (from manifests) to **observed deltas** (from actual runs).

### CI Integration (Optional)
If CI exists, add:
```yaml
- name: Rent Enforcement Check
  run: python -m abraxas.cli.rent_check --strict true
```

If no CI, document how to add it.

---

## Evolution Path

### v0.1 (This Patch)
- Manifest schema defined
- Loader + validator implemented
- Basic rent checks (existence, structure)
- CLI command
- Seed manifests for critical spines

### v0.2 (Future)
- Observed performance comparison against cost_model
- Auto-generation of manifests from docstrings
- Rent check runs tests and compares outputs

### v0.3 (Future)
- Backtest linkage: rent claims must attach to backtest case suites
- Thresholds enforced against backtest results
- Rent amortization: high-cost modules must show proportional improvement

### v1.0 (Future)
- Rent becomes continuous: each run updates rent ledger
- Components that stop improving get flagged for removal
- Automatic rent audits with degradation alerts

---

## File Tree (New Files)

```
abraxas/
├── governance/
│   ├── __init__.py
│   ├── rent_manifest_loader.py      # Load + validate manifests
│   ├── rent_checks.py                # Enforcement gate logic
│   └── rent_report.py                # Report generation
├── cli/
│   └── rent_check.py                 # CLI command
└── artifacts/
    └── daily_run_receipt.py          # Modified: add rent_metrics section

data/
└── rent_manifests/
    ├── metrics/
    │   ├── tau_latency.yaml
    │   ├── tau_memory.yaml
    │   └── ...
    ├── operators/
    │   ├── smem_gatekeeper.yaml
    │   ├── srr_router.yaml
    │   └── ...
    └── artifacts/
        ├── integrity_brief.yaml
        ├── ledger_hash_chain.yaml
        └── ...

docs/
├── plan/
│   └── rent_enforcement_v0_1_patch_plan.md  # This file
└── specs/
    ├── rent_manifest_schema.md               # Schema definition
    └── rent_enforcement_v0_1.md              # Specification

tests/
├── test_rent_manifest_validation.py
├── test_rent_check_fails_missing_test.py
├── test_rent_check_fails_missing_cost_model.py
├── test_rent_check_operator_edges_subset.py
├── test_rent_report_emission.py
└── golden/
    └── governance/
        └── rent_check_report.json

out/
└── reports/
    └── rent_check_<timestamp>.{json,md}
```

---

## Constraints Met

✅ **Incremental Patch Only**: New files + minimal modifications to existing systems
✅ **Deterministic**: All checks are rule-based, no heuristics
✅ **Append-only where applicable**: Manifests are additive; run receipts gain new section
✅ **No rewrites**: Existing metrics/operators untouched; manifests added separately
✅ **Governance, not simulation**: Lives beside specs/tests/manifests, not in core logic

---

## What This Buys Immediately

1. **No more "cool idea" modules without proof** 🧾
2. **Auditability**: Every component's value proposition is explicit
3. **Gatekeeping**: CI/local checks prevent complexity creep
4. **Evolvability**: Manifests become living documentation
5. **Foundation for backtest-as-rent**: v0.2+ can require backtest improvements

---

## Next After Rent Enforcement

**Backtest-as-rent**: Any predictive claim must attach to backtest case suite and show improvement across versions.

That's how Abraxas becomes something that survives hostile questioning.

---

**End of Patch Plan**
