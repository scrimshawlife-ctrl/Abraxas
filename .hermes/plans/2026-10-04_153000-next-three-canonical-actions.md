# Next Three Canonical Actions Implementation Plan

**Goal**: Execute the next three canonical actions from the Master Index roadmap:
1. TRUTINA-Q1 calibration qualification
2. ABRAXAS-Q1 governance qualification  
3. Advance RSI/Timechain integration (CypherTempre)

---

## Current Context / Assumptions

- **Repository**: `/Users/appliedalchemylabs/Abraxas` (main branch, clean, 143 tests passing)
- **Completed Q1 Qualifications**: HYPERLEX-Q1, SEMION-Q1, NOESIS-Q1 (all `PROVISIONALLY_QUALIFIED`)
- **Pairwise Status**: 
  - SEMION→HYPERLEX: UNBLOCKED ✅
  - HYPERLEX→NOESIS: UNBLOCKED ✅
  - NOESIS→TRUTINA: BLOCKED (requires TRUTINA-Q1)
  - NOESIS→ABRAXAS: BLOCKED (requires ABRAXAS-Q1)
  - TRUTINA→ABRAXAS: BLOCKED (requires TRUTINA-Q1, ABRAXAS-Q1)
- **Hard Gates**: EXP-001 DEFERRED, N5 BLOCKED, Production DENIED
- **Existing Implementation**:
  - `abraxas/evidence/__init__.py` — Brier scoring, Trutina functions, CALIBRATION evidence type
  - `abraxas/governance/production.py` — 6-gate governor, ProductionArbiter, mock TrutinaProvider
  - `abraxas/evidence/verifiers/latent.py` — Brier calibration hooks used by Noesis verifier
  - No dedicated Trutina verifier or provider exists yet
  - CypherTempre Timechain referenced in Master Index (2026-09-03 RSI/Timechain Operator pack)

---

## Architecture / Proposed Approach

Following the established Q1 pattern (HYPERLEX/SEMION/NOESIS), we will:

1. **TRUTINA-Q1**: Create dedicated TrutinaEvidenceProvider + CalibrationVerifier with deterministic fixtures, spec, tests, receipt
2. **ABRAXAS-Q1**: Formalize the 6-gate governance system as a qualified subsystem with spec, fixtures, tests, receipt
3. **RSI/Timechain**: Implement CypherTempre Timechain integration via Yggdrasil memory layer with operator pack

All work remains **CANON-SHADOW / ADVISORY_ONLY** — no canon mutation.

---

## Step-by-Step Tasks

### Task 1: TRUTINA-Q1 Calibration Qualification

**File**: `abraxas/evidence/trutina_calibration_v1.spec.md`

**Content Structure**:
- Header: Status, Version, Receipt Reference, Dependencies (NOESIS-Q1)
- 6 Gates Table (Q1-SPEC, Q1-FIXTURE, Q1-ADAPTER, Q1-SCHEMA, Q1-VERIFIER, Q1-ARBITRATION)
- Wire-Shape Contract: TrutinaObservation → Abraxas EvidenceEnvelope (CALIBRATION type)
- Calibration Schema: forecasts, outcomes, Platt/Isotonic regression, regime-aware
- Invariants (authority boundary, no forecast influence, shadow lane)
- Test Fixtures Overview (8 fixtures)
- Qualification Receipt Structure
- Pairwise Conformance (NOESIS→TRUTINA, TRUTINA→ABRAXAS)

**Verification**: `cat abraxas/evidence/trutina_calibration_v1.spec.md | grep -c "Q1-"`

---

**File**: `abraxas/evidence/trutina_q1_fixtures.yaml`

**Fixtures** (8 total):
1. `fixture_valid_calibration` — Platt scaling with 100 forecasts/outcomes
2. `fixture_valid_regime_aware` — HMM regimes (stable/contagion/shock/recovery) with per-regime calibration
3. `fixture_valid_brier_ledger` — Ledger entries with deterministic hashes
4. `fixture_valid_platt_scaling` — Isotonic regression calibration
5. `fixture_invalid_probability_out_of_range` — Negative: probability >1 or <0
6. `fixture_invalid_outcome_not_binary` — Negative: outcome not 0/1
7. `fixture_mismatched_forecasts_outcomes` — Negative: length mismatch
8. `fixture_empty_forecasts` — Negative: empty forecasts

**Verification**: `python -c "import yaml; d=yaml.safe_load(open('abraxas/evidence/trutina_q1_fixtures.yaml')); print(len(d))"`

---

**File**: `abraxas/evidence/test_trutina_q1.py`

**Test Classes** (following HYPERLEX/SEMION/NOESIS pattern):

```python
class TestTRUTINA_Q1_Specification:
    - test_spec_file_exists
    - test_spec_contains_required_sections

class TestTRUTINA_Q1_BrierMath:
    - test_compute_atomic_brier
    - test_compute_brier_series
    - test_compute_brier_series_weights
    - test_to_brier_score_packet
    - test_to_brier_ledger_entry
    - test_compute_ledger_hash
    - test_compute_score_hash

class TestTRUTINA_Q1_Fixtures:
    - test_fixture_valid_calibration
    - test_fixture_valid_regime_aware
    - test_fixture_valid_brier_ledger
    - test_fixture_valid_platt_scaling
    - test_fixture_invalid_probability
    - test_fixture_invalid_outcome
    - test_fixture_mismatched_lengths
    - test_fixture_empty_forecasts

class TestTRUTINA_Q1_Verifier:
    - test_calibration_verifier_exists
    - test_calibration_verifier_verify_passed
    - test_calibration_verifier_verify_escalate
    - test_calibration_verifier_regime_aware

class TestTRUTINA_Q1_Provider:
    - test_provider_engine_identity
    - test_provider_produces_evidence
    - test_provider_provenance_completeness

class TestTRUTINA_Q1_Integration:
    - test_trutina_evidence_through_production_arbiter
    - test_trutina_evidence_through_six_gate_governor

class TestTRUTINA_Q1_Schema:
    - test_evidence_type_defined
    - test_subsystem_yaml_exists
```

**Verification**: `python -m pytest abraxas/evidence/test_trutina_q1.py -v --tb=short`

---

**File**: `abraxas/evidence/verifiers/calibration.py` (NEW)

Create dedicated `CalibrationVerifier` class:
- Verifies Brier score quality, calibration quality, regime-aware calibration
- Implements `Verifier` interface for `EvidenceType.CALIBRATION`
- Methods: `verify(envelope)` → `{passed, escalate, details}`

**File**: `abraxas/evidence/providers/trutina.py` (NEW)

Create dedicated `TrutinaEvidenceProvider` class:
- Implements `EvidenceProvider` interface
- `produce_evidence()` using Brier scoring from `__init__.py`
- Provenance includes authority fields (advisory, semantic_truth=false, etc.)

**Verification**: Import and instantiate both classes successfully

---

**File**: `abraxas/evidence/trutina_q1_receipt.json`

```json
{
  "receipt_id": "TRUTINA-Q1-2026-10-04-001",
  "receipt_type": "qualification",
  "subsystem": "trutina_calibration_v1",
  "status": "PROVISIONALLY_QUALIFIED",
  "gates": {
    "Q1-SPEC": {"passed": true, "artifact": "abraxas/evidence/trutina_calibration_v1.spec.md"},
    "Q1-FIXTURE": {"passed": true, "artifact": "abraxas/evidence/trutina_q1_fixtures.yaml"},
    "Q1-ADAPTER": {"passed": true, "artifact": "abraxas/evidence/test_trutina_q1.py"},
    "Q1-SCHEMA": {"passed": true, "artifact": "trutina.brier.v1 (Brier scoring schema)"},
    "Q1-VERIFIER": {"passed": true, "artifact": "abraxas/evidence/verifiers/calibration.py"},
    "Q1-ARBITRATION": {"passed": true, "artifact": "integration tests in test_trutina_q1.py"}
  }
}
```

**Verification**: `cat abraxas/evidence/trutina_q1_receipt.json | jq .`

---

### Task 2: ABRAXAS-Q1 Governance Qualification

**File**: `abraxas/evidence/abraxas_governance_v1.spec.md`

**Content Structure**:
- Header: Status, Version, Receipt Reference, Dependencies (TRUTINA-Q1, NOESIS-Q1)
- 6 Gates Table (governance spec, fixtures, adapter, schema, verifier, arbitration)
- Wire-Shape Contract: GovernanceDecision → Abraxas EvidenceEnvelope
- Governance Schema: 6 gates (provenance, falsifiability, redundancy, rent, ablation, stabilization)
- DecisionRecord schema, gate weights, aggregate scoring
- Invariants (authority boundary, no forecast influence, shadow lane)
- Test Fixtures Overview (8 fixtures)
- Qualification Receipt Structure
- Pairwise Conformance (NOESIS→ABRAXAS, TRUTINA→ABRAXAS)

**Verification**: `cat abraxas/evidence/abraxas_governance_v1.spec.md | grep -c "Q1-"`

---

**File**: `abraxas/evidence/abraxas_q1_fixtures.yaml`

**Fixtures** (8 total):
1. `fixture_valid_governed_decision` — All 6 gates pass, aggregate >0.8
2. `fixture_valid_provenance_gate` — Full traceability, 3+ engines
3. `fixture_valid_falsifiability_gate` — Contradictions present
4. `fixture_valid_redundancy_gate` — 3+ engines agree
5. `fixture_valid_rent_gate` — Confidence > cost estimate
6. `fixture_valid_ablation_gate` — Survives engine removal
7. `fixture_valid_stabilization_gate` — Decision ACCEPT/VERIFY
8. `fixture_invalid_ungoverned` — Negative: fails governance

**Verification**: `python -c "import yaml; d=yaml.safe_load(open('abraxas/evidence/abraxas_q1_fixtures.yaml')); print(len(d))"`

---

**File**: `abraxas/evidence/test_abraxas_q1.py`

**Test Classes**:

```python
class TestABRAXAS_Q1_Specification:
    - test_spec_file_exists
    - test_spec_contains_required_sections

class TestABRAXAS_Q1_Governance:
    - test_six_gate_governor_exists
    - test_gate_provenance
    - test_gate_falsifiability
    - test_gate_redundancy
    - test_gate_rent
    - test_gate_ablation
    - test_gate_stabilization
    - test_aggregate_scoring

class TestABRAXAS_Q1_Fixtures:
    - test_fixture_valid_governed_decision
    - test_fixture_valid_provenance_gate
    - test_fixture_valid_falsifiability_gate
    - test_fixture_valid_redundancy_gate
    - test_fixture_valid_rent_gate
    - test_fixture_valid_ablation_gate
    - test_fixture_valid_stabilization_gate
    - test_fixture_invalid_ungoverned

class TestABRAXAS_Q1_Integration:
    - test_governance_through_production_arbiter
    - test_governance_through_six_gate_governor
    - test_cross_engine_governance

class TestABRAXAS_Q1_Schema:
    - test_decision_record_schema
    - test_subsystem_yaml_exists
```

**Verification**: `python -m pytest abraxas/evidence/test_abraxas_q1.py -v --tb=short`

---

**File**: `abraxas/evidence/abraxas_q1_receipt.json`

```json
{
  "receipt_id": "ABRAXAS-Q1-2026-10-04-001",
  "receipt_type": "qualification",
  "subsystem": "abraxas_governance_v1",
  "status": "PROVISIONALLY_QUALIFIED",
  "gates": {
    "Q1-SPEC": {"passed": true, "artifact": "abraxas/evidence/abraxas_governance_v1.spec.md"},
    "Q1-FIXTURE": {"passed": true, "artifact": "abraxas/evidence/abraxas_q1_fixtures.yaml"},
    "Q1-ADAPTER": {"passed": true, "artifact": "abraxas/evidence/test_abraxas_q1.py"},
    "Q1-SCHEMA": {"passed": true, "artifact": "abraxas.governance (6-gate system)"},
    "Q1-VERIFIER": {"passed": true, "artifact": "abraxas/governance/production.py (SixGateGovernor)"},
    "Q1-ARBITRATION": {"passed": true, "artifact": "integration tests in test_abraxas_q1.py"}
  }
}
```

---

### Task 3: RSI/Timechain Integration (CypherTempre)

**File**: `abraxas/yggdrasil/timechain.py` (NEW)

Implement `CypherTempreTimechain` class:
- `initialize()` — Connect to Timechain (or file fallback)
- `store(record)` — Append immutable record with timestamp hash
- `retrieve(query)` — Retrieve records by query
- `verify_chain()` — Verify hash chain integrity
- `get_head()` — Get latest block/hash
- Fallback to file storage if Timechain unavailable (per existing Yggdrasil pattern)

**File**: `abraxas/yggdrasil/memory.py` — Update `CypherMemoryLayer`

Add Timechain integration:
- Initialize `CypherTempreTimechain` in `initialize()`
- `store_evidence()` → try Timechain first, fallback to file
- `retrieve_evidence()` → query Timechain with fallback
- `get_timechain_status()` — Return Timechain connection status
- Preserve existing file storage as fallback

**File**: `abraxas/evidence/adapters/cypher.py` — Update

Integrate Timechain:
- Use `CypherMemoryLayer` with Timechain backend
- Provenance includes `timechain_hash` and `timechain_timestamp`
- Maintains SHADOW lane, advisory authority

**File**: `abraxas/yggdrasil/timechain_test.py` (NEW)

Tests for Timechain integration:
- `test_timechain_initialize`
- `test_timechain_store_retrieve`
- `test_timechain_verify_chain`
- `test_timechain_fallback_to_file`
- `test_timechain_hash_integrity`
- `test_cypher_memory_layer_with_timechain`

**Verification**: `python -m pytest abraxas/yggdrasil/timechain_test.py -v --tb=short`

---

## Tests / Validation (TDD Cycle per Task)

| Task | Test Command | Expected Output |
|------|--------------|-----------------|
| TRUTINA Spec | `cat abraxas/evidence/trutina_calibration_v1.spec.md | grep -c "Q1-"` | 6 gates |
| TRUTINA Fixtures | `python -c "import yaml; print(len(yaml.safe_load(open('abraxas/evidence/trutina_q1_fixtures.yaml'))))"` | 8 fixtures |
| TRUTINA Tests | `python -m pytest abraxas/evidence/test_trutina_q1.py -v` | 30+ tests PASSED |
| TRUTINA Verifier | `python -c "from abraxas.evidence.verifiers.calibration import CalibrationVerifier; print('ok')"` | ok |
| TRUTINA Provider | `python -c "from abraxas.evidence.providers.trutina import TrutinaEvidenceProvider; p=TrutinaEvidenceProvider(); print(p.engine_name)"` | trutina |
| TRUTINA Integration | `python -m pytest abraxas/evidence/test_trutina_q1.py::TestTRUTINA_Q1_Integration -v` | 2 tests PASSED |
| ABRAXAS Spec | `cat abraxas/evidence/abraxas_governance_v1.spec.md | grep -c "Q1-"` | 6 gates |
| ABRAXAS Fixtures | `python -c "import yaml; print(len(yaml.safe_load(open('abraxas/evidence/abraxas_q1_fixtures.yaml'))))"` | 8 fixtures |
| ABRAXAS Tests | `python -m pytest abraxas/evidence/test_abraxas_q1.py -v` | 20+ tests PASSED |
| Timechain | `python -m pytest abraxas/yggdrasil/timechain_test.py -v` | 6 tests PASSED |
| Full Suite | `python -m pytest tests/evidence tests/integration tests/chaos abraxas/evidence/test_*_q1.py -q` | ~200+ tests PASSED |

---

## Risks, Tradeoffs, and Open Questions

**Risks**:
- **Trutina calibration complexity**: Real calibration needs historical data; fixtures use synthetic data
- **Governance qualification circularity**: ABRAXAS-Q1 qualifies the governance system that qualifies Q1s
- **Timechain external dependency**: CypherTempre may not be available; must have robust file fallback
- **Circular imports**: New modules must avoid import cycles with existing governance/evidence modules

**Tradeoffs**:
- **Synthetic vs Real Data**: Fixtures use synthetic data for determinism; real integration tests deferred
- **Mock vs Real Engines**: ProductionArbiter tests use mock providers; real engine integration deferred
- **Timechain Optional**: Timechain is optional enhancement; file storage remains primary per existing pattern

**Open Questions**:
1. Should ABRAXAS-Q1 receipt reference the 6-gate governor as both verifier AND governance artifact?
2. Does TRUTINA need a subsystem YAML (`.abraxas/subsystems/trutina_calibration_v1.yaml`)?
3. CypherTempre Timechain: Is there a Python SDK available, or is it HTTP/gRPC only?
4. Should Timechain records include Brier calibration hashes for audit trail?

---

## Plan Summary

| # | Task | Files | Est. Time |
|---|------|-------|-----------|
| 1.1 | TRUTINA Spec | `abraxas/evidence/trutina_calibration_v1.spec.md` | 5 min |
| 1.2 | TRUTINA Fixtures | `abraxas/evidence/trutina_q1_fixtures.yaml` | 5 min |
| 1.3 | TRUTINA Tests | `abraxas/evidence/test_trutina_q1.py` | 10 min |
| 1.4 | Calibration Verifier | `abraxas/evidence/verifiers/calibration.py` | 5 min |
| 1.5 | Trutina Provider | `abraxas/evidence/providers/trutina.py` | 5 min |
| 1.6 | TRUTINA Receipt | `abraxas/evidence/trutina_q1_receipt.json` | 2 min |
| 2.1 | ABRAXAS Spec | `abraxas/evidence/abraxas_governance_v1.spec.md` | 5 min |
| 2.2 | ABRAXAS Fixtures | `abraxas/evidence/abraxas_q1_fixtures.yaml` | 5 min |
| 2.3 | ABRAXAS Tests | `abraxas/evidence/test_abraxas_q1.py` | 10 min |
| 2.4 | ABRAXAS Receipt | `abraxas/evidence/abraxas_q1_receipt.json` | 2 min |
| 3.1 | Timechain Core | `abraxas/yggdrasil/timechain.py` | 10 min |
| 3.2 | Memory Layer Update | `abraxas/yggdrasil/memory.py` | 5 min |
| 3.3 | Cypher Adapter Update | `abraxas/evidence/adapters/cypher.py` | 5 min |
| 3.4 | Timechain Tests | `abraxas/yggdrasil/timechain_test.py` | 5 min |
| All | Test & Commit | `pytest`, `git add/commit/push` | 5 min |

**Total**: ~90 minutes of focused implementation

---

**Saved to**: `.hermes/plans/2026-10-04_153000-next-three-canonical-actions.md`