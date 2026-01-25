# Seal Validation Guide

**Version:** 1.1.0  
**Last Updated:** 2026-01-11  
**Purpose:** Operational guide to Abraxas seal validation for production releases

---

## Overview

Seal validation enforces deterministic, provenance-tracked release readiness by running a minimal tick, validating emitted artifacts, and verifying invariance across 12 runs. The workflow is implemented by:

- `scripts/seal_release.py` — orchestrates the seal run + dozen-run gate + report
- `scripts/validate_artifacts.py` — validates artifacts against JSON schemas

---

## Quick Start

```bash
# Full seal (recommended)
make seal

# Explicit run
python3 -m scripts.seal_release --run_id seal --tick 0 --runs 12
```

Expected CLI flow:
```
[1/4] Running seal tick into artifacts_seal...
[2/4] Validating artifacts...
[3/4] Running dozen-run gate (12 runs) into artifacts_gate...
[4/4] Writing SealReport.v0...
SEAL RELEASE: PASS
```

Validate existing artifacts:
```bash
make validate
# or
python3 -m scripts.validate_artifacts --artifacts_dir ./artifacts_seal --run_id seal --tick 0
```

---

## Seal Process Steps

### Step 1: Seal Tick Execution

Runs a deterministic sandbox tick with minimal pipeline functions to generate core artifacts.

**Artifacts written to `./artifacts_seal`:**
```
artifacts_seal/
├── runs/
│   ├── seal.runheader.json
│   └── seal.sealreport.json
├── run_index/
│   └── seal/000000.runindex.json
├── viz/
│   └── seal/000000.trendpack.json
├── results/
│   └── seal/000000.resultspack.json
├── view/
│   └── seal/000000.viewpack.json
└── manifests/...
```

### Step 2: Artifact Validation

`validate_artifacts.py` checks each artifact against its schema:

- `RunIndex.v0`
- `TrendPack.v0`
- `ResultsPack.v0`
- `RunHeader.v0`
- `ViewPack.v0` (if present)
- `RunStability.v0` / `StabilityRef.v0` (if present)

The validator is deterministic and uses the repo `schemas/` directory.

### Step 3: Dozen-Run Gate

Runs the seal tick 12 times into `./artifacts_gate` and compares hashes:

- TrendPack SHA-256 hashes must match across all runs.
- RunHeader SHA-256 hashes must match across all runs.

Any divergence fails the gate.

### Step 4: Seal Report

Writes `SealReport.v0` to `./artifacts_seal/runs/<run_id>.sealreport.json` and prints the report hash.

---

## SealReport.v0 Schema (Actual Payload)

```json
{
  "schema": "SealReport.v0",
  "version": "<VERSION file>",
  "version_pack": {"schema": "AbraxasVersionPack.v0", "abraxas": "<version>"},
  "seal_tick_artifacts": {
    "trendpack": "...",
    "trendpack_sha256": "...",
    "results_pack": "...",
    "results_pack_sha256": "...",
    "runindex": "...",
    "runindex_sha256": "...",
    "viewpack": "...",
    "viewpack_sha256": "...",
    "run_header": "...",
    "run_header_sha256": "..."
  },
  "validation_result": {
    "ok": true,
    "validated_ticks": [0],
    "failures": []
  },
  "dozen_gate_result": {
    "ok": true,
    "expected_trendpack_sha256": "...",
    "expected_runheader_sha256": "...",
    "first_mismatch_run": null,
    "divergence_kind": null
  },
  "ok": true
}
```

Schema file: `schemas/sealreport.v0.schema.json`.

---

## Validation Rules

**Universal:**
- Each artifact must declare a `schema` field matching a file in `schemas/`.
- Required fields must be present with correct types.
- Hash fields are 64-char lowercase SHA-256.
- Ordering must be deterministic (sorted keys, stable lists).

**Dozen-run gate:**
- TrendPack SHA-256 must match across all runs.
- RunHeader SHA-256 must match across all runs.

---

## Troubleshooting

**Validation fails**
- Run: `python3 -m scripts.validate_artifacts --artifacts_dir ./artifacts_seal --run_id seal --tick 0`
- Inspect `failures` in the JSON output.

**Dozen-run gate fails**
- Check for timestamp leaks in artifacts.
- Ensure any randomness is seeded and deterministic.

---

## CI/CD Integration (Minimal)

```yaml
- name: Seal validation
  run: make seal

- name: Fail if seal failed
  run: |
    jq -e '.ok == true' ./artifacts_seal/runs/seal.sealreport.json
```

---

## References

- `scripts/seal_release.py`
- `scripts/validate_artifacts.py`
- `schemas/*.schema.json`
- `Makefile` (seal/validate/clean targets)

---

**End of Seal Validation Guide**
