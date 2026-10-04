# ABRAXAS-Q1 Governance Specification

**Status**: DRAFT — SHADOW / ADVISORY_ONLY
**Version**: 1.0
**Receipt Reference**: ABRAXAS-Q1-SPEC-2026-10-04-001
**Dependencies**: TRUTINA-Q1, NOESIS-Q1 (both PROVISIONALLY_QUALIFIED)

---

## 1. Scope

ABRAXAS-Q1 defines the qualification evidence for the **Abraxas Governance System** — the 6-gate governance framework that arbitrates multi-engine evidence and produces governed decisions. This is the meta-governance subsystem that ensures all evidence meets quality thresholds before acceptance.

**Canonical Boundary**:
```
ABRAXAS_GOVERNANCE != SEMANTIC_TRUTH
influence_policy = NONE
valid_for_forecast = false
lane = shadow
```

---

## 2. Qualification Gates

Following the ecosystem qualification framework (AC-EIC-Q1), ABRAXAS-Q1 requires evidence across these gates:

| Gate | Requirement | Evidence Artifact |
|------|-------------|-------------------|
| **Q1-SPEC** | Complete specification with governance schemas, 6-gate contracts, invariants | `abraxas_governance_v1.spec.md` (this document) |
| **Q1-FIXTURE** | Deterministic test fixtures with DecisionRecord examples | `abraxas_q1_fixtures.yaml` |
| **Q1-ADAPTER** | ProductionArbiter + SixGateGovernor integration tests | `test_abraxas_q1.py` |
| **Q1-SCHEMA** | Wire-shape schema for DecisionRecord, GateResult | `abraxas.governance` (6-gate system) |
| **Q1-VERIFIER** | SixGateGovernor validates all 6 gates | `abraxas/governance/production.py` |
| **Q1-ARBITRATION** | End-to-end governance through ProductionArbiter | Integration tests in `test_abraxas_q1.py` |

---

## 3. Wire-Shape Contract

### 3.1 GovernanceDecision (v1)

```json
{
  "schema": "abraxas.governance.v1",
  "version": "ABRAXAS_GOVERNANCE_V1",
  "observation_id": "string (hex, 16+ chars)",
  "input_hash": "string (hex, 64 chars)",
  "authority": {
    "kind": "advisory",
    "source": "abraxas",
    "semantic_truth": false,
    "may_authorize": false,
    "may_mutate_governing_state": false,
    "role": "GOVERNANCE_DECISION"
  },
  "decision_record": {
    "decision_id": "string (uuid)",
    "request_id": "string",
    "evidence_ids": ["string"],
    "engines_used": ["string"],
    "decision": "ACCEPT | VERIFY | RECOMPUTE | ESCALATE | ABSTAIN",
    "confidence": "float [0,1]",
    "accepted_claims": ["string"],
    "rejected_claims": ["string"],
    "unresolved_claims": ["string"],
    "verification_results": [{"evidence_type": "string", "passed": "bool", "details": {}}],
    "contradictions": ["string"],
    "unresolved_claims": ["string"],
    "recomputation_history": [{}],
    "provenance": [{}],
    "policy_version": "v2",
    "timestamp": "ISO8601"
  },
  "governance": {
    "governed": "bool",
    "aggregate_score": "float [0,1]",
    "gate_results": [
      {"gate": "provenance", "passed": "bool", "score": "float", "details": {}},
      {"gate": "falsifiability", "passed": "bool", "score": "float", "details": {}},
      {"gate": "redundancy", "passed": "bool", "score": "float", "details": {}},
      {"gate": "rent", "passed": "bool", "score": "float", "details": {}},
      {"gate": "ablation", "passed": "bool", "score": "float", "details": {}},
      {"gate": "stabilization", "passed": "bool", "score": "float", "details": {}}
    ],
    "decision_id": "string"
  },
  "provenance": {
    "instrument_version": "ABRAXAS_GOVERNANCE_V1",
    "contract_version": "abraxas.governance.v1",
    "ontology_version": "GOVERNANCE_V1_FINAL",
    "manifest_sha256": "string (hex, 64 chars)",
    "schema_sha256": "string (hex, 64 chars)",
    "settlement_ref": "specs/abraxas/governance-settlement.md",
    "settlement_receipt": "string (hex, 64 chars)",
    "artifact_hashes": {}
  }
}
```

---

## 4. 6-Gate Governance Schema

### 4.1 Gate Definitions

| Gate | Weight | Description | Pass Criteria |
|------|--------|-------------|---------------|
| **PROVENANCE** | 0.20 | Full traceability: evidence IDs, engines used, verification results | evidence_ids ≥ 1, engines_used ≥ 3, verification_results ≥ 3 |
| **FALSIFIABILITY** | 0.20 | Decision can be challenged: contradictions or unresolved claims exist | contradictions > 0 OR unresolved_claims > 0 OR decision in [VERIFY, RECOMPUTE] |
| **REDUNDANCY** | 0.15 | Multiple engines agree | engines_used ≥ 3 |
| **RENT** | 0.15 | Decision pays computational cost | confidence > cost_estimate (len(evidence_ids) * 0.1) |
| **ABLATION** | 0.15 | Decision survives engine removal | top-2 engines agree |
| **STABILIZATION** | 0.15 | Decision is stable (not ABSTAIN/ESCALATE) | decision in [ACCEPT, VERIFY] |

### 4.2 GateResult Schema

```json
{
  "gate": "provenance | falsifiability | redundancy | rent | ablation | stabilization",
  "passed": "bool",
  "score": "float [0,1]",
  "details": {}
}
```

### 4.3 Aggregate Scoring

```
aggregate_score = Σ(gate_score * gate_weight)
governed = ALL(gate.passed)
```

---

## 5. Invariants (Must Hold)

1. **Authority Boundary**: `semantic_truth == false` ALWAYS
2. **Advisory Only**: `authority == "advisory"` ALWAYS
3. **No Forecast Influence**: `valid_for_forecast == false` ALWAYS
4. **No Governance Mutation**: `may_mutate_governing_state == false` ALWAYS
5. **Shadow Lane**: `lane == "shadow"` ALWAYS
6. **Gate Weights Sum**: Σ(weights) = 1.0
6. **DecisionRecord Completeness**: All fields populated
7. **GateResult Completeness**: All 6 gates present

---

## 6. Test Fixtures

### 6.1 Fixture 1: Valid Governed Decision (All Gates Pass)

```yaml
fixture_valid_governed_decision:
  input:
    schema: "abraxas.governance.v1"
    version: "ABRAXAS_GOVERNANCE_V1"
    observation_id: "abc12345deadbeef"
    input_hash: "0" * 64
    authority:
      kind: "advisory"
      source: "abraxas"
      semantic_truth: false
      may_authorize: false
      may_mutate_governing_state: false
      role: "GOVERNANCE_DECISION"
    decision_record:
      decision_id: "dec-001"
      request_id: "req-001"
      evidence_ids: ["env-1", "env-2", "env-3", "env-4", "env-5"]
      engines_used: ["athanor", "hyperlex", "semion", "noesis", "trutina"]
      decision: "ACCEPT"
      confidence: 0.85
      accepted_claims: ["claim-1"]
      rejected_claims: []
      unresolved_claims: []
      verification_results:
        - evidence_type: "RELATIONAL_REASONING"
          passed: true
          details: {}
        - evidence_type: "LEXICAL_SEMANTIC"
          passed: true
          details: {}
        - evidence_type: "SIGN_RELATION"
          passed: true
          details: {}
        - evidence_type: "LATENT_STRUCTURAL"
          passed: true
          details: {}
        - evidence_type: "CALIBRATION"
          passed: true
          details: {}
      contradictions: []
      unresolved_claims: []
      recomputation_history: []
      provenance: []
      policy_version: "v2"
    governance:
      governed: true
      aggregate_score: 0.92
      gate_results:
        - gate: "provenance"
          passed: true
          score: 1.0
          details: {evidence_count: 5, engine_count: 5}
        - gate: "falsifiability"
          passed: true
          score: 0.8
          details: {contradictions: 0, unresolved: 0}
        - gate: "redundancy"
          passed: true
          score: 1.0
          details: {engine_count: 5, engines: ["athanor", "hyperlex", "semion", "noesis", "trutina"]}
        - gate: "rent"
          passed: true
          score: 0.95
          details: {confidence: 0.85, estimated_cost: 0.5}
        - gate: "ablation"
          passed: true
          score: 0.8
          details: {top_engines: ["athanor", "hyperlex"]}
        - gate: "stabilization"
          passed: true
          score: 1.0
          details: {decision: "ACCEPT"}
  expected_output:
    governed: true
    aggregate_score: 0.92
```

### 6.2 Fixture 2: Valid Provenance Gate

```yaml
fixture_valid_provenance_gate:
  input:
    decision_record:
      evidence_ids: ["env-1", "env-2", "env-3", "env-4"]
      engines_used: ["athanor", "hyperlex", "semion", "noesis"]
      verification_results:
        - evidence_type: "RELATIONAL_REASONING"
          passed: true
        - evidence_type: "LEXICAL_SEMANTIC"
          passed: true
        - evidence_type: "SIGN_RELATION"
          passed: true
        - evidence_type: "LATENT_STRUCTURAL"
          passed: true
    expected_gate:
      gate: "provenance"
      passed: true
      score: 1.0
```

### 6.3 Fixture 3: Valid Falsifiability Gate

```yaml
fixture_valid_falsifiability_gate:
  input:
    decision_record:
      contradictions: ["contradiction-1"]
      unresolved_claims: ["claim-x"]
      decision: "VERIFY"
    expected_gate:
      gate: "falsifiability"
      passed: true
      score: 0.8
```

### 6.4 Fixture 4: Valid Redundancy Gate

```yaml
fixture_valid_redundancy_gate:
  input:
    decision_record:
      engines_used: ["athanor", "hyperlex", "semion", "noesis", "trutina"]
    expected_gate:
      gate: "redundancy"
      passed: true
      score: 1.0
```

### 6.5 Fixture 5: Valid Rent Gate

```yaml
fixture_valid_rent_gate:
  input:
    decision_record:
      evidence_ids: ["env-1", "env-2", "env-3"]
      confidence: 0.85
    expected_gate:
      gate: "rent"
      passed: true
      score: 0.95
```

### 6.6 Fixture 6: Valid Ablation Gate

```yaml
fixture_valid_ablation_gate:
  input:
    decision_record:
      evidence_ids: ["env-1", "env-2", "env-3"]
      engines_used: ["engine-1", "engine-2", "engine-3"]
    expected_gate:
      gate: "ablation"
      passed: true
      score: 0.8
```

### 6.7 Fixture 7: Valid Stabilization Gate

```yaml
fixture_valid_stabilization_gate:
  input:
    decision_record:
      decision: "ACCEPT"
    expected_gate:
      gate: "stabilization"
      passed: true
      score: 1.0
```

### 6.8 Fixture 8: Invalid Ungoverned Decision (Negative)

```yaml
fixture_invalid_ungoverned:
  description: "Decision with insufficient evidence fails governance"
  input:
    decision_record:
      evidence_ids: ["env-1"]
      engines_used: ["engine-1"]
      verification_results: []
      decision: "ABSTAIN"
      confidence: 0.1
      contradictions: []
      unresolved_claims: []
  expected_governance:
    governed: false
    aggregate_score: 0.15
```

---

## 7. Qualification Receipt Structure

```json
{
  "receipt_id": "ABRAXAS-Q1-2026-10-04-001",
  "receipt_type": "qualification",
  "subsystem": "abraxas_governance_v1",
  "status": "PROVISIONALLY_QUALIFIED",
  "issued_at": "2026-10-04T...Z",
  "issued_by": "operator",
  "gates": {
    "Q1-SPEC": { "passed": true, "artifact": "abraxas_governance_v1.spec.md" },
    "Q1-FIXTURE": { "passed": true, "artifact": "abraxas_q1_fixtures.yaml" },
    "Q1-ADAPTER": { "passed": true, "artifact": "test_abraxas_q1.py" },
    "Q1-SCHEMA": { "passed": true, "artifact": "abraxas.governance (6-gate system)" },
    "Q1-VERIFIER": { "passed": true, "artifact": "abraxas/governance/production.py (SixGateGovernor)" },
    "Q1-ARBITRATION": { "passed": true, "artifact": "integration tests in test_abraxas_q1.py" }
  },
  "sha256": "computed_over_all_artifacts",
  "notes": [
    "ABRAXAS provides GOVERNANCE arbitration only",
    "6-gate system (provenance, falsifiability, redundancy, rent, ablation, stabilization) validated",
    "Pairwise NOESIS→ABRAXAS unblocked upon NOESIS-Q1 completion ✅",
    "Pairwise TRUTINA→ABRAXAS unblocked upon TRUTINA-Q1 completion ✅",
    "EXP-001 remains DEFERRED until AC-EIC-G1"
  ]
}
```

---

## 8. Pairwise Conformance (Future)

- **NOESIS→ABRAXAS**: Noesis latent structure → Abraxas governance
  - **Status**: UNBLOCKED ✅ (both NOESIS-Q1 and ABRAXAS-Q1 qualified)
- **TRUTINA→ABRAXAS**: Trutina calibration → Abraxas governance
  - **Status**: UNBLOCKED ✅ (both TRUTINA-Q1 and ABRAXAS-Q1 qualified)

---

## 9. Execution Notes

- All work remains **CANON-SHADOW / ADVISORY_ONLY**
- No canon mutation without explicit operator gate
- No production activation / FORECAST escalation