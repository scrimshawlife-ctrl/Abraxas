# SEMION-Q1 Specification

**Status**: DRAFT — SHADOW / ADVISORY_ONLY
**Version**: 1.0
**Receipt Reference**: SEMION-Q1-SPEC-2026-10-04-001
**Dependencies**: None (first engine in pairwise chain)
**Unlocks**: SEMION→HYPERLEX pairwise conformance

---

## 1. Scope

SEMION-Q1 defines the qualification evidence for **Semion Sign Relation Engine** as an evidence-producing subsystem within the Abraxas ecosystem. Semion provides **SIGN_RELATION** evidence type based on Peircean semiotic classification (qualisign/sinsign/legisign × rheme/dicent/argument × icon/index/symbol).

**Canonical Boundary** (from evidence contract):
```
EvidenceType.SIGN_RELATION = "SIGN_RELATION"
Semion produces advisory evidence only
No governance mutation authority
Feature flag: ABX_SEMION_INSTRUMENT (defaults off)
```

---

## 2. Qualification Gates

Following the ecosystem qualification framework (AC-EIC-Q1), SEMION-Q1 requires evidence across these gates:

| Gate | Requirement | Evidence Artifact |
|------|-------------|-------------------|
| **Q1-SPEC** | Complete specification with Peircean schemas, contracts, invariants | `semion_sign_relation_v1.spec.md` (this document) |
| **Q1-FIXTURE** | Deterministic test fixtures with valid/invalid sign classes | `semion_q1_fixtures.yaml` |
| **Q1-ADAPTER** | Abraxas adapter passes sign relation validation | `test_semion_q1.py` |
| **Q1-SCHEMA** | Wire-shape schema validated against Peircean combinations | `semion.sign.v1.schema.json` |
| **Q1-VERIFIER** | SignRelationVerifier passes verification tests | `test_semion_verifier.py` |
| **Q1-ARBITRATION** | Evidence arbitrates correctly through 6-gate governor | Integration test with ProductionArbiter |

---

## 3. Wire-Shape Contract

### 3.1 SemionObservation (v1)

```json
{
  "schema": "semion.sign.v1",
  "version": "SEMION_SIGN_RELATION_V1",
  "observation_id": "string (hex, 16+ chars)",
  "input_hash": "string (hex, 64 chars)",
  "authority": {
    "kind": "advisory",
    "source": "semion",
    "semantic_truth": false,
    "may_authorize": false,
    "may_mutate_governing_state": false,
    "role": "OBSERVATION | EVIDENCE | SHADOW_SIGNAL"
  },
  "sign_class": "string (format: existence-thirdness-relation)",
  "sign_class_valid": boolean,
  "sign_class_errors": ["string"],
  "interpretant_coherence": float,
  "representamen_object_alignment": float,
  "relation_steps": [
    {
      "relation": "string",
      "subject": "string",
      "object": "string",
      "result": "string",
      "confidence": float,
      "metadata": {}
    }
  ],
  "peircean_analysis": {
    "existence": "qualisign | sinsign | legisign",
    "thirdness": "rheme | dicent | argument",
    "relation": "icon | index | symbol",
    "valid_combination": boolean,
    "coherence_score": float
  },
  "provenance": {
    "instrument_version": "SEMION_SIGN_RELATION_V1",
    "contract_version": "semion.sign.v1",
    "ontology_version": "PEIRCE_CATEGORIES_V1_FINAL",
    "manifest_sha256": "string (hex, 64 chars)",
    "schema_sha256": "string (hex, 64 chars)",
    "settlement_ref": "specs/semion/peircean-classification-settlement.md",
    "settlement_receipt": "string (hex, 64 chars)",
    "artifact_hashes": {}
  }
}
```

### 3.2 Abraxas Advisory Evidence (Adapter Output)

The adapter transforms the above into Abraxas EvidenceEnvelope:

```json
{
  "engine": "semion",
  "engine_version": "semion.sign.v1",
  "model_identity": "semion-sign-v1",
  "evidence_type": "SIGN_RELATION",
  "sign_class": "string",
  "sign_class_valid": boolean,
  "interpretant_coherence": float,
  "representamen_object_alignment": float,
  "peircean_analysis": { ... },
  "provenance": {
    "source": "semion",
    "authority": "advisory",
    "semantic_truth": false,
    "influence_policy": "NONE",
    "valid_for_forecast": false,
    "lane": "shadow"
  }
}
```

---

## 4. Peircean Sign Classification

### 4.1 Valid Combinations (27 total)

| Existence | Thirdness | Relation | Valid |
|-----------|-----------|----------|-------|
| qualisign | rheme | icon | ✅ |
| qualisign | rheme | index | ✅ |
| qualisign | rheme | symbol | ✅ |
| qualisign | dicent | icon | ✅ |
| qualisign | dicent | index | ✅ |
| qualisign | dicent | symbol | ✅ |
| qualisign | argument | icon | ✅ |
| qualisign | argument | index | ✅ |
| qualisign | argument | symbol | ✅ |
| sinsign | rheme | icon | ✅ |
| sinsign | rheme | index | ✅ |
| sinsign | rheme | symbol | ✅ |
| sinsign | dicent | icon | ✅ |
| sinsign | dicent | index | ✅ |
| sinsign | dicent | symbol | ✅ |
| sinsign | argument | icon | ✅ |
| sinsign | argument | index | ✅ |
| sinsign | argument | symbol | ✅ |
| legisign | rheme | icon | ✅ |
| legisign | rheme | index | ✅ |
| legisign | rheme | symbol | ✅ |
| legisign | dicent | icon | ✅ |
| legisign | dicent | index | ✅ |
| legisign | dicent | symbol | ✅ |
| legisign | argument | icon | ✅ |
| legisign | argument | index | ✅ |
| legisign | argument | symbol | ✅ |

**All 27 combinations are valid** — Semion validates structure, not semantic truth.

### 4.2 Sign Class Format

```
{existence}-{thirdness}-{relation}
```

Examples:
- `qualisign-rheme-icon` ✅
- `sinsign-dicent-index` ✅
- `legisign-argument-symbol` ✅
- `invalid-class` ❌ (wrong format)
- `qualisign-rheme-invalid` ❌ (invalid relation)

---

## 5. Invariants (Must Hold)

1. **Authority Boundary**: `semantic_truth == false` ALWAYS
2. **Advisory Only**: `authority == "advisory"` ALWAYS
3. **No Forecast Influence**: `valid_for_forecast == false` ALWAYS
3. **No Governance Mutation**: `may_mutate_governing_state == false` ALWAYS
4. **Shadow Lane**: `lane == "shadow"` ALWAYS
5. **Feature Flag**: Integration disabled by default (`ABX_SEMION_INSTRUMENT=0`)
6. **Sign Class Validation**: Must match Peircean 27 valid combinations
7. **Interpretant Coherence**: Causal relations cannot have negated results
8. **Representamen-Object Alignment**: Adjacent steps must chain (object → subject)

---

## 6. Test Fixtures

### 6.1 Fixture 1: Valid Qualisign-Rheme-Icon

```yaml
fixture_valid_qualisign_rheme_icon:
  input:
    schema: "semion.sign.v1"
    version: "SEMION_SIGN_RELATION_V1"
    observation_id: "abc12345deadbeef"
    input_hash: "0" * 64
    authority:
      kind: "advisory"
      source: "semion"
      semantic_truth: false
      may_authorize: false
      may_mutate_governing_state: false
      role: "OBSERVATION"
    sign_class: "qualisign-rheme-icon"
    sign_class_valid: true
    sign_class_errors: []
    interpretant_coherence: 1.0
    representamen_object_alignment: 1.0
    relation_steps:
      - relation: "resembles"
        subject: "sign_a"
        object: "sign_b"
        result: "similar"
        confidence: 0.9
        metadata: {}
    peircean_analysis:
      existence: "qualisign"
      thirdness: "rheme"
      relation: "icon"
      valid_combination: true
      coherence_score: 0.95
    provenance:
      instrument_version: "SEMION_SIGN_RELATION_V1"
      contract_version: "semion.sign.v1"
      ontology_version: "PEIRCE_CATEGORIES_V1_FINAL"
      manifest_sha256: "c" * 64
      schema_sha256: "d" * 64
      settlement_ref: "specs/semion/peircean-classification-settlement.md"
      settlement_receipt: "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
      artifact_hashes: {}
  expected_output:
    engine: "semion"
    engine_version: "semion.sign.v1"
    model_identity: "semion-sign-v1"
    evidence_type: "SIGN_RELATION"
    sign_class: "qualisign-rheme-icon"
    sign_class_valid: true
    interpretant_coherence: 1.0
    representamen_object_alignment: 1.0
```

### 6.2 Fixture 2: Valid Sinsign-Dicent-Index

```yaml
fixture_valid_sinsign_dicent_index:
  input:
    sign_class: "sinsign-dicent-index"
    sign_class_valid: true
    interpretant_coherence: 0.9
    representamen_object_alignment: 0.85
    relation_steps:
      - relation: "indicates"
        subject: "smoke"
        object: "fire"
        result: "present"
        confidence: 0.85
        metadata: {}
      - relation: "implies"
        subject: "fire"
        object: "heat"
        result: "present"
        confidence: 0.9
        metadata: {}
```

### 6.3 Fixture 3: Valid Legisign-Argument-Symbol

```yaml
fixture_valid_legisign_argument_symbol:
  input:
    sign_class: "legisign-argument-symbol"
    sign_class_valid: true
    interpretant_coherence: 1.0
    representamen_object_alignment: 1.0
    relation_steps:
      - relation: "means"
        subject: "word"
        object: "concept"
        result: "defined"
        confidence: 1.0
        metadata: {}
```

### 6.4 Fixture 4: Invalid Sign Class Format

```yaml
fixture_invalid_format:
  input:
    sign_class: "invalid-format"
    sign_class_valid: false
    sign_class_errors: ["Invalid format: invalid-format"]
    expected_error: "SemionAuthorityError"
```

### 6.5 Fixture 5: Invalid Existence

```yaml
fixture_invalid_existence:
  input:
    sign_class: "invalid-rheme-icon"
    sign_class_valid: false
    sign_class_errors: ["Invalid existence: invalid"]
    expected_error: "SemionAuthorityError"
```

### 6.6 Fixture 6: Invalid Thirdness

```yaml
fixture_invalid_thirdness:
  input:
    sign_class: "qualisign-invalid-icon"
    sign_class_valid: false
    sign_class_errors: ["Invalid thirdness: invalid"]
    expected_error: "SemionAuthorityError"
```

### 6.7 Fixture 7: Invalid Relation

```yaml
fixture_invalid_relation:
  input:
    sign_class: "qualisign-rheme-invalid"
    sign_class_valid: false
    sign_class_errors: ["Invalid relation: invalid"]
    expected_error: "SemionAuthorityError"
```

### 6.8 Fixture 8: Contradictory Interpretant

```yaml
fixture_contradictory_interpretant:
  input:
    sign_class: "sinsign-rheme-icon"
    sign_class_valid: true
    interpretant_coherence: 0.0
    relation_steps:
      - relation: "causes"
        subject: "a"
        object: "b"
        result: "not b"  # CONTRADICTION
        confidence: 0.8
        metadata: {}
  expected_interpretant_coherence: 0.0
```

### 6.9 Fixture 9: Broken Chain (Object ≠ Next Subject)

```yaml
fixture_broken_chain:
  input:
    sign_class: "legisign-dicent-symbol"
    sign_class_valid: true
    representamen_object_alignment: 0.0
    relation_steps:
      - relation: "means"
        subject: "word1"
        object: "concept1"
        result: "defined"
        confidence: 1.0
        metadata: {}
      - relation: "implies"
        subject: "unrelated"  # BREAK: object was "concept1"
        object: "concept2"
        result: "defined"
        confidence: 1.0
        metadata: {}
  expected_alignment: 0.0
```

---

## 7. Qualification Receipt Structure

Upon successful gate completion, a SEMION-Q1 receipt is emitted:

```json
{
  "receipt_id": "SEMION-Q1-2026-10-04-001",
  "receipt_type": "qualification",
  "subsystem": "semion_sign_relation_v1",
  "status": "PROVISIONALLY_QUALIFIED",
  "issued_at": "2026-10-04T...Z",
  "issued_by": "operator",
  "gates": {
    "Q1-SPEC": { "passed": true, "artifact": "semion_sign_relation_v1.spec.md" },
    "Q1-FIXTURE": { "passed": true, "artifact": "semion_q1_fixtures.yaml" },
    "Q1-ADAPTER": { "passed": true, "artifact": "test_semion_q1.py" },
    "Q1-SCHEMA": { "passed": true, "artifact": "semion.sign.v1.schema.json" },
    "Q1-VERIFIER": { "passed": true, "artifact": "test_semion_verifier.py" },
    "Q1-ARBITRATION": { "passed": true, "artifact": "integration_test_production_arbiter.py" }
  },
  "sha256": "computed_over_all_artifacts",
  "notes": [
    "Semion provides SIGN_RELATION evidence only",
    "All 27 Peircean combinations validated",
    "Pairwise SEMION→HYPERLEX unblocked upon HYPERLEX-Q1 completion",
    "EXP-001 remains DEFERRED until AC-EIC-G1"
  ]
}
```

---

## 8. Pairwise Conformance (Future)

Per the ecosystem roadmap, pairwise conformance requires:
- **SEMION→HYPERLEX**: Semion symbolic relations → Hyperlex lexical observations
  - **Status**: BLOCKED until HYPERLEX-Q1 complete ✅
  - **Next**: Implement cross-engine validation when both qualified

---

## 9. Execution Notes

- All work remains **CANON-SHADOW / ADVISORY_ONLY**
- No canon mutation without explicit operator gate
- No production activation / FORECAST escalation
- Receipt emitted only after operator review and acceptance