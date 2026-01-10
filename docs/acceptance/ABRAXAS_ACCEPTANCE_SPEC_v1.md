# Abraxas Acceptance Test Specification v1.0

**Version**: 1.0.0
**Status**: Canonical
**Purpose**: Define the hard gates for release readiness and operational trust

---

## Abstract

"Abraxas is doing its job" is defined as an acceptance test suite: **deterministic, provenance-embedded, audit-ready, drift-resilient**. This becomes the hard gate for releases and the dashboard's "green/red" truth panel.

---

## Scope & Constraints

### Core Principles

1. **No mock data**: Use real or inferential inputs only
2. **Shadow ≠ Forecast**: Shadow metrics may observe, never influence
3. **Evidence gating is binary**: evidence present → computed; absent → not_computable
4. **12-run invariance**: Default stability gate for determinism verification

### Artifact Types (Minimum)

- `oracle_envelope_v2`: Canonical output
- `narrative_bundle_v1`: Renderer output (grounded)
- `drift_report_v1`: Shadow correlation output

---

## A) Determinism & Invariance (Core Gate)

### A1 — Single-input determinism

**Given**: A fixed input bundle `I0`
**When**: Run Abraxas N=12 times
**Then**: The canonical envelope hash must be identical across runs

**Pass condition**: `hash(env_run_1) == hash(env_run_2) == ... == hash(env_run_12)`

**Required output fields**:
- `artifact_id` (may differ per run; allowed)
- `input_hash` (must be identical)
- `determinism_hash` or canonical JSON hash (must be identical)

**Verdict**:
- ✅ **PASS** if identical hash across all runs
- ❌ **FAIL** if any mismatch → classify drift cause (see Section F)

---

### A2 — Order invariance

**Given**: Same semantic inputs with list order permuted
**Then**: Output hash unchanged

**Pass**: Canonical normalization exists, ordering choices are stable

---

### A3 — Time invariance

**Given**: System clock changes (or run at different times)
**Then**: Output content (excluding timestamps) is identical

**Pass**: Runtime time data is fenced to metadata only

---

## B) Artifact Contract & Schema Validation

### B1 — Schema-valid output

**Given**: Any completed run
**Then**: `oracle_envelope_v2` validates against its JSON schema

**Pass**: Validator runs in pipeline; invalid output produces a schema-valid failure artifact

---

### B2 — Versioning discipline

**Then**: `schema_version` exists and matches SemVer

**Pass**: Breaking changes bump major; additive bump minor; fixes bump patch

---

## C) Provenance & Evidence Gating

### C1 — Provenance footer required

**Then**: Envelope includes:
- `input_hash`
- `created_at`
- `source_count` (or explicit "unknown")
- `commit` (if available)
- `missing_inputs[]`
- `not_computable[]`

**Verdict**:
- ✅ **PASS** if present and structured
- ❌ **FAIL** if missing or freeform

---

### C2 — Evidence gating (negative test)

**Given**: Remove a required evidence source from inputs
**Then**: Dependent outputs must flip to `not_computable` (or be omitted)
**And**: Narrative must not mention the dependent claim

**Purpose**: The "no phantom evidence" test

---

## D) Shadow Lane Isolation

### D1 — Shadow metrics are non-causal

**Given**: Shadow detectors enabled/disabled
**Then**: Forecast outputs must be identical (hash-equal)

**Pass**: Shadow outputs exist only in shadow namespace/artifacts/logs

---

### D2 — Promotion gate required

**Then**: No emergent metric influences predictions without governance promotion record

**Pass**: A "promotion ledger" entry is required to change forecast weighting

---

## E) Renderer Integrity (Resonance Narratives)

### E1 — Renderer determinism

**Given**: A fixed envelope
**Then**: Narrative bundle hash identical across renders

---

### E2 — Pointer auditability

**Then**: Every `signal_summary.pointer`, `motifs.pointer`, `what_changed.pointer` resolves against the envelope

**Pass**: Pointer resolver test passes

---

### E3 — No invention

**Then**: Narrative cannot contain claims not present in envelope fields

**Operational definition**: Every narrative item is either:
- Direct value rendering from pointer, OR
- Explicitly tagged overlay and non-causal unless evidence present

---

## F) Drift Detection & Classification

When invariance fails (A1), the system must emit a drift report.

### F1 — Drift report required on mismatch

**Then**: Classify mismatch as one of:
- `NONDETERMINISM_RANDOMNESS`
- `TIME_DEPENDENCE`
- `ORDERING_INSTABILITY`
- `EXTERNAL_SOURCE_VARIANCE`
- `VERSION_SKEW`
- `UNINITIALIZED_STATE`
- `UNKNOWN`

---

### F2 — Minimum drift payload

- Differing hashes
- Pointers/paths that differ (diff list)
- Suspected class
- Run metadata (commit, env vars whitelist, seeds)

---

## G) Event Correlation Output Contract (Shadow Artifact)

### G1 — Drift report schema-valid

**Then**: `drift_report_v1` validates against schema

---

### G2 — Evidence pointers required

**Then**: Every cluster includes `artifact_id` + pointer evidence refs

**Pass**: Pointer integrity test passes

---

## H) Acceptance Thresholds (Definition of "Doing Its Job")

Abraxas is **"doing its job"** when, on your primary execution environment:

1. **Hard gates** (all PASS):
   - A1: 12-run determinism
   - B1: Schema validation
   - C2: Evidence gating
   - D1: Shadow isolation
   - E2: Pointer auditability

2. **No FAIL** in any hard gate across a rolling window of ≥30 runs

3. **Drift classification exists** for any mismatch events (never silent)

---

## What This Spec Doesn't Demand (Yet)

- Accuracy of predictions (that's calibration + empirical backtesting)
- Live UI
- Database
- Real-time updates

This is about **trust and legibility**—the substrate for everything else.

---

## Implementation Requirements

### Test Harness Entry Point

- `tools/acceptance/run_acceptance_suite.py` (or TS equivalent)

### Acceptance Test Suite Components

1. **12-run invariance test**: Verify hash stability across repeated runs
2. **Schema validation hooks**: Validate all artifacts against JSON schemas
3. **Evidence gating test**: Verify `not_computable` behavior when inputs missing
4. **Shadow isolation test**: Verify forecasts unchanged when shadow metrics toggled
5. **Pointer integrity test**: Verify all narrative pointers resolve correctly
6. **Drift classifier**: Categorize and report any determinism failures

---

## Test Execution Protocol

### Standard Run

```bash
python tools/acceptance/run_acceptance_suite.py \
  --input tests/fixtures/acceptance/baseline_input.json \
  --runs 12 \
  --output out/acceptance/
```

### Expected Output

```
Abraxas Acceptance Suite v1.0
================================================================================

[A1] 12-run determinism................................................. PASS
     Hash: a3f5e9c8... (identical across 12 runs)

[B1] Schema validation................................................. PASS
     oracle_envelope_v2: VALID
     narrative_bundle_v1: VALID

[C2] Evidence gating................................................... PASS
     Removed source: "twitter_trends"
     Dependent field "social_velocity": not_computable ✓

[D1] Shadow isolation.................................................. PASS
     Forecast hash identical with/without shadow detectors

[E2] Pointer auditability.............................................. PASS
     All 47 pointers resolved successfully

================================================================================
VERDICT: ✅ PASS (5/5 hard gates)
Abraxas is doing its job.
```

---

## Failure Handling

### On Hard Gate Failure

1. **Block release**: Do not proceed with deployment
2. **Emit drift report**: Generate `drift_report_v1` artifact
3. **Classify cause**: Apply F1 classification taxonomy
4. **Log to ledger**: Append to `out/ledger/acceptance_failures.jsonl`

### Drift Report Example

```json
{
  "timestamp": "2026-01-01T19:30:00Z",
  "test": "A1_12_RUN_DETERMINISM",
  "verdict": "FAIL",
  "classification": "ORDERING_INSTABILITY",
  "differing_hashes": [
    "a3f5e9c8...",
    "b2d4f1a7..."
  ],
  "diff_paths": [
    "$.claims[*].sources"
  ],
  "metadata": {
    "commit": "72da34a",
    "env": "production",
    "python_version": "3.11.7"
  }
}
```

---

## Versioning

- **v1.0.0** (2026-01-01): Initial canonical specification
- Future versions must maintain backward compatibility or bump major version

---

## Authority

This specification is **canonical** and takes precedence over informal documentation. Any conflict between this spec and implementation behavior is a bug in implementation.

**Maintainer**: Abraxas Core Team
**Review Cycle**: Quarterly or on-demand for breaking changes
