# Abraxas Acceptance Test Suite

This directory contains the canonical acceptance test specification and harness for Abraxas release readiness verification.

## Overview

The acceptance suite defines **"Abraxas is doing its job"** through a series of hard gates:

1. **A1**: 12-run determinism (hash stability)
2. **B1**: Schema validation (artifact contracts)
3. **C2**: Evidence gating (no phantom evidence)
4. **D1**: Shadow isolation (non-causal metrics)
5. **E2**: Pointer auditability (narrative grounding)

## Quick Start

### Run the Full Suite

```bash
python tools/acceptance/run_acceptance_suite.py
```

### With Custom Input

```bash
python tools/acceptance/run_acceptance_suite.py \
  --input tests/fixtures/acceptance/baseline_input.json \
  --runs 12 \
  --output out/acceptance/
```

## Expected Output

```
Abraxas Acceptance Suite v1.0
================================================================================

[A1_12_RUN_DETERMINISM] 12-run determinism.................. PASS
     Hash: a3f5e9c8... (identical across 12 runs)

[B1_SCHEMA_VALIDATION] Schema validation.................... PASS
     oracle_envelope_v2: VALID
     narrative_bundle_v1: VALID

[C2_EVIDENCE_GATING] Evidence gating........................ PASS
     Removed source: "twitter_trends"
     Dependent field "social_velocity": not_computable ✓

[D1_SHADOW_ISOLATION] Shadow isolation...................... PASS
     Forecast hash identical with/without shadow detectors

[E2_POINTER_AUDITABILITY] Pointer auditability.............. PASS
     All 47 pointers resolved successfully

================================================================================
VERDICT: ✅ PASS (5/5 hard gates)
Abraxas is doing its job.
```

## Files

- **`ABRAXAS_ACCEPTANCE_SPEC_v1.md`**: Canonical specification (authoritative)
- **`README.md`**: This file (usage guide)

## Integration

### Pre-Release Gate

Add to CI/CD pipeline:

```yaml
# .github/workflows/acceptance.yml
- name: Run Acceptance Suite
  run: |
    python tools/acceptance/run_acceptance_suite.py
    if [ $? -ne 0 ]; then
      echo "❌ Acceptance suite FAILED - blocking release"
      exit 1
    fi
```

### Dashboard Integration

The acceptance suite can generate a status artifact for the dashboard:

```bash
python tools/acceptance/run_acceptance_suite.py \
  --output out/acceptance/

# Read result
cat out/acceptance/acceptance_result.json
```

## Failure Handling

When a hard gate fails:

1. **Block release**: Do not deploy
2. **Check drift report**: `out/acceptance/acceptance_failures.jsonl`
3. **Classify cause**: See F1 taxonomy in spec
4. **Fix root cause**: Address determinism/schema/evidence issue
5. **Re-run suite**: Verify fix

## Development

### Adding New Tests

1. Add test method to `AcceptanceTestSuite` class in `run_acceptance_suite.py`
2. Update spec document if new hard gate
3. Run full suite to verify

### Updating Spec

The specification is **canonical**. Any changes must:

1. Update version in `ABRAXAS_ACCEPTANCE_SPEC_v1.md`
2. Follow SemVer (breaking = major, additive = minor, fix = patch)
3. Document in changelog
4. Get team review

## Versioning

- **v1.0.0** (2026-01-01): Initial canonical specification

## Authority

This suite is the **canonical definition** of release readiness. Any conflict between this suite and informal documentation is a bug in the informal documentation.

**Maintainer**: Abraxas Core Team
**Review Cycle**: Quarterly or on-demand for breaking changes
