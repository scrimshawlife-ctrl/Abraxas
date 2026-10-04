# NOESIS-Q1 Specification

**Status**: DRAFT — SHADOW / ADVISORY_ONLY
**Version**: 1.0
**Receipt Reference**: NOESIS-Q1-SPEC-2026-10-04-001
**Dependencies**: None (first in latent pipeline)
**Prior Receipt**: `28c840dd` (NOESIS-Q1 PROVISIONALLY_QUALIFIED per Master Index 2026-09-19)

---

## 1. Scope

NOESIS-Q1 defines the qualification evidence for **Noesis Latent Structure Engine** as an evidence-producing subsystem within the Abraxas ecosystem. Noesis provides **LATENT_STRUCTURAL** evidence type based on structural coherence analysis of latent representations across interventions, counterfactuals, and ablations.

**Canonical Boundary** (from Master Index 2026-09-19):
```
NOESIS_OUTPUT != SEMANTIC_TRUTH
influence_policy = NONE
valid_for_forecast = false
lane = shadow
```

---

## 2. Qualification Gates

Following the ecosystem qualification framework (AC-EIC-Q1), NOESIS-Q1 requires evidence across these gates:

| Gate | Requirement | Evidence Artifact |
|------|-------------|-------------------|
| **Q1-SPEC** | Complete specification with latent schemas, contracts, and invariants | `noesis_latent_v1.spec.md` (this document) |
| **Q1-FIXTURE** | Deterministic test fixtures with known latent captures/conditions | `noesis_q1_fixtures.yaml` |
| **Q1-ADAPTER** | Abraxas adapter passes authority-boundary tests | `test_noesis_q1.py` |
| **Q1-SCHEMA** | Wire-shape schema validated against latent structure schema | `noesis.latent.v1` (latent structure schema) |
| **Q1-VERIFIER** | LatentStructureVerifier passes verification tests | `abraxas/evidence/verifiers/latent.py` |
| **Q1-ARBITRATION** | Evidence arbitrates correctly through 6-gate governor | Integration test with ProductionArbiter |

---

## 3. Wire-Shape Contract

### 3.1 NoesisObservation (v1)

```json
{
  "schema": "noesis.latent.v1",
  "version": "NOESIS_LATENT_V1",
  "observation_id": "string (hex, 16+ chars)",
  "input_hash": "string (hex, 64 chars)",
  "authority": {
    "kind": "advisory",
    "source": "noesis",
    "semantic_truth": false,
    "may_authorize": false,
    "may_mutate_governing_state": false,
    "role": "OBSERVATION | EVIDENCE | SHADOW_SIGNAL"
  },
  "latent_captures": [
    {
      "condition": "string (baseline | intervention | counterfactual | ablation | noise | patch)",
      "activations": "List[List[float]] | List[float]",
      "metadata": {}
    }
  ],
  "structural_analysis": {
    "overall_structural_coherence": "float [0,1]",
    "conditions_tested": ["string"],
    "conditions": {
      "intervention": {
        "mean_stability": "float [0,1]",
        "mean_intervention_sensitivity": "float [0,1]",
        "sample_count": "int"
      }
    }
  },
  "rsa_correlation": "float [0,1]",
  "geometric_integrity": "float [0,1]",
  "manifold_integrity": "float [0,1]",
  "provenance": {
    "instrument_version": "NOESIS_LATENT_V1",
    "contract_version": "noesis.latent.v1",
    "ontology_version": "LATENT_STRUCTURE_V1_FINAL",
    "manifest_sha256": "string (hex, 64 chars)",
    "schema_sha256": "string (hex, 64 chars)",
    "settlement_ref": "specs/noesis/latent-structure-settlement.md",
    "settlement_receipt": "string (hex, 64 chars)",
    "artifact_hashes": {}
  }
}
```

### 3.2 Abraxas Advisory Evidence (Adapter Output)

The `NoesisEvidenceProvider.produce_evidence()` transforms the above into Abraxas EvidenceEnvelope:

```json
{
  "engine": "noesis",
  "engine_version": "noesis.latent.v1",
  "model_identity": "noesis.latent.v1",
  "evidence_type": "LATENT_STRUCTURAL",
  "confidence": "float [0,1] (structural_coherence)",
  "uncertainty": "float [0,1] (1 - coherence)",
  "entropy": "float [0,1] (intervention_sensitivity)",
  "provenance": {
    "source": "noesis.latent.v1",
    "method": "latent_structure_analysis",
    "structural_coherence": "float [0,1]",
    "intervention_sensitivity": "float [0,1]",
    "rsa_correlation": "float [0,1]",
    "geometric_integrity": "float [0,1]",
    "manifold_integrity": "float [0,1]",
    "conditions_tested": ["string"],
    "authority": "advisory",
    "semantic_truth": false,
    "influence_policy": "NONE",
    "valid_for_forecast": false,
    "lane": "shadow"
  }
}
```

---

## 4. Latent Structure Schema

### 4.1 Conditions

| Condition | Description | Expected Effect |
|-----------|-------------|-----------------|
| `baseline` | Reference condition | Reference activations |
| `intervention` | Targeted intervention | Small perturbations (σ≈0.3) |
| `counterfactual` | Counterfactual reasoning | Inverted + noise (σ≈0.2) |
| `ablation` | Component removal | Scaled activations (0.5-1.5x) |
| `noise` | Random noise injection | Large perturbations (σ≈0.5) |
| `patch` | Surgical patch | Minimal perturbations (σ≈0.1) |

### 4.2 Activations Format

- **Flat**: `List[float]` — e.g., `[0.1, -0.3, 0.7, ...]`
- **Nested**: `List[List[float]]` — e.g., `[[0.1, 0.2], [0.3, 0.4], ...]`
- Both supported via `_flatten()` utility

### 4.3 Metrics

| Metric | Range | Threshold | Meaning |
|--------|-------|-----------|---------|
| `structural_coherence` | [0,1] | ≥0.7 | Mean stability across conditions |
| `intervention_sensitivity` | [0,1] | ≤0.3 | 1 - stability |
| `rsa_correlation` | [0,1] | ≥0.6 | Representational similarity correlation |
| `geometric_integrity` | [0,1] | — | Same as coherence |
| `manifold_integrity` | [0,1] | ≥0.5 | Local neighborhood preservation |

---

## 5. Invariants (Must Hold)

1. **Authority Boundary**: `semantic_truth == false` ALWAYS
2. **Advisory Only**: `authority == "advisory"` ALWAYS
3. **No Forecast Influence**: `valid_for_forecast == false` ALWAYS
4. **No Governance Mutation**: `may_mutate_governing_state == false` ALWAYS
5. **Shadow Lane**: `lane == "shadow"` ALWAYS
6. **Feature Flag**: Integration disabled by default (`ABX_NOESIS_INSTRUMENT=0`)
7. **Deterministic Adapter**: Same input captures → same output evidence (modulo timestamps)
8. **Baseline Required**: At least one `baseline` condition capture required

---

## 6. Test Fixtures

### 6.1 Fixture 1: Valid Baseline + Intervention

```yaml
fixture_valid_baseline_intervention:
  input:
    schema: "noesis.latent.v1"
    version: "NOESIS_LATENT_V1"
    observation_id: "abc12345deadbeef"
    input_hash: "0" * 64
    authority:
      kind: "advisory"
      source: "noesis"
      semantic_truth: false
      may_authorize: false
      may_mutate_governing_state: false
      role: "OBSERVATION"
    latent_captures:
      - condition: "baseline"
        activations: [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
      - condition: "baseline"
        activations: [[1.1, 2.1, 3.1], [4.1, 5.1, 6.1]]
      - condition: "intervention"
        activations: [[1.3, 2.3, 3.3], [4.3, 5.3, 6.3]]
    structural_analysis:
      overall_structural_coherence: 0.85
      conditions_tested: ["intervention"]
      conditions:
        intervention:
          mean_stability: 0.88
          mean_intervention_sensitivity: 0.12
          sample_count: 1
    rsa_correlation: 0.92
    geometric_integrity: 0.85
    manifold_integrity: 0.82
    provenance:
      instrument_version: "NOESIS_LATENT_V1"
      contract_version: "noesis.latent.v1"
      ontology_version: "LATENT_STRUCTURE_V1_FINAL"
      manifest_sha256: "c" * 64
      schema_sha256: "d" * 64
      settlement_ref: "specs/noesis/latent-structure-settlement.md"
      settlement_receipt: "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
      artifact_hashes: {}
  expected_output:
    engine: "noesis"
    engine_version: "noesis.latent.v1"
    model_identity: "noesis.latent.v1"
    evidence_type: "LATENT_STRUCTURAL"
    confidence: 0.85
    uncertainty: 0.15
    entropy: 0.12
    provenance:
      structural_coherence: 0.85
      intervention_sensitivity: 0.12
      rsa_correlation: 0.92
      geometric_integrity: 0.85
      manifold_integrity: 0.82
      conditions_tested: ["intervention"]
```

### 6.2 Fixture 2: Valid Multiple Conditions

```yaml
fixture_valid_multiple_conditions:
  input:
    latent_captures:
      - condition: "baseline"
        activations: [[1.0, 2.0], [3.0, 4.0]]
      - condition: "baseline"
        activations: [[1.1, 2.1], [3.1, 4.1]]
      - condition: "intervention"
        activations: [[1.2, 2.2], [3.2, 4.2]]
      - condition: "counterfactual"
        activations: [[-1.0, -2.0], [-3.0, -4.0]]
      - condition: "ablation"
        activations: [[0.5, 1.0], [1.5, 2.0]]
      - condition: "noise"
        activations: [[2.0, 3.0], [5.0, 6.0]]
      - condition: "patch"
        activations: [[1.05, 2.05], [3.05, 4.05]]
    structural_analysis:
      overall_structural_coherence: 0.72
      conditions_tested: ["intervention", "counterfactual", "ablation", "noise", "patch"]
      conditions:
        intervention:
          mean_stability: 0.85
          mean_intervention_sensitivity: 0.15
          sample_count: 1
        counterfactual:
          mean_stability: 0.45
          mean_intervention_sensitivity: 0.55
          sample_count: 1
        ablation:
          mean_stability: 0.68
          mean_intervention_sensitivity: 0.32
          sample_count: 1
        noise:
          mean_stability: 0.35
          mean_intervention_sensitivity: 0.65
          sample_count: 1
        patch:
          mean_stability: 0.92
          mean_intervention_sensitivity: 0.08
          sample_count: 1
    rsa_correlation: 0.88
    geometric_integrity: 0.72
    manifold_integrity: 0.75
```

### 6.3 Fixture 3: Valid High Coherence (Should Pass)

```yaml
fixture_valid_high_coherence:
  input:
    latent_captures:
      - condition: "baseline"
        activations: [[1.0] * 64]
      - condition: "baseline"
        activations: [[1.01] * 64]
      - condition: "intervention"
        activations: [[1.02] * 64]
      - condition: "patch"
        activations: [[1.005] * 64]
    structural_analysis:
      overall_structural_coherence: 0.95
      conditions_tested: ["intervention", "patch"]
      conditions:
        intervention:
          mean_stability: 0.98
          mean_intervention_sensitivity: 0.02
          sample_count: 1
        patch:
          mean_stability: 0.99
          mean_intervention_sensitivity: 0.01
          sample_count: 1
    rsa_correlation: 0.99
    geometric_integrity: 0.95
    manifold_integrity: 0.98
  expected_verifier:
    passed: true
    escalate: false
```

### 6.4 Fixture 4: Valid Low Coherence (Should Escalate)

```yaml
fixture_valid_low_coherence:
  input:
    latent_captures:
      - condition: "baseline"
        activations: [[1.0] * 64]
      - condition: "baseline"
        activations: [[1.0] * 64]
      - condition: "noise"
        activations: [[10.0] * 64]
    structural_analysis:
      overall_structural_coherence: 0.25
      conditions_tested: ["noise"]
      conditions:
        noise:
          mean_stability: 0.25
          mean_intervention_sensitivity: 0.75
          sample_count: 1
    rsa_correlation: 0.15
    geometric_integrity: 0.25
    manifold_integrity: 0.20
  expected_verifier:
    passed: false
    escalate: true
```

### 6.5 Fixture 5: Empty Captures (Error Handling)

```yaml
fixture_empty_captures:
  input:
    latent_captures: []
    structural_analysis:
      overall_structural_coherence: 0.0
      conditions_tested: []
      conditions: {}
    rsa_correlation: 0.0
    geometric_integrity: 0.0
    manifold_integrity: 0.0
  expected_error: "No baseline captures"
```

### 6.6 Fixture 6: Mismatched Dimensions (Error Handling)

```yaml
fixture_mismatched_dimensions:
  input:
    latent_captures:
      - condition: "baseline"
        activations: [[1.0, 2.0, 3.0]]  # 3 dims
      - condition: "intervention"
        activations: [[1.0, 2.0]]        # 2 dims - MISMATCH
  expected_behavior: "skip mismatched"
```

### 6.7 Fixture 7: Missing Baseline (Error)

```yaml
fixture_missing_baseline:
  input:
    latent_captures:
      - condition: "intervention"
        activations: [[1.0, 2.0]]
      - condition: "noise"
        activations: [[3.0, 4.0]]
  expected_error: "Baseline 'baseline' not found"
```

### 6.8 Fixture 8: Single Capture (Manifold = 1.0)

```yaml
fixture_single_capture:
  input:
    latent_captures:
      - condition: "baseline"
        activations: [[1.0, 2.0, 3.0]]
  expected_manifold_integrity: 1.0
```

### 6.9 Fixture 9: Semantic Truth True (Rejected)

```yaml
fixture_semantic_truth_true:
  description: "semantic_truth=true must be rejected"
  input_modification:
    authority:
      semantic_truth: true
  expected_error: "SemionAuthorityError"
  expected_message: "semantic_truth"
```

### 6.10 Fixture 10: Non-Advisory Authority (Rejected)

```yaml
fixture_non_advisory_authority:
  description: "authority.kind != advisory must be rejected"
  input_modification:
    authority:
      kind: "authoritative"
  expected_error: "SemionAuthorityError"
  expected_message: "advisory"
```

---

## 7. Qualification Receipt Structure

Upon successful gate completion, a NOESIS-Q1 receipt is emitted:

```json
{
  "receipt_id": "NOESIS-Q1-2026-10-04-001",
  "receipt_type": "qualification",
  "subsystem": "noesis_latent_v1",
  "status": "PROVISIONALLY_QUALIFIED",
  "issued_at": "2026-10-04T...Z",
  "issued_by": "operator",
  "gates": {
    "Q1-SPEC": { "passed": true, "artifact": "noesis_latent_v1.spec.md" },
    "Q1-FIXTURE": { "passed": true, "artifact": "noesis_q1_fixtures.yaml" },
    "Q1-ADAPTER": { "passed": true, "artifact": "test_noesis_q1.py" },
    "Q1-SCHEMA": { "passed": true, "artifact": "noesis.latent.v1 (latent structure schema)" },
    "Q1-VERIFIER": { "passed": true, "artifact": "abraxas/evidence/verifiers/latent.py" },
    "Q1-ARBITRATION": { "passed": true, "artifact": "integration_test_production_arbiter.py" }
  },
  "sha256": "computed_over_all_artifacts",
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

---

## 8. Pairwise Conformance (Future)

Per the ecosystem roadmap, pairwise conformance requires:
- **HYPERLEX→NOESIS**: Hyperlex lexical observations → Noesis latent evidence/falsification
  - **Status**: UNBLOCKED ✅ (both HYPERLEX-Q1 and NOESIS-Q1 qualified)
- **NOESIS→TRUTINA**: Noesis latent structure → Trutina calibration
  - **Status**: BLOCKED — requires TRUTINA-Q1
- **NOESIS→ABRAXAS**: Noesis latent evidence → Abraxas SHADOW/FORECAST governance
  - **Status**: BLOCKED — requires ABRAXAS-Q1

---

## 9. Execution Notes

- All work remains **CANON-SHADOW / ADVISORY_ONLY**
- No canon mutation without explicit operator gate
- No production activation / FORECAST escalation
- Receipt emitted only after operator review and acceptance
- Formalizes existing receipt `28c840dd` (PR #31) with full gate evidence