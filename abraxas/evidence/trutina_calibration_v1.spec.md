# TRUTINA-Q1 Specification

**Status**: DRAFT — SHADOW / ADVISORY_ONLY
**Version**: 1.0
**Receipt Reference**: TRUTINA-Q1-SPEC-2026-10-04-001
**Dependencies**: NOESIS-Q1 (PROVISIONALLY_QUALIFIED)

---

## 1. Scope

TRUTINA-Q1 defines the qualification evidence for **Trutina Calibration Engine** as an evidence-producing subsystem within the Abraxas ecosystem. Trutina provides **CALIBRATION** evidence type based on Brier scoring, probabilistic calibration (Platt scaling, isotonic regression), and regime-aware calibration across market/regime conditions.

**Canonical Boundary**:
```
TRUTINA_OUTPUT != SEMANTIC_TRUTH
influence_policy = NONE
valid_for_forecast = false
lane = shadow
```

---

## 2. Qualification Gates

Following the ecosystem qualification framework (AC-EIC-Q1), TRUTINA-Q1 requires evidence across these gates:

| Gate | Requirement | Evidence Artifact |
|------|-------------|-------------------|
| **Q1-SPEC** | Complete specification with calibration schemas, contracts, and invariants | `trutina_calibration_v1.spec.md` (this document) |
| **Q1-FIXTURE** | Deterministic test fixtures with known forecasts/outcomes | `trutina_q1_fixtures.yaml` |
| **Q1-ADAPTER** | Abraxas adapter passes authority-boundary tests | `test_trutina_q1.py` |
| **Q1-SCHEMA** | Wire-shape schema validated against calibration schema | `trutina.brier.v1` (Brier scoring schema) |
| **Q1-VERIFIER** | CalibrationVerifier passes verification tests | `abraxas/evidence/verifiers/calibration.py` |
| **Q1-ARBITRATION** | Evidence arbitrates correctly through 6-gate governor | Integration test with ProductionArbiter |

---

## 3. Wire-Shape Contract

### 3.1 TrutinaObservation (v1)

```json
{
  "schema": "trutina.brier.v1",
  "version": "TRUTINA_BRIER_V1",
  "observation_id": "string (hex, 16+ chars)",
  "input_hash": "string (hex, 64 chars)",
  "authority": {
    "kind": "advisory",
    "source": "trutina",
    "semantic_truth": false,
    "may_authorize": false,
    "may_mutate_governing_state": false,
    "role": "OBSERVATION | EVIDENCE | SHADOW_SIGNAL"
  },
  "forecasts": [
    {
      "forecast_id": "string",
      "probability": "float [0,1]",
      "signal_key": "string",
      "mapping_version": "string"
    }
  ],
  "outcomes": [
    {
      "forecast_id": "string",
      "outcome_value": "int (0|1)",
      "settlement_id": "string"
    }
  ],
  "calibration": {
    "method": "PLATT | ISOTONIC | BETA | REGIME_AWARE",
    "parameters": {},
    "regimes": ["stable", "contagion", "shock", "recovery"],
    "brier_score": "float [0,1]",
    "reliability": "float [0,1]",
    "resolution": "float [0,1]",
    "uncertainty": "float [0,1]"
  },
  "provenance": {
    "instrument_version": "TRUTINA_BRIER_V1",
    "contract_version": "trutina.brier.v1",
    "ontology_version": "BRIER_SCORING_V1_FINAL",
    "manifest_sha256": "string (hex, 64 chars)",
    "schema_sha256": "string (hex, 64 chars)",
    "settlement_ref": "specs/trutina/brier-scoring-settlement.md",
    "settlement_receipt": "string (hex, 64 chars)",
    "artifact_hashes": {}
  }
}
```

### 3.2 Abraxas Advisory Evidence (Adapter Output)

The `TrutinaEvidenceProvider.produce_evidence()` transforms the above into Abraxas EvidenceEnvelope:

```json
{
  "engine": "trutina",
  "engine_version": "trutina.brier.v1",
  "model_identity": "trutina.brier.v1",
  "evidence_type": "CALIBRATION",
  "confidence": "float [0,1] (1 - brier_score)",
  "uncertainty": "float [0,1] (brier_score)",
  "entropy": "float [0,1] (uncertainty component)",
  "provenance": {
    "source": "trutina.brier.v1",
    "method": "brier_calibration",
    "brier_score": "float [0,1]",
    "reliability": "float [0,1]",
    "resolution": "float [0,1]",
    "uncertainty": "float [0,1]",
    "calibration_method": "PLATT | ISOTONIC | BETA | REGIME_AWARE",
    "regimes_tested": ["stable", "contagion", "shock", "recovery"],
    "authority": "advisory",
    "semantic_truth": false,
    "influence_policy": "NONE",
    "valid_for_forecast": false,
    "lane": "shadow"
  }
}
```

---

## 4. Calibration Schema

### 4.1 Calibration Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| `PLATT` | Platt scaling (sigmoid) | Binary classification calibration |
| `ISOTONIC` | Isotonic regression | Non-parametric monotonic calibration |
| `BETA` | Beta calibration | Flexible calibration curves |
| `REGIME_AWARE` | Per-regime calibration | Market regime-dependent calibration |

### 4.2 Regimes

| Regime | Description | Calibration Approach |
|--------|-------------|---------------------|
| `stable` | Low volatility, normal conditions | Standard Platt/Isotonic |
| `contagion` | Crisis propagation, high correlation | Beta + regime shift detection |
| `shock` | Sudden regime change | CUSUM + adaptive recalibration |
| `recovery` | Post-crisis normalization | Weighted historical + current |

### 4.3 Metrics

| Metric | Range | Threshold | Meaning |
|--------|-------|-----------|---------|
| `brier_score` | [0,1] | ≤0.25 | Mean squared error of predictions |
| `reliability` | [0,1] | ≤0.1 | Calibration reliability (ECE) |
| `resolution` | [0,1] | ≥0.1 | Discriminatory power |
| `uncertainty` | [0,1] | — | Outcome entropy |

---

## 5. Invariants (Must Hold)

1. **Authority Boundary**: `semantic_truth == false` ALWAYS
2. **Advisory Only**: `authority == "advisory"` ALWAYS
3. **No Forecast Influence**: `valid_for_forecast == false` ALWAYS
4. **No Governance Mutation**: `may_mutate_governing_state == false` ALWAYS
5. **Shadow Lane**: `lane == "shadow"` ALWAYS
6. **Probability Bounds**: All probabilities in [0,1]
7. **Outcome Binary**: All outcomes in {0,1}
8. **Forecast-Outcome Alignment**: Lengths must match

---

## 6. Test Fixtures

### 6.1 Fixture 1: Valid Calibration (Platt Scaling)

```yaml
fixture_valid_calibration:
  input:
    schema: "trutina.brier.v1"
    version: "TRUTINA_BRIER_V1"
    observation_id: "abc12345deadbeef"
    input_hash: "0" * 64
    authority:
      kind: "advisory"
      source: "trutina"
      semantic_truth: false
      may_authorize: false
      may_mutate_governing_state: false
      role: "EVIDENCE"
    forecasts:
      - forecast_id: "f1"
        probability: 0.8
        signal_key: "btc_long"
        mapping_version: "v1"
      - forecast_id: "f2"
        probability: 0.3
        signal_key: "eth_short"
        mapping_version: "v1"
      # ... 98 more forecasts for 100 total
    outcomes:
      - forecast_id: "f1"
        outcome_value: 1
        settlement_id: "s1"
      - forecast_id: "f2"
        outcome_value: 0
        settlement_id: "s2"
      # ... 98 more outcomes
    calibration:
      method: "PLATT"
      parameters: {A: 1.2, B: -0.3}
      regimes: ["stable"]
      brier_score: 0.12
      reliability: 0.05
      resolution: 0.25
      uncertainty: 0.18
    provenance:
      instrument_version: "TRUTINA_BRIER_V1"
      contract_version: "trutina.brier.v1"
      ontology_version: "BRIER_SCORING_V1_FINAL"
      manifest_sha256: "c" * 64
      schema_sha256: "d" * 64
      settlement_ref: "specs/trutina/brier-scoring-settlement.md"
      settlement_receipt: "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
      artifact_hashes: {}
  expected_output:
    engine: "trutina"
    engine_version: "trutina.brier.v1"
    model_identity: "trutina.brier.v1"
    evidence_type: "CALIBRATION"
    confidence: 0.88
    uncertainty: 0.12
    provenance:
      brier_score: 0.12
      reliability: 0.05
      resolution: 0.25
      uncertainty: 0.18
      calibration_method: "PLATT"
      regimes_tested: ["stable"]
```

### 6.2 Fixture 2: Valid Regime-Aware Calibration

```yaml
fixture_valid_regime_aware:
  input:
    forecasts: [100 forecasts across regimes]
    outcomes: [100 outcomes]
    calibration:
      method: "REGIME_AWARE"
      regimes: ["stable", "contagion", "shock", "recovery"]
      brier_score: 0.18
      reliability: 0.08
      resolution: 0.35
      uncertainty: 0.22
  expected_verifier:
    passed: true
    escalate: false
```

### 6.3 Fixture 3: Valid Brier Ledger

```yaml
fixture_valid_brier_ledger:
  input:
    calibration:
      method: "PLATT"
      brier_score: 0.15
    provenance:
      ledger_entries: 1000
      ledger_generation: 5
  expected_output:
    provenance:
      ledger_entries: 1000
      ledger_generation: 5
```

### 6.4 Fixture 4: Valid Platt Scaling

```yaml
fixture_valid_platt_scaling:
  input:
    calibration:
      method: "PLATT"
      parameters: {A: 1.5, B: -0.5}
      brier_score: 0.10
      reliability: 0.03
  expected_verifier:
    passed: true
```

### 6.5 Fixture 5: Invalid Probability (Negative)

```yaml
fixture_invalid_probability_out_of_range:
  description: "probability > 1 must be rejected"
  input_modification:
    forecasts:
      - forecast_id: "f1"
        probability: 1.5
        signal_key: "test"
        mapping_version: "v1"
  expected_error: "ValueError"
  expected_message: "probability out of [0,1]"
```

### 6.6 Fixture 6: Invalid Outcome (Negative)

```yaml
fixture_invalid_outcome_not_binary:
  description: "outcome not 0/1 must be rejected"
  input_modification:
    outcomes:
      - forecast_id: "f1"
        outcome_value: 2
        settlement_id: "s1"
  expected_error: "ValueError"
  expected_message: "observed_outcome must be 0 or 1"
```

### 6.7 Fixture 7: Mismatched Lengths (Negative)

```yaml
fixture_mismatched_forecasts_outcomes:
  description: "forecasts/outcomes length mismatch must be rejected"
  input_modification:
    forecasts: [100 forecasts]
    outcomes: [99 outcomes]
  expected_error: "ValueError"
  expected_message: "length mismatch"
```

### 6.8 Fixture 8: Empty Forecasts (Negative)

```yaml
fixture_empty_forecasts:
  description: "empty forecasts must be rejected"
  input_modification:
    forecasts: []
    outcomes: []
  expected_error: "ValueError"
  expected_message: "empty"
```

---

## 7. Qualification Receipt Structure

Upon successful gate completion, a TRUTINA-Q1 receipt is emitted:

```json
{
  "receipt_id": "TRUTINA-Q1-2026-10-04-001",
  "receipt_type": "qualification",
  "subsystem": "trutina_calibration_v1",
  "status": "PROVISIONALLY_QUALIFIED",
  "issued_at": "2026-10-04T...Z",
  "issued_by": "operator",
  "gates": {
    "Q1-SPEC": { "passed": true, "artifact": "trutina_calibration_v1.spec.md" },
    "Q1-FIXTURE": { "passed": true, "artifact": "trutina_q1_fixtures.yaml" },
    "Q1-ADAPTER": { "passed": true, "artifact": "test_trutina_q1.py" },
    "Q1-SCHEMA": { "passed": true, "artifact": "trutina.brier.v1 (Brier scoring schema)" },
    "Q1-VERIFIER": { "passed": true, "artifact": "abraxas/evidence/verifiers/calibration.py" },
    "Q1-ARBITRATION": { "passed": true, "artifact": "integration_test_production_arbiter.py" }
  },
  "sha256": "computed_over_all_artifacts",
  "notes": [
    "TRUTINA provides CALIBRATION evidence only",
    "Brier scoring + calibration (Platt/Isotonic/Beta/Regime-Aware) validated",
    "Pairwise NOESIS→TRUTINA unblocked upon NOESIS-Q1 completion ✅",
    "Pairwise TRUTINA→ABRAXAS unblocked upon ABRAXAS-Q1",
    "EXP-001 remains DEFERRED until AC-EIC-G1"
  ]
}
```

---

## 8. Pairwise Conformance (Future)

Per the ecosystem roadmap, pairwise conformance requires:
- **NOESIS→TRUTINA**: Noesis latent structure → Trutina calibration
  - **Status**: UNBLOCKED ✅ (NOESIS-Q1 qualified, TRUTINA-Q1 in progress)
- **TRUTINA→ABRAXAS**: Trutina calibration → Abraxas SHADOW/FORECAST governance
  - **Status**: BLOCKED — requires ABRAXAS-Q1

---

## 9. Execution Notes

- All work remains **CANON-SHADOW / ADVISORY_ONLY**
- No canon mutation without explicit operator gate
- No production activation / FORECAST escalation
- Receipt emitted only after operator review and acceptance