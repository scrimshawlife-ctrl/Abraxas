# HYPERLEX-Q1 Specification

**Status**: DRAFT — SHADOW / ADVISORY_ONLY
**Version**: 1.0
**Receipt Reference**: HYPERLEX-Q1-SPEC-2026-10-04-001
**Dependencies**: NOESIS-Q1 (PROVISIONALLY_QUALIFIED, receipt `28c840dd`)

---

## 1. Scope

HYPERLEX-Q1 defines the qualification evidence for **Hyperlex Instrument V1** as a versioned semantic instrumentation dependency within the Abraxas ecosystem. This specification establishes the boundary conditions, evidence requirements, and verification gates for Hyperlex to achieve `PROVISIONALLY_QUALIFIED` status.

**Canonical Boundary** (from Master Index 2026-09-19):
```
HYPERLEX_OUTPUT != SEMANTIC_TRUTH
influence_policy = NONE
valid_for_forecast = false
lane = shadow
```

---

## 2. Qualification Gates

Following the ecosystem qualification framework (AC-EIC-Q1), HYPERLEX-Q1 requires evidence across these gates:

| Gate | Requirement | Evidence Artifact |
|------|-------------|-------------------|
| **Q1-SPEC** | Complete specification with schemas, contracts, and invariants | `hyperlex_instrument_v1.spec.md` (this document) |
| **Q1-FIXTURE** | Deterministic test fixtures with known inputs/outputs | `hyperlex_q1_fixtures.yaml` |
| **Q1-ADAPTER** | Abraxas adapter passes authority-boundary tests | `test_hyperlex_instrument_evidence.py` (existing) |
| **Q1-SCHEMA** | Wire-shape schema validated against Hyperlex Instrument V1 | `hyperlex.instrument.v1.schema.json` |
| **Q1-SETTLEMENT** | Classification program settlement receipt linked | `4ae7cddf...` (Hyperlex V6 settlement) |
| **Q1-ARBITRATION** | Evidence arbitrates correctly through 6-gate governor | Integration test with ProductionArbiter |

---

## 3. Wire-Shape Contract

### 3.1 HyperlexObservation (v1)

```json
{
  "schema": "hyperlex.instrument.v1",
  "version": "HYPERLEX_INSTRUMENT_V1",
  "observation_id": "string (hex, 16+ chars)",
  "input_hash": "string (hex, 64 chars)",
  "authority": {
    "kind": "advisory",
    "source": "hyperlex",
    "semantic_truth": false,
    "may_authorize": false,
    "may_mutate_governing_state": false,
    "role": "OBSERVATION | EVIDENCE | SHADOW_SIGNAL"
  },
  "evidence": {
    "present": boolean,
    "score": "float [0,1] | null",
    "abstain": boolean,
    "reason": "string | null"
  },
  "representation": {
    "encoder_id": "string",
    "encoder_hash": "string (hex, 64 chars)",
    "embed_mode": "STATIC_HASH_EMBEDDING",
    "embedding_ref": "string (hex, 64 chars) | null"
  },
  "candidates": [
    {
      "concept_id": "string (domain.* | archetype.*)",
      "score": "float [0,1]",
      "axis": "string",
      "advisory": true,
      "status": "advisory"
    }
  ],
  "neighborhood": [
    {"concept_id": "string", "similarity": "float [0,1]"}
  ],
  "diagnostics": {
    "margin": "float [0,1] | null",
    "ambiguity": "float [0,1] | null",
    "distribution_distance": "float | null",
    "representation_drift": "float | null",
    "unavailable": ["distribution_distance", "representation_drift", ...]
  },
  "provenance": {
    "instrument_version": "HYPERLEX_INSTRUMENT_V1",
    "contract_version": "hyperlex.instrument.v1",
    "ontology_version": "HYPERLEX_V6_FAMILY_ONTOLOGY_V1_FINAL",
    "manifest_sha256": "string (hex, 64 chars)",
    "schema_sha256": "string (hex, 64 chars)",
    "settlement_ref": "specs/007-hyperlexical-model/classification-v6-program-settlement-20261002.md",
    "settlement_receipt": "4ae7cddffcf72330adad8eb3dfd453025aa02c8cb12c5e6f5499a4e6cad06ca2",
    "artifact_hashes": {}
  }
}
```

### 3.2 Abraxas Advisory Evidence (Adapter Output)

The adapter `adapt_observation()` transforms the above into:

```json
{
  "schema": "abraxas.evidence.hyperlex_instrument.v1",
  "kind": "SHADOW_SIGNAL",
  "source": "hyperlex",
  "authority": "advisory",
  "semantic_truth": false,
  "may_authorize": false,
  "may_mutate_governing_state": false,
  "may_override_provenance": false,
  "observation_id": "string",
  "input_hash": "string",
  "evidence": { "present": bool, "score": float, "abstain": bool, "reason": "string" },
  "candidates": [...],
  "neighborhood": [...],
  "ambiguity": float,
  "margin": float,
  "diagnostics": { ... },
  "representation": { ... },
  "instrument_version": "HYPERLEX_INSTRUMENT_V1",
  "ontology_version": "HYPERLEX_V6_FAMILY_ONTOLOGY_V1_FINAL",
  "contract_version": "hyperlex.instrument.v1",
  "manifest_sha256": "string",
  "schema_sha256": "string",
  "settlement_ref": "string",
  "settlement_receipt": "string",
  "artifact_hashes": {},
  "influence_policy": "NONE",
  "valid_for_forecast": false,
  "lane": "shadow",
  "enabled": boolean,
  "notes": ["HYPERLEX_OUTPUT != SEMANTIC_TRUTH", "..."]
}
```

---

## 4. Invariants (Must Hold)

1. **Authority Boundary**: `semantic_truth == false` ALWAYS
2. **Advisory Only**: `authority == "advisory"` ALWAYS
3. **No Forecast Influence**: `valid_for_forecast == false` ALWAYS
4. **No Governance Mutation**: `may_mutate_governing_state == false` ALWAYS
5. **Shadow Lane**: `lane == "shadow"` ALWAYS
6. **Classifier Rejected**: V6 classification program settlement is final; no reopening
7. **Feature Flag**: Integration disabled by default (`ABX_HYPERLEX_INSTRUMENT=0`)
8. **Deterministic Adapter**: Same input observation → same output evidence (modulo timestamps)

---

## 5. Test Fixtures

### 5.1 Fixture 1: Minimal Valid Observation

```yaml
# hyperlex_q1_fixtures.yaml
fixture_minimal_valid:
  input:
    schema: "hyperlex.instrument.v1"
    version: "HYPERLEX_INSTRUMENT_V1"
    observation_id: "abc12345deadbeef"
    input_hash: "0" * 64
    authority:
      kind: "advisory"
      source: "hyperlex"
      semantic_truth: false
      may_authorize: false
      may_mutate_governing_state: false
      role: "OBSERVATION"
    evidence:
      present: true
      score: 0.5
      abstain: false
      reason: null
    representation:
      encoder_id: "sentence-transformers/msmarco-distilbert-base-v4"
      encoder_hash: "a" * 64
      embed_mode: "STATIC_HASH_EMBEDDING"
      embedding_ref: "b" * 64
    candidates:
      - concept_id: "domain.crypto"
        score: 0.8
        axis: "domain"
        advisory: true
        status: "advisory"
    neighborhood:
      - concept_id: "domain.crypto"
        similarity: 0.8
    diagnostics:
      margin: 0.2
      ambiguity: 0.1
      distribution_distance: null
      representation_drift: null
      unavailable: ["distribution_distance", "representation_drift"]
    provenance:
      instrument_version: "HYPERLEX_INSTRUMENT_V1"
      contract_version: "hyperlex.instrument.v1"
      ontology_version: "HYPERLEX_V6_FAMILY_ONTOLOGY_V1_FINAL"
      manifest_sha256: "c" * 64
      schema_sha256: "d" * 64
      settlement_ref: "specs/007-hyperlexical-model/classification-v6-program-settlement-20261002.md"
      settlement_receipt: "4ae7cddffcf72330adad8eb3dfd453025aa02c8cb12c5e6f5499a4e6cad06ca2"
      artifact_hashes: {}
  expected_output:
    schema: "abraxas.evidence.hyperlex_instrument.v1"
    kind: "SHADOW_SIGNAL"
    source: "hyperlex"
    authority: "advisory"
    semantic_truth: false
    may_authorize: false
    may_mutate_governing_state: false
    may_override_provenance: false
    valid_for_forecast: false
    influence_policy: "NONE"
    lane: "shadow"
```

### 5.2 Fixture 2: Abstain Observation

```yaml
fixture_abstain:
  input:
    # ... same as minimal but:
    evidence:
      present: false
      score: null
      abstain: true
      reason: "insufficient_confidence"
    candidates: []
  expected_output:
    evidence:
      present: false
      score: null
      abstain: true
      reason: "insufficient_confidence"
    candidates: []
```

### 5.3 Fixture 3: Multiple Candidates

```yaml
fixture_multi_candidate:
  input:
    candidates:
      - concept_id: "domain.crypto"
        score: 0.75
        axis: "domain"
        advisory: true
        status: "advisory"
      - concept_id: "archetype.pump_fun"
        score: 0.62
        axis: "archetype"
        advisory: true
        status: "advisory"
      - concept_id: "domain.defi"
        score: 0.55
        axis: "domain"
        advisory: true
        status: "advisory"
```

### 5.4 Fixture 4: Negative Cases (Must Reject)

```yaml
fixture_semantic_truth_true:
  input:
    authority:
      semantic_truth: true  # VIOLATION
  expected: HyperlexAuthorityError

fixture_non_advisory_candidate:
  input:
    candidates:
      - concept_id: "domain.crypto"
        score: 0.8
        axis: "domain"
        advisory: false  # VIOLATION
        status: "advisory"
  expected: HyperlexAuthorityError

fixture_authoritative_kind:
  input: # kind="CANONICAL_STATE" passed to adapt_observation
  expected: HyperlexAuthorityError

fixture_valid_for_forecast_true:
  input: # adapter output modified to have valid_for_forecast=true
  expected: HyperlexAuthorityError (via assert_not_authoritative)
```

---

## 6. Qualification Receipt Structure

Upon successful gate completion, a HYPERLEX-Q1 receipt is emitted:

```json
{
  "receipt_id": "HYPERLEX-Q1-2026-10-04-001",
  "receipt_type": "qualification",
  "subsystem": "hyperlex_instrument_v1",
  "status": "PROVISIONALLY_QUALIFIED",
  "issued_at": "2026-10-04T...Z",
  "issued_by": "operator",
  "gates": {
    "Q1-SPEC": { "passed": true, "artifact": "hyperlex_instrument_v1.spec.md" },
    "Q1-FIXTURE": { "passed": true, "artifact": "hyperlex_q1_fixtures.yaml" },
    "Q1-ADAPTER": { "passed": true, "artifact": "test_hyperlex_instrument_evidence.py" },
    "Q1-SCHEMA": { "passed": true, "artifact": "hyperlex.instrument.v1.schema.json" },
    "Q1-SETTLEMENT": { "passed": true, "artifact": "4ae7cddf... (V6 settlement)" },
    "Q1-ARBITRATION": { "passed": true, "artifact": "integration_test_production_arbiter.py" }
  },
  "sha256": "computed_over_all_artifacts",
  "notes": [
    "HYPERLEX_OUTPUT != SEMANTIC_TRUTH",
    "Pairwise conformance blocked until SEMION-Q1, NOESIS-Q1, TRUTINA-Q1 complete",
    "EXP-001 remains DEFERRED until AC-EIC-G1"
  ]
}
```

---

## 7. Pairwise Conformance (Future)

Per the ecosystem roadmap, pairwise conformance requires:
- **SEMION→HYPERLEX**: Semion symbolic relations → Hyperlex lexical observations
- **HYPERLEX→NOESIS**: Hyperlex observations → Noesis latent evidence/falsification
- **HYPERLEX→ABRAXAS**: Hyperlex signals → Abraxas SHADOW/FORECAST governance consumption

**Status**: BLOCKED — requires SEMION-Q1, NOESIS-Q1, ABRAXAS-Q1 completion first.

---

## 8. Execution Notes

- All work remains **CANON-SHADOW / ADVISORY_ONLY**
- No canon mutation without explicit operator gate
- No production activation / FORECAST escalation
- Receipt emitted only after operator review and acceptance