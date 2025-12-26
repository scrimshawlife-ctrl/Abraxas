# Rent Enforcement v0.1 — Specification

**Version**: 0.1
**Status**: Active
**Created**: 2025-12-26
**Purpose**: Make "complexity must pay rent" deterministically enforceable

---

## Doctrine

**"Complexity must pay rent."**

Every new metric, operator, or artifact added to Abraxas must justify its existence by:

1. **Declaring what it improves** (measurably)
2. **Declaring what it costs** (time, compute, entropy)
3. **Proving its value** (via tests, golden files, or ledger deltas)

**No manifest = No merge.**

This is not aspirational. This is enforceable.

---

## What Is "Rent"?

Rent is **proof that added complexity reduces applied metrics**.

A component "pays rent" when it can demonstrate:

- **Benefit**: Measurable improvement to system properties (auditability, replayability, prediction calibration, etc.)
- **Cost**: Explicit computational cost (time, memory, I/O)
- **Proof**: Reproducible evidence via tests, golden outputs, or ledger deltas

If a component cannot declare these three things, it doesn't belong in Abraxas.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Developer Workflow                         │
│                                                               │
│  1. Implement metric/operator/artifact                       │
│  2. Add tests + golden files                                 │
│  3. Create rent manifest (YAML)                              │
│  4. Run: python -m abraxas.cli.rent_check --strict true      │
│  5. Fix any validation errors                                │
│  6. Merge (CI gate enforces rent check)                      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Rent Enforcement System                         │
│                                                               │
│  ┌──────────────────────────────────────────────┐            │
│  │ 1. Manifest Loader                            │            │
│  │    - Load all .yaml files from manifests dir │            │
│  │    - Validate schema (required fields)       │            │
│  └──────────────┬───────────────────────────────┘            │
│                 │                                             │
│                 ▼                                             │
│  ┌──────────────────────────────────────────────┐            │
│  │ 2. Rent Checks (The Gate)                    │            │
│  │    - Tests exist?                            │            │
│  │    - Golden files declared?                  │            │
│  │    - Ledgers declared?                       │            │
│  │    - Cost model present?                     │            │
│  │    - Operator edges valid? (if applicable)   │            │
│  │    - Cost bounds reasonable? (if stats)      │            │
│  └──────────────┬───────────────────────────────┘            │
│                 │                                             │
│                 ▼                                             │
│  ┌──────────────────────────────────────────────┐            │
│  │ 3. Report Generation                          │            │
│  │    - Console output (pass/fail)              │            │
│  │    - JSON report (for CI/audits)             │            │
│  │    - Markdown report (for humans)            │            │
│  └──────────────────────────────────────────────┘            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Rent Manifests (YAML Files)

**Location**: `data/rent_manifests/{metrics|operators|artifacts}/`

Each manifest is a YAML file declaring:

- **What**: ID, description, domain, owner module
- **Inputs/Outputs**: What it consumes/produces
- **Cost Model**: Expected time, memory, I/O
- **Rent Claim**: What it improves and how that's measurable
- **Proof**: Tests, golden files, ledgers touched

**Schema**: See [rent_manifest_schema.md](./rent_manifest_schema.md)

### 2. Manifest Loader (`abraxas.governance.rent_manifest_loader`)

**Purpose**: Load and validate manifest files.

**Functions**:
- `load_all_manifests(root_dir)`: Load all manifests from repo
- `validate_manifest(manifest)`: Validate against schema
- `get_manifest_summary(manifests)`: Generate summary stats

**Validation Rules**:
- All required fields present
- Cost model fields non-negative
- Test format valid (pytest node IDs)
- Domain and kind values valid
- Version follows semantic versioning

### 3. Rent Checks (`abraxas.governance.rent_checks`)

**Purpose**: Enforce rent payment via deterministic checks.

**Checks**:
1. **Tests Exist**: All declared tests are discoverable by pytest
2. **Golden Files Declared**: If tests exist, golden files should be declared
3. **Ledgers Declared**: Ledger paths declared (even if not yet created)
4. **Cost Model Present**: All cost model fields provided
5. **Operator Edges Valid**: TER edges subset of TER spec (if applicable)
6. **Cost Bounds Reasonable**: Observed costs within 2x of expected (if stats available)

**Output**: `RentCheckReport` with pass/fail status, failures, warnings, provenance

### 4. CLI Command (`python -m abraxas.cli.rent_check`)

**Purpose**: Run rent enforcement checks from command line or CI.

**Usage**:
```bash
python -m abraxas.cli.rent_check \
  --manifests data/rent_manifests \
  --strict true \
  --fail-on-warnings false \
  --output out/reports
```

**Exit Codes**:
- `0`: All checks passed
- `1`: Validation failures or errors

**Outputs**:
- Console summary (pass/fail)
- JSON report: `out/reports/rent_check_<timestamp>.json`
- Markdown report: `out/reports/rent_check_<timestamp>.md`

### 5. Run Receipt Integration (`abraxas.artifacts.daily_run_receipt`)

**Purpose**: Tie rent claims to observed runtime behavior.

**New Section**: `rent_metrics`

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

This links **claims** (from manifests) to **observed deltas** (from actual runs).

---

## How to Add a New Component

### Step 1: Implement Your Component

Write the code as usual. No special requirements.

### Step 2: Add Tests + Golden Files

```python
# tests/test_my_metric.py

def test_my_metric_computation():
    result = compute_my_metric(sample_input)
    assert result.passes_threshold()

def test_my_metric_golden():
    result = compute_my_metric(canonical_input)
    # Compare against golden/my_metric_output.json
    with open("tests/golden/metrics/my_metric_output.json") as f:
        expected = json.load(f)
    assert result.to_dict() == expected
```

### Step 3: Create Rent Manifest

```yaml
# data/rent_manifests/metrics/my_metric.yaml

id: "my_metric"
kind: "metric"
domain: "TAU"
description: "Measures temporal alignment quality between MW and TAU"
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
  tests:
    - "tests/test_my_metric.py::test_my_metric_computation"
    - "tests/test_my_metric.py::test_my_metric_golden"
  golden_files:
    - "tests/golden/metrics/my_metric_output.json"
  ledgers_touched:
    - "out/temporal_ledgers/tau_ledger.jsonl"

version: "0.1"
created_at: "2025-12-26"
```

### Step 4: Run Rent Check

```bash
python -m abraxas.cli.rent_check --strict true
```

Fix any validation errors reported.

### Step 5: Merge

Once rent-check passes, your PR is mergeable.

If CI is configured, the rent check will run automatically and block merge if failing.

---

## Validation Rules

### Structural Validation

1. All required fields present
2. `kind` ∈ {`metric`, `operator`, `artifact`}
3. `domain` ∈ {`MW`, `AALMANAC`, `TAU`, `INTEGRITY`, `TER`, `SOD`, `ROUTING`, `SCHEDULER`, `GOVERNANCE`}
4. `version` follows semantic versioning (e.g., `0.1`, `1.0.0`)
5. `created_at` is valid ISO 8601 date (YYYY-MM-DD)

### Cost Model Validation

1. `time_ms_expected` ≥ 0
2. `memory_kb_expected` ≥ 0
3. `io_expected` ∈ {`none`, `read`, `write`, `read_write`}

### Proof Validation

1. All `tests` discoverable by pytest
2. Test format: `path/to/test.py::test_function`
3. `golden_files` either exist or are created by tests
4. `ledgers_touched` follow path conventions

### Operator-Specific Validation

1. `ter_edges_claimed` is valid list of edge dicts
2. Each edge has `from` and `to` fields
3. If TER spec exists, edges ⊆ TER graph

### Artifact-Specific Validation

1. `output_paths` non-empty
2. `uniqueness_claim` non-empty

---

## CI Integration (Optional)

If your repository has CI (GitHub Actions, GitLab CI, etc.), add:

```yaml
- name: Rent Enforcement Check
  run: python -m abraxas.cli.rent_check --strict true
```

This gates merge on rent enforcement passing.

If no CI exists yet, document in your workflow how to run rent-check locally before merge.

---

## Evolution Path

### v0.1 (Current)

✅ Manifest schema defined
✅ Loader + validator implemented
✅ Basic rent checks (existence, structure)
✅ CLI command
✅ Seed manifests for critical spines
✅ Run receipt integration

### v0.2 (Future)

- Observed performance comparison against `cost_model`
- Auto-generation of manifests from docstrings
- Rent check runs tests and compares outputs
- Deprecation warnings for manifests without recent test runs

### v0.3 (Future)

- **Backtest-as-rent**: Predictive claims must attach to backtest case suites
- Thresholds enforced against actual backtest results
- Rent amortization: high-cost modules must show proportional improvement

### v1.0 (Future)

- Rent becomes continuous: each run updates rent ledger
- Components that stop improving get flagged for removal
- Automatic rent audits with degradation alerts
- Rent decay: components must continue proving value over time

---

## Examples

### Example 1: Metric Manifest

See: [data/rent_manifests/metrics/integrity_hash_chain.yaml](../../data/rent_manifests/metrics/integrity_hash_chain.yaml)

### Example 2: Operator Manifest

See: [data/rent_manifests/operators/scenario_router.yaml](../../data/rent_manifests/operators/scenario_router.yaml)

### Example 3: Artifact Manifest

See: [data/rent_manifests/artifacts/integrity_brief.yaml](../../data/rent_manifests/artifacts/integrity_brief.yaml)

---

## FAQs

### Q: What if I just want to experiment?

**A**: Experiments belong in `sandbox/` or `experiments/`, not in the main codebase. Once an experiment proves valuable, create a manifest and move it into the main system.

### Q: What if I don't know the exact cost model yet?

**A**: Make conservative estimates. Start with higher values. The cost model is a declaration of intent, not a contract. Over time (v0.2+), observed stats will inform cost model accuracy.

### Q: What if my component doesn't touch any ledgers?

**A**: That's a warning, not a failure. But ask yourself: if it doesn't affect any persistent state, how does it improve Abraxas? Consider whether it should exist.

### Q: Can I create a manifest without tests?

**A**: No. Tests are required. At minimum, create a smoke test that ensures your component doesn't crash.

### Q: What if my component is too simple to need a manifest?

**A**: If it's too simple to need a manifest, it's probably too simple to be a separate component. Inline it or make it a helper function.

### Q: Can I skip rent enforcement for "internal" components?

**A**: No. Internal components still add complexity. They must pay rent too.

---

## Related Documents

- [Rent Enforcement Patch Plan](../plan/rent_enforcement_v0_1_patch_plan.md) — Implementation roadmap
- [Rent Manifest Schema](./rent_manifest_schema.md) — Canonical manifest structure

---

## Summary

Rent Enforcement v0.1 makes "complexity must pay rent" **machine-checkable**.

Every metric, operator, and artifact must:
- Declare what it improves
- Declare what it costs
- Prove its value via tests

The gate is deterministic. The CLI is simple. The doctrine is clear.

**No manifest, no merge.**

Complexity must pay rent.

---

**End of Specification**
