# NOESIS-Q1 Qualification Artifacts Implementation Plan

**Goal**: Create complete NOESIS-Q1 qualification package (spec, fixtures, tests, receipt) following the established HYPERLEX-Q1 and SEMION-Q1 patterns, to formalize NOESIS-Q1 from `PROVISIONALLY_QUALIFIED` (receipt `28c840dd`) to full `PROVISIONALLY_QUALIFIED` with all gates passing.

---

## Current Context / Assumptions

- **Repository**: `/Users/appliedalchemylabs/Abraxas` (main branch, clean, 93 tests passing)
- **NOESIS Status**: Currently `PROVISIONALLY_QUALIFIED` per Master Index 2026-09-19 with receipt SHA `28c840dd`, PR #31 draft
- **Dependencies**: None (NOESIS is first in pipeline after Hyperlex/Semion)
- **Unlocks**: HYPERLEX→NOESIS pairwise, NOESIS→TRUTINA, NOESIS→ABRAXAS pairwise
- **Existing Implementation**: 
  - `abraxas/evidence/verifiers/latent.py` — LatentStructureVerifier + NoesisEvidenceProvider (fully implemented)
  - Evidence type: `EvidenceType.LATENT_STRUCTURAL`
  - Engine: `noesis` / `noesis.latent.v1`
- **Canonical Boundary**: Advisory only, `semantic_truth=false`, `valid_for_forecast=false`, `lane=shadow`

---

## Architecture / Proposed Approach

Following the exact pattern established by HYPERLEX-Q1 and SEMION-Q1:

1. **Specification Document** (`abraxas/evidence/noesis_latent_v1.spec.md`) — Wire-shape contract, 6 gates, invariants, Peircean-level detail for latent structure
2. **Deterministic Fixtures** (`abraxas/evidence/noesis_q1_fixtures.yaml`) — 8+ fixtures covering valid latent captures, edge conditions, negative cases
3. **Test Suite** (`abraxas/evidence/test_noesis_q1.py`) — 30+ tests covering spec compliance, latent analysis math, verifier, integration, authority boundary
4. **Qualification Receipt** (`abraxas/evidence/noesis_q1_receipt.json`) — `PROVISIONALLY_QUALIFIED` with all gates passing

All artifacts go in `abraxas/evidence/` alongside existing Q1 packages.

---

## Step-by-Step Tasks

### Task 1: Create NOESIS-Q1 Specification Document

**File**: `abraxas/evidence/noesis_latent_v1.spec.md`

**Content Structure**:
- Header: Status, Version, Receipt Reference, Dependencies (none), Canonical Boundary
- 6 Gates Table (Q1-SPEC, Q1-FIXTURE, Q1-ADAPTER, Q1-SCHEMA, Q1-VERIFIER, Q1-ARBITRATION)
- Wire-Shape Contract: NoesisObservation (v1) → Abraxas EvidenceEnvelope
- Latent Structure Schema: conditions, activations, interventions, counterfactuals
- Invariants (7 items: authority, advisory, no forecast, no governance, shadow lane, feature flag, deterministic)
- Test Fixtures Overview (8 fixtures)
- Qualification Receipt Structure
- Pairwise Conformance (HYPERLEX→NOESIS, NOESIS→TRUTINA, NOESIS→ABRAXAS)
- Execution Notes

**Verification**: `cat abraxas/evidence/noesis_latent_v1.spec.md | head -50`

---

### Task 2: Create NOESIS-Q1 Deterministic Fixtures

**File**: `abraxas/evidence/noesis_q1_fixtures.yaml`

**Fixtures** (8 total):
1. `fixture_valid_baseline_intervention` — Baseline + intervention with coherent structure
2. `fixture_valid_multiple_conditions` — baseline, intervention, counterfactual, ablation, noise, patch
3. `fixture_valid_high_coherence` — High structural coherence (>0.85), low sensitivity (<0.2)
4. `fixture_valid_low_coherence` — Low coherence (<0.4), high sensitivity (>0.6) → should escalate
5. `fixture_empty_captures` — Empty captures list → error handling
6. `fixture_mismatched_dimensions` — Captures with different activation dimensions → error
7. `fixture_missing_baseline` — No baseline condition → error
8. `fixture_single_capture` — Single capture edge case → manifold integrity = 1.0
9. `fixture_semantic_truth_true` — Negative: semantic_truth=true rejected
9. `fixture_non_advisory_authority` — Negative: authority.kind != advisory rejected
10. `fixture_valid_for_forecast_true` — Negative: valid_for_forecast=true rejected via assert

**Verification**: `python -c "import yaml; print(len(yaml.safe_load(open('abraxas/evidence/noesis_q1_fixtures.yaml'))))"`

---

### Task 3: Create NOESIS-Q1 Test Suite

**File**: `abraxas/evidence/test_noesis_q1.py`

**Test Classes** (following HYPERLEX-Q1/SEMION-Q1 pattern exactly):

```python
class TestNOESIS_Q1_Specification:
    - test_spec_file_exists
    - test_spec_contains_required_sections

class TestNOESIS_Q1_LatentAnalysis:  # Core math validation
    - test_cosine_similarity
    - test_l2_distance
    - test_kl_divergence
    - test_rsa_matrix_computation
    - test_rsa_correlation
    - test_analyze_latent_structure_baseline
    - test_analyze_latent_structure_multiple_conditions
    - test_compute_manifold_integrity
    - test_calibrate_confidence_via_brier
    - test_compute_atomic_brier

class TestNOESIS_Q1_Fixtures:  # Fixture-driven tests
    - test_fixture_valid_baseline_intervention
    - test_fixture_valid_multiple_conditions
    - test_fixture_valid_high_coherence
    - test_fixture_valid_low_coherence
    - test_fixture_empty_captures
    - test_fixture_mismatched_dimensions
    - test_fixture_missing_baseline
    - test_fixture_single_capture

class TestNOESIS_Q1_AuthorityBoundary:
    - test_semantic_truth_true_rejected
    - test_non_advisory_authority_rejected
    - test_assert_not_authoritative_forecast
    - test_assert_not_authoritative_authority
    - test_assert_not_authoritative_semantic_truth
    - test_promote_to_canonical_blocked

class TestNOESIS_Q1_Verifier:
    - test_latent_verifier_exists
    - test_latent_verifier_verify_passed
    - test_latent_verifier_verify_escalate
    - test_latent_verifier_verify_borderline_jev
    - test_latent_verifier_calibrated_confidence

class TestNOESIS_Q1_Provider:
    - test_provider_engine_identity
    - test_provider_produces_evidence
    - test_provider_provenance_completeness

class TestNOESIS_Q1_Integration:
    - test_noesis_evidence_through_production_arbiter
    - test_noesis_evidence_through_six_gate_governor

class TestNOESIS_Q1_FeatureFlag:
    - test_noesis_feature_flag_behavior

class TestNOESIS_Q1_Schema:
    - test_subsystem_yaml_exists
```

**Verification**: `python -m pytest abraxas/evidence/test_noesis_q1.py -v --tb=short`

---

### Task 4: Create NOESIS-Q1 Qualification Receipt

**File**: `abraxas/evidence/noesis_q1_receipt.json`

```json
{
  "receipt_id": "NOESIS-Q1-2026-10-04-001",
  "receipt_type": "qualification",
  "subsystem": "noesis_latent_v1",
  "status": "PROVISIONALLY_QUALIFIED",
  "issued_at": "2026-10-04T00:00:00Z",
  "issued_by": "operator",
  "gates": {
    "Q1-SPEC": { "passed": true, "artifact": "abraxas/evidence/noesis_latent_v1.spec.md" },
    "Q1-FIXTURE": { "passed": true, "artifact": "abraxas/evidence/noesis_q1_fixtures.yaml" },
    "Q1-ADAPTER": { "passed": true, "artifact": "abraxas/evidence/test_noesis_q1.py" },
    "Q1-SCHEMA": { "passed": true, "artifact": "noesis.latent.v1 (latent structure schema)" },
    "Q1-VERIFIER": { "passed": true, "artifact": "abraxas/evidence/verifiers/latent.py" },
    "Q1-ARBITRATION": { "passed": true, "artifact": "integration tests in test_noesis_q1.py" }
  },
  "sha256": "pending_operator_computation",
  "notes": [
    "NOESIS provides LATENT_STRUCTURAL evidence only",
    "Structural coherence + intervention sensitivity + RSA correlation validated",
    "Pairwise HYPERLEX→NOESIS unblocked upon HYPERLEX-Q1 completion ✅",
    "Pairwise NOESIS→TRUTINA unblocked upon TRUTINA-Q1",
    "Pairwise NOESIS→ABRAXAS unblocked upon ABRAXAS-Q1",
    "EXP-001 remains DEFERRED until AC-EIC-G1"
  ]
}
```

**Verification**: `cat abraxas/evidence/noesis_q1_receipt.json | jq .`

---

### Task 5: Run Full Test Suite & Validate

**Commands**:
```bash
cd /Users/appliedalchemylabs/Abraxas
python -m pytest abraxas/evidence/test_noesis_q1.py -v --tb=short
python -m pytest tests/evidence tests/integration tests/chaos abraxas/evidence/test_hyperlex_q1.py tests/test_hyperlex_instrument_evidence.py abraxas/evidence/test_semion_q1.py abraxas/evidence/test_noesis_q1.py -q
```

**Expected**: All tests passing (target: 93 + ~30 = ~123 tests)

---

### Task 6: Git Commit & Push

```bash
cd /Users/appliedalchemylabs/Abraxas
git add abraxas/evidence/noesis_latent_v1.spec.md abraxas/evidence/noesis_q1_fixtures.yaml abraxas/evidence/test_noesis_q1.py abraxas/evidence/noesis_q1_receipt.json
git commit -m "feat: NOESIS-Q1 qualification artifacts (spec, fixtures, tests, receipt)

Add complete NOESIS-Q1 qualification package:
- noesis_latent_v1.spec.md: Specification with latent structure wire-shape, 6 gates, invariants
- noesis_q1_fixtures.yaml: 10 deterministic fixtures (valid captures, edge cases, negatives)
- test_noesis_q1.py: 30+ tests (latent analysis math, fixtures, verifier, provider, integration)
- noesis_q1_receipt.json: PROVISIONALLY_QUALIFIED receipt formalizing 28c840dd

All tests passing. HYPERLEX→NOESIS pairwise UNBLOCKED. NOESIS→TRUTINA, NOESIS→ABRAXAS pending.
CANON-SHADOW / ADVISORY_ONLY. No canon mutation."
git push origin main
```

---

## Tests / Validation (TDD Cycle per Task)

| Task | Test Command | Expected Output |
|------|--------------|-----------------|
| 1 | `cat abraxas/evidence/noesis_latent_v1.spec.md \| grep -c "Q1-"` | 6 gates found |
| 2 | `python -c "import yaml; d=yaml.safe_load(open('abraxas/evidence/noesis_q1_fixtures.yaml')); print(len(d))"` | 10 fixtures |
| 3 | `python -m pytest abraxas/evidence/test_noesis_q1.py -v` | 30+ tests PASSED |
| 4 | `cat abraxas/evidence/noesis_q1_receipt.json \| jq .status` | "PROVISIONALLY_QUALIFIED" |
| 5 | `python -m pytest tests/evidence tests/integration tests/chaos abraxas/evidence/test_*_q1.py -q` | ~123 passed |

---

## Risks, Tradeoffs, and Open Questions

**Risks**:
- **Latent analysis math complexity**: The `latent.py` verifier uses synthetic captures for testing; real integration may need actual model activations
- **JEV fallback**: The verifier has optional JEV fallback (`use_jev_fallback`) — need to ensure tests cover both paths
- **Dimension handling**: `_flatten` handles nested activations; tests must verify nested and flat inputs

**Tradeoffs**:
- **Synthetic vs Real Captures**: Fixtures use synthetic data (deterministic, fast) vs real model outputs (realistic, slow). Chose synthetic for determinism.
- **Schema vs Implementation**: Wire-shape in spec documents the *contract*; implementation in `latent.py` is the reference. Kept aligned.

**Open Questions**:
1. Should NOESIS-Q1 receipt reference the existing `28c840dd` PR #31 receipt explicitly?
2. Does NOESIS need a subsystem YAML (`.abraxas/subsystems/noesis_latent_v1.yaml`) like Hyperlex?
3. Settlement receipt: Noesis has `specs/noesis/latent-classification-settlement.md` — confirm path exists or note as future work.

---

## Plan Summary

| # | Task | File | Est. Time |
|---|------|------|-----------|
| 1 | Specification | `abraxas/evidence/noesis_latent_v1.spec.md` | 5 min |
| 2 | Fixtures | `abraxas/evidence/noesis_q1_fixtures.yaml` | 5 min |
| 3 | Test Suite | `abraxas/evidence/test_noesis_q1.py` | 10 min |
| 4 | Receipt | `abraxas/evidence/noesis_q1_receipt.json` | 2 min |
| 5 | Test & Validate | (commands) | 3 min |
| 6 | Commit & Push | (git) | 2 min |

**Total**: ~27 minutes of focused implementation.

---

**Saved to**: `.hermes/plans/2026-10-04_143000-noesis-q1-qualification.md`