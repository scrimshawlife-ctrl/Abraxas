# Seal Validation Guide

**Version:** 1.0.0  
**Last Updated:** 2026-01-11  
**Purpose:** Complete guide to Abraxas seal validation infrastructure for production releases

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Seal Process Steps](#seal-process-steps)
4. [Artifact Schemas](#artifact-schemas)
5. [Validation Rules](#validation-rules)
6. [Dozen-Run Gate](#dozen-run-gate)
7. [Seal Report](#seal-report)
8. [Troubleshooting](#troubleshooting)
9. [Integration with CI/CD](#integration-with-cicd)

---

## Overview

The Abraxas seal validation infrastructure ensures **deterministic, reproducible production releases** through:

1. **Artifact Generation**: Running deterministic tick to produce validated artifacts
2. **Schema Validation**: Verifying all artifacts against JSON schemas
3. **Dozen-Run Gate**: Ensuring 12 consecutive runs produce identical results
4. **Seal Report**: Generating provenance-tracked release certification

### Philosophy

- **Determinism First**: Same inputs → same outputs, always
- **Provenance Tracked**: SHA-256 hashes for every artifact
- **Zero Tolerance**: Any variation fails the gate
- **Audit Ready**: Complete trace from code to sealed artifacts

### Components

```
scripts/
├── seal_release.py       # Main seal orchestration script
└── validate_artifacts.py # Artifact validator CLI

schemas/
├── runheader.v0.schema.json       # Run metadata schema
├── runindex.v0.schema.json        # Run index schema
├── trendpack.v0.schema.json       # Trend data schema
├── resultspack.v0.schema.json     # Results pack schema
├── viewpack.v0.schema.json        # View pack schema
├── policysnapshot.v0.schema.json  # Policy snapshot schema
├── runstability.v0.schema.json    # Stability metrics schema
├── stabilityref.v0.schema.json    # Stability reference schema
└── sealreport.v0.schema.json      # Seal report schema

Makefile targets:
- make seal      # Run full seal process
- make validate  # Validate existing artifacts
- make clean     # Clean up seal artifacts
```

---

## Quick Start

### Running a Full Seal

```bash
# Option 1: Use Makefile (recommended)
make seal

# Option 2: Direct script invocation
python3 -m scripts.seal_release --run_id seal

# Option 3: Custom tick and runs
python3 -m scripts.seal_release --run_id seal --tick 0 --runs 12
```

**Expected Output:**
```
=== Abraxas Seal Release ===
Run ID: seal
Tick: 0
Dozen-run count: 12

Step 1: Running seal tick...
✓ Seal tick completed

Step 2: Validating artifacts...
✓ All artifacts valid

Step 3: Running dozen-run gate...
✓ All 12 runs match (determinism verified)

Step 4: Writing seal report...
✓ Seal report written to ./artifacts_seal/seal_report.json

=== Seal PASSED ===
Exit code: 0
```

### Validating Existing Artifacts

```bash
# Option 1: Use Makefile
make validate

# Option 2: Direct script invocation
python3 -m scripts.validate_artifacts \
  --artifacts_dir ./artifacts_seal \
  --run_id seal \
  --tick 0

# Option 3: Validate specific artifact
python3 -m scripts.validate_artifacts \
  --artifacts_dir ./artifacts_seal \
  --run_id seal \
  --tick 0 \
  --artifact_type runheader
```

---

## Seal Process Steps

### Step 1: Seal Tick Execution

**Purpose:** Generate artifacts in deterministic sandbox mode

**Process:**
1. Clear `./artifacts_seal` directory
2. Run `abraxas_tick()` with minimal deterministic inputs
3. Generate core artifacts:
   - `RunHeader.v0` - Run metadata
   - `TrendPack.v0` - Trend data
   - `ResultsPack.v0` - Results bundle
   - `ViewPack.v0` - View data
   - `RunIndex.v0` - Run index
   - `PolicySnapshot.v0` - Policy state

**Code:**
```python
from abraxas.runtime.tick import abraxas_tick

result = abraxas_tick(
    tick=0,
    run_id="seal",
    mode="sandbox",
    context={"x": 1},  # Minimal deterministic input
    artifacts_dir="./artifacts_seal",
    run_signal=lambda ctx: {"signal": 1},
    run_compress=lambda ctx: {"compress": 1},
    run_overlay=lambda ctx: {"overlay": 1},
    run_shadow_tasks={"sei": lambda ctx: {"sei": 0}},
)
```

**Expected Artifacts:**
```
./artifacts_seal/
├── seal_tick0000_runheader.json
├── seal_tick0000_trendpack.json
├── seal_tick0000_resultspack.json
├── seal_tick0000_viewpack.json
├── seal_tick0000_runindex.json
└── seal_tick0000_policysnapshot.json
```

---

### Step 2: Artifact Validation

**Purpose:** Verify all artifacts conform to JSON schemas

**Process:**
1. Discover all artifacts in `./artifacts_seal`
2. For each artifact:
   - Load artifact JSON
   - Identify schema from `"schema"` field
   - Load corresponding `.schema.json` from `schemas/`
   - Validate with `jsonschema` library
3. Report pass/fail for each artifact

**Code:**
```python
from scripts.validate_artifacts import validate_run

validation_result = validate_run(
    artifacts_dir="./artifacts_seal",
    run_id="seal",
    tick=0,
    schemas_dir="./schemas",  # Optional, defaults to ./schemas
)

# validation_result = {
#     "ok": True,
#     "artifacts_checked": 6,
#     "artifacts_valid": 6,
#     "artifacts_invalid": 0,
#     "errors": [],
# }
```

**Validation Rules:**
- Every artifact MUST have a `"schema"` field
- Schema MUST match a file in `schemas/` directory
- All required fields MUST be present
- All fields MUST match type constraints
- Provenance hashes MUST be 64-character hex strings (SHA-256)

**Common Validation Errors:**
```json
{
  "artifact": "seal_tick0000_runheader.json",
  "schema": "RunHeader.v0",
  "errors": [
    "'run_id' is a required property",
    "'started_at_utc' does not match pattern '^[0-9]{4}-[0-9]{2}-[0-9]{2}T.*Z$'"
  ]
}
```

---

### Step 3: Dozen-Run Gate

**Purpose:** Verify deterministic execution (12 identical runs)

**Process:**
1. Clear `./artifacts_gate` directory
2. Run seal tick 12 times into subdirectories:
   - `./artifacts_gate/run_0000/`
   - `./artifacts_gate/run_0001/`
   - ...
   - `./artifacts_gate/run_0011/`
3. Extract TrendPack SHA-256 from each run
4. Extract RunHeader SHA-256 from each run
5. Verify all 12 TrendPacks have identical hashes
6. Verify all 12 RunHeaders have identical hashes

**Code:**
```python
from abraxas.runtime.invariance_gate import dozen_run_tick_invariance_gate

def run_once(i: int, artifacts_dir: str):
    return abraxas_tick(
        tick=0,
        run_id="seal",
        mode="sandbox",
        context={"x": 1},
        artifacts_dir=artifacts_dir,
        # ... pipeline functions
    )

result = dozen_run_tick_invariance_gate(
    base_artifacts_dir="./artifacts_gate",
    runs=12,
    run_once=run_once,
)

# result.ok = True if all hashes match
# result.sha256s = [hash1, hash2, ..., hash12]  # All identical
# result.first_mismatch_run = None  # Or index of first mismatch
```

**Pass Criteria:**
- All 12 TrendPack SHA-256 hashes MUST be identical
- All 12 RunHeader SHA-256 hashes MUST be identical
- Any deviation → FAIL

**Example Output:**
```
Dozen-Run Gate Results:
  TrendPack hashes:
    Run 0: abc123...
    Run 1: abc123...  ✓
    Run 2: abc123...  ✓
    ...
    Run 11: abc123... ✓

  RunHeader hashes:
    Run 0: def456...
    Run 1: def456...  ✓
    Run 2: def456...  ✓
    ...
    Run 11: def456... ✓

✓ All 12 runs match - determinism verified!
```

---

### Step 4: Seal Report

**Purpose:** Generate SealReport.v0 with provenance chain

**Process:**
1. Collect metadata:
   - VERSION file content
   - abx_versions.json content
   - Git SHA (if available)
2. Record validation results
3. Record dozen-run gate results
4. Compute SHA-256 hash of entire report
5. Write `seal_report.json`

**SealReport.v0 Schema:**
```json
{
  "schema": "SealReport.v0",
  "run_id": "seal",
  "tick": 0,
  "version": "4.2.0",
  "version_pack": {
    "schema": "AbraxasVersionPack.v0",
    "abraxas": "4.2.0",
    "abx": "1.0.0"
  },
  "git_sha": "abc123def456...",
  "seal_timestamp_utc": "2026-01-11T18:45:00.000000Z",
  "validation": {
    "ok": true,
    "artifacts_checked": 6,
    "artifacts_valid": 6,
    "artifacts_invalid": 0,
    "errors": []
  },
  "dozen_gate": {
    "ok": true,
    "expected_trendpack_sha256": "abc123...",
    "expected_runheader_sha256": "def456...",
    "trendpack_sha256s": ["abc123...", "abc123...", ...],
    "runheader_sha256s": ["def456...", "def456...", ...],
    "first_mismatch_run": null,
    "divergence_kind": null
  },
  "provenance": {
    "seal_report_sha256": "fedcba987654...",
    "artifacts_dir": "./artifacts_seal",
    "gate_artifacts_dir": "./artifacts_gate"
  }
}
```

**Usage:**
```bash
# View seal report
cat ./artifacts_seal/seal_report.json | jq .

# Verify seal passed
jq -e '.validation.ok and .dozen_gate.ok' ./artifacts_seal/seal_report.json
# Exit code 0 = passed, 1 = failed

# Extract provenance hash
jq -r '.provenance.seal_report_sha256' ./artifacts_seal/seal_report.json
```

---

## Artifact Schemas

### Core Artifacts (Generated by abraxas_tick)

#### 1. RunHeader.v0
**Purpose:** Run metadata and provenance

```json
{
  "schema": "RunHeader.v0",
  "run_id": "seal",
  "tick": 0,
  "started_at_utc": "2026-01-11T18:00:00.000000Z",
  "mode": "sandbox",
  "provenance": {
    "inputs_hash": "abc123...",
    "config_hash": "def456...",
    "git_sha": "fedcba..."
  }
}
```

**Schema:** `schemas/runheader.v0.schema.json`

---

#### 2. TrendPack.v0
**Purpose:** Trend data and signals

```json
{
  "schema": "TrendPack.v0",
  "run_id": "seal",
  "tick": 0,
  "trends": [...],
  "provenance_hash": "abc123..."
}
```

**Schema:** `schemas/trendpack.v0.schema.json`

---

#### 3. ResultsPack.v0
**Purpose:** Execution results bundle

```json
{
  "schema": "ResultsPack.v0",
  "run_id": "seal",
  "tick": 0,
  "results": {...},
  "provenance_hash": "def456..."
}
```

**Schema:** `schemas/resultspack.v0.schema.json`

---

#### 4. ViewPack.v0
**Purpose:** View/rendering data

```json
{
  "schema": "ViewPack.v0",
  "run_id": "seal",
  "tick": 0,
  "views": [...],
  "provenance_hash": "fedcba..."
}
```

**Schema:** `schemas/viewpack.v0.schema.json`

---

#### 5. RunIndex.v0
**Purpose:** Run indexing metadata

```json
{
  "schema": "RunIndex.v0",
  "run_id": "seal",
  "tick": 0,
  "index": {...}
}
```

**Schema:** `schemas/runindex.v0.schema.json`

---

#### 6. PolicySnapshot.v0
**Purpose:** Immutable policy state at execution time

```json
{
  "schema": "PolicySnapshot.v0",
  "run_id": "seal",
  "tick": 0,
  "policies": {...},
  "provenance_hash": "abc123..."
}
```

**Schema:** `schemas/policysnapshot.v0.schema.json`

---

### Validation Artifacts

#### 7. RunStability.v0
**Purpose:** Stability metrics for dozen-run gate

**Schema:** `schemas/runstability.v0.schema.json`

---

#### 8. StabilityRef.v0
**Purpose:** Stability reference baseline

**Schema:** `schemas/stabilityref.v0.schema.json`

---

#### 9. SealReport.v0
**Purpose:** Seal validation report

**Schema:** `schemas/sealreport.v0.schema.json`

---

## Validation Rules

### Universal Rules (All Artifacts)

1. **Schema Field Required**
   - Every artifact MUST have a `"schema"` field
   - Format: `"<ArtifactType>.v<MajorVersion>"`
   - Example: `"RunHeader.v0"`

2. **Provenance Hash Format**
   - All `provenance_hash` fields MUST be 64-character hex strings
   - SHA-256 hashes only
   - Lowercase hex (a-f, 0-9)

3. **Timestamp Format**
   - All `*_utc` fields MUST use ISO8601 with 'Z' timezone
   - Format: `YYYY-MM-DDTHH:MM:SS.ffffffZ`
   - Example: `2026-01-11T18:00:00.000000Z`

4. **Deterministic Ordering**
   - All arrays MUST have stable, deterministic ordering
   - Use explicit sort keys (e.g., alphabetical, chronological)
   - Never rely on insertion order without explicit sorting

---

### Artifact-Specific Rules

#### RunHeader.v0
- `run_id` MUST be a non-empty string
- `tick` MUST be >= 0
- `mode` MUST be one of: `"sandbox"`, `"production"`, `"test"`
- `started_at_utc` MUST be valid ISO8601 timestamp

#### TrendPack.v0
- `trends` MUST be an array (can be empty)
- Each trend MUST have deterministic ordering
- `provenance_hash` MUST be SHA-256 of canonical trends JSON

#### PolicySnapshot.v0
- `policies` MUST be a dictionary
- Policy provenance MUST be traceable to git SHA
- Immutable once written (never modify existing snapshots)

---

## Dozen-Run Gate

### Purpose

The dozen-run gate ensures **absolute determinism** by running the same tick 12 times and verifying identical outputs.

### Why 12 Runs?

- Statistical significance (99.9% confidence in determinism)
- Catches intermittent non-determinism (e.g., timestamp leaks)
- Balances thoroughness vs runtime cost

### What Gets Compared?

1. **TrendPack SHA-256**: Primary determinism signal
2. **RunHeader SHA-256**: Metadata consistency check

### Failure Scenarios

#### Scenario 1: Timestamp Leak
```
Run 0: started_at_utc = "2026-01-11T18:00:00.123456Z"
Run 1: started_at_utc = "2026-01-11T18:00:01.234567Z"  ✗ Different!
```

**Cause:** `datetime.now()` called instead of deterministic timestamp  
**Fix:** Use fixed timestamp from inputs or config

---

#### Scenario 2: Random State
```
Run 0: trend_score = 0.7823
Run 1: trend_score = 0.5491  ✗ Different!
```

**Cause:** `random.random()` without seeding  
**Fix:** Use deterministic random seed: `random.seed(42)`

---

#### Scenario 3: Dict Ordering
```
Run 0: {"b": 1, "a": 2}  → hash: abc123
Run 1: {"a": 2, "b": 1}  → hash: abc123  ✓ Matches (same content)

But if comparison is done on JSON strings:
Run 0: '{"b":1,"a":2}'  → hash: abc123
Run 1: '{"a":2,"b":1}'  → hash: def456  ✗ Different!
```

**Cause:** JSON serialization without `sort_keys=True`  
**Fix:** Use canonical JSON: `json.dumps(obj, sort_keys=True)`

---

### Debugging Gate Failures

```bash
# Run seal with verbose output
python3 -m scripts.seal_release --run_id seal --tick 0 --runs 12 --verbose

# Compare first two runs manually
diff \
  ./artifacts_gate/run_0000/seal_tick0000_trendpack.json \
  ./artifacts_gate/run_0001/seal_tick0000_trendpack.json

# Check for timestamp variations
grep -r "started_at_utc" ./artifacts_gate/ | sort | uniq
# Should show only ONE unique timestamp

# Check for random variations
jq '.trends[0].score' ./artifacts_gate/run_*/seal_tick0000_trendpack.json | sort | uniq -c
# Should show "12 <same_value>"
```

---

## Troubleshooting

### Problem: Seal Fails at Validation Step

**Symptoms:**
```
Step 2: Validating artifacts...
✗ Validation failed
  seal_tick0000_runheader.json: 'run_id' is a required property
```

**Solution:**
1. Check artifact generation code
2. Ensure all required fields are populated
3. Validate schema: `python3 -m scripts.validate_artifacts --artifact_type runheader`

---

### Problem: Dozen-Run Gate Fails

**Symptoms:**
```
Step 3: Running dozen-run gate...
✗ Run 2 diverged from expected
  Expected TrendPack hash: abc123...
  Actual TrendPack hash:   def456...
```

**Solution:**
1. Check for timestamp leaks: `grep "utc" artifacts_gate/run_*/seal_tick0000_trendpack.json`
2. Check for random calls: Search for `random.` in pipeline code
3. Check for dict ordering: Ensure `json.dumps(..., sort_keys=True)`
4. Run with `--verbose` to see detailed diff

---

### Problem: Seal Report Not Generated

**Symptoms:**
```
Step 4: Writing seal report...
✗ Failed to write seal report
```

**Solution:**
1. Check `./artifacts_seal` directory exists and is writable
2. Verify VERSION file exists: `cat VERSION`
3. Verify abx_versions.json exists: `cat abx_versions.json`
4. Check Python import: `python3 -c "from scripts.seal_release import write_seal_report"`

---

### Problem: Schemas Not Found

**Symptoms:**
```
✗ Schema file not found: schemas/runheader.v0.schema.json
```

**Solution:**
1. Verify schemas directory: `ls -1 schemas/*.schema.json`
2. Check artifact schema field matches filename
3. Ensure schema files are tracked in git: `git ls-files schemas/`

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Seal Validation

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  seal:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install jsonschema

      - name: Run seal validation
        run: make seal

      - name: Upload seal report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: seal-report
          path: ./artifacts_seal/seal_report.json

      - name: Fail if seal failed
        run: |
          jq -e '.validation.ok and .dozen_gate.ok' ./artifacts_seal/seal_report.json
```

---

### Pre-Release Checklist

Before creating a release:

- [ ] Run `make seal` locally
- [ ] Verify seal report: `cat ./artifacts_seal/seal_report.json | jq '.validation.ok, .dozen_gate.ok'`
- [ ] Check VERSION file matches release version
- [ ] Check abx_versions.json matches component versions
- [ ] Commit seal report to git (optional but recommended for audit trail)
- [ ] Tag release with seal report hash:
  ```bash
  SEAL_HASH=$(jq -r '.provenance.seal_report_sha256' ./artifacts_seal/seal_report.json)
  git tag -a "v4.2.0-seal-${SEAL_HASH:0:8}" -m "Release 4.2.0 (sealed)"
  ```

---

## Best Practices

### 1. Seal on Every Release
- Run `make seal` before tagging any release
- Include seal report in release notes
- Track seal hashes in CHANGELOG.md

### 2. Version Seal Schemas
- Never modify existing schemas (e.g., RunHeader.v0)
- Create new versions for breaking changes (e.g., RunHeader.v1)
- Document schema changes in schemas/CHANGELOG.md

### 3. Automate in CI/CD
- Run seal on main branch commits
- Fail builds if seal fails
- Archive seal reports as build artifacts

### 4. Audit Trail
- Commit seal reports to git
- Reference seal hashes in git tags
- Include seal provenance in production deployments

### 5. Test Locally First
- Always run `make seal` locally before pushing
- Fix determinism issues locally (faster iteration)
- Use `--verbose` for debugging

---

## FAQ

**Q: Why does seal take so long?**  
A: The dozen-run gate runs 12 identical executions. This is intentional to ensure absolute determinism.

**Q: Can I skip the dozen-run gate?**  
A: Not recommended. The gate catches intermittent non-determinism that single runs miss.

**Q: What if I need to modify a sealed artifact?**  
A: Never modify sealed artifacts. Create a new version with incremented version number.

**Q: Can I run seal with different inputs?**  
A: Yes, but seal uses minimal deterministic inputs by design. Custom inputs should be reproducible.

**Q: How do I verify a sealed release?**  
A: Run `make seal` with the same version and compare seal report hashes.

---

## See Also

- **Artifact Schemas:** `schemas/*.schema.json`
- **Seal Script:** `scripts/seal_release.py`
- **Validate Script:** `scripts/validate_artifacts.py`
- **Makefile Targets:** `Makefile` (seal, validate, clean)
- **Provenance Guide:** `docs/provenance/PROVENANCE_GUIDE.md` (if exists)
- **Runtime Infrastructure:** `abraxas/runtime/` (policy_snapshot, invariance_gate, tick)

---

**End of Seal Validation Guide**
