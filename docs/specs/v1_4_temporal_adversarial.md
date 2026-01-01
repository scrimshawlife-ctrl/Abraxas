## Abraxas v1.4: Temporal & Adversarial Expansion

**Version**: 1.4.0
**Date**: 2025-12-25
**Status**: Production

---

### Overview

Abraxas v1.4 introduces three foundational layers for temporal dynamics, adversarial resilience, and second-order narrative modeling. This expansion transforms Abraxas from a symbolic compression detector into a full-spectrum memetic weather system capable of tracking lifecycle dynamics, assessing information integrity, and modeling cascade scenarios.

---

### τ (Tau) Operator: Temporal Metrics

The τ operator provides three complementary temporal metrics for symbolic lifecycle tracking:

#### τₕ (Tau Half-Life)
- **Purpose**: Measures symbolic persistence under declining reinforcement
- **Model**: Exponential decay model where τₕ = t₁/₂ (time for observation frequency to halve)
- **Silence-as-signal**: Missing observations accelerate decay
- **Output**: Half-life in hours (range: 1-8760 hours)

#### τᵥ (Tau Velocity)
- **Purpose**: Measures emergence/decay slope from time-series observations
- **Formula**: Δcount / Δtime over sliding window
- **Interpretation**:
  - Positive = emergence
  - Negative = decay
  - ~0 = stability
- **Output**: Velocity with sign (events/day)

#### τₚ (Tau Phase Proximity)
- **Purpose**: Measures distance to next lifecycle boundary
- **Lifecycle Phases**: Proto → Front → Saturated → Dormant → Archived
- **Computation**: Derived from τₕ and τᵥ combination against threshold matrix
- **Output**: Proximity score [0,1] to next phase transition

#### Confidence Bands (Deterministic)
- **LOW**: sample_size < 5 OR observation_window < 48 hours
- **MED**: sample_size 5-19 OR variance > threshold
- **HIGH**: sample_size ≥ 20 AND variance ≤ threshold

**Module**: `abraxas.core.temporal_tau`

---

### D/M Layer: Information Integrity Metrics

**IMPORTANT**: These are risk/likelihood estimators, NOT truth adjudication.

#### Artifact Integrity Metrics
- **PPS** (Provenance Presence Score): [0,1], metadata completeness
- **PCS** (Provenance Chain Score): [0,1], traceable source chain
- **MMS** (Mutation Marker Score): [0,1], edit history present
- **SLS** (Source Locality Score): [0,1], cross-platform coherence
- **EIS** (Evidence Integrity Score): [0,1], supporting data quality

#### Narrative Manipulation Metrics
- **FLS** (Framing Leverage Score): [0,1], narrative control indicators
- **EIL** (Emotional Intensity Level): [0,1], affective loading
- **OCS** (Omission/Contextualization Score): [0,1], selective presentation
- **RRS** (Repetition/Redundancy Score): [0,1], saturation tactics
- **MPS** (Misattribution Probability Score): [0,1], source confusion risk
- **CIS** (Coordination Indicator Score): [0,1], synchronized distribution

#### Network/Campaign Metrics
- **CUS** (Coordination/Uniformity Score): [0,1], bot-like patterns
- **SVS** (Source Velocity Score): [0,1], rapid propagation
- **BAS** (Bursting/Amplification Score): [0,1], artificial boosting
- **MDS** (Multi-Domain Spread Score): [0,1], cross-platform coordination

#### Composite Risk Indices
- **IRI** (Integrity Risk Index): [0,100]
  Formula: `100 * (1 - mean(PPS, PCS, MMS, SLS, EIS))`

- **MRI** (Manipulation Risk Index): [0,100]
  Formula: `100 * weighted_mean(FLS, EIL, OCS, RRS, MPS, CIS, CUS, SVS, BAS, MDS)`

**Modules**:
- `abraxas.integrity.dm_metrics`
- `abraxas.integrity.composites`
- `abraxas.integrity.payload_taxonomy`
- `abraxas.integrity.propaganda_archetypes`

---

### AAlmanac: Write-Once, Annotate-Only Ledger

**Storage**: `data/a_almanac/terms.jsonl` (JSONL format)

**Lifecycle States**: Proto → Front → Saturated → Dormant → Archived

**State Transitions** (Deterministic):
- Proto → Front: τᵥ > 0.5 AND obs_count > 5
- Front → Saturated: |τᵥ| < 0.1 AND τₕ > 168h
- Saturated → Dormant: τᵥ < -0.1
- Dormant → Archived: τₕ < 24h
- Revival (any → Proto): mutation_evidence AND new_observation

**API**:
```python
from abraxas.slang.a_almanac_store import AAlmanacStore

store = AAlmanacStore()
term_id = store.create_entry_if_missing(
    term="cap",
    class_id="slang",
    created_at="2025-12-20T00:00:00Z",
    provenance=prov
)

store.append_annotation(
    term_id=term_id,
    annotation_type="observation",
    data={"value": 1.0, "source_id": "twitter-001"},
    provenance=prov
)

state, tau = store.compute_current_state(term_id)
```

**Module**: `abraxas.slang.a_almanac_store`

---

### Memetic Weather Registry

**Five Canonical Types**: MW-01 through MW-05

#### MW-01: Symbolic Drift
- High replacement pressure, rising transparency flux
- Indicators: τᵥ > 0.5, eggcorn formation rate elevated

#### MW-02: Compression Stability
- Low τᵥ, stable τₕ, established patterns
- Indicators: |τᵥ| < 0.1, τₕ variance low

#### MW-03: Emergence Storm
- Rapid new symbol introduction, high τᵥ, volatile τₕ
- Indicators: multiple Proto state entries, τᵥ >> 1.0

#### MW-04: Semantic Saturation
- Dormant transitions, declining engagement
- Indicators: τᵥ < -0.1, Saturated → Dormant transitions

#### MW-05: Revival Wave
- Mutation-driven re-emergence
- Indicators: Archived/Dormant → Proto transitions with mutation evidence

**Affinity Scoring**: Deterministic [0,1] score based on archetype class, tone alignment, and τ signature.

**Module**: `abraxas.weather`

---

### Usage Examples

#### Computing τ Metrics
```python
from abraxas.core.temporal_tau import TauCalculator, Observation

calculator = TauCalculator(git_sha="abc123", host="prod-01")
observations = [
    Observation("2025-12-20T12:00:00Z", 1.0, "src-001"),
    Observation("2025-12-21T12:00:00Z", 1.0, "src-002"),
    # ...
]

snapshot = calculator.compute_snapshot(
    observations,
    run_id="RUN-001",
    current_time_utc="2025-12-25T12:00:00Z"
)

print(f"τₕ = {snapshot.tau_half_life:.2f} hours")
print(f"τᵥ = {snapshot.tau_velocity:.2f} events/day")
print(f"Confidence = {snapshot.confidence.value}")
```

#### Computing D/M Metrics
```python
from abraxas.integrity import compute_artifact_integrity, compute_composite_risk

integrity = compute_artifact_integrity(
    has_timestamp=True,
    has_source_id=True,
    source_chain_length=3,
    cross_platform_matches=2,
    total_platforms_checked=3
)

risk = compute_composite_risk(
    integrity,
    narrative_manipulation,
    network_campaign
)

print(f"IRI = {risk.iri:.1f}")  # Integrity Risk Index
print(f"MRI = {risk.mri:.1f}")  # Manipulation Risk Index
```

#### Running v1.4 Pipeline
```bash
python -m abraxas.cli.abx_run_v1_4 \
  --observations data/obs.json \
  --format both \
  --artifacts cascade_sheet,contamination_advisory \
  --output-dir data/runs/v1_4
```

---

### Configuration

**Environment Variables**: None required (all deterministic)

**Data Directories**:
- `data/a_almanac/` — AAlmanac JSONL storage
- `data/runs/v1_4/` — Default output directory
- `data/runs/last_snapshot.json` — Prior snapshot for delta-only mode

---

### Testing

All modules have golden test coverage with deterministic fixtures:

```bash
pytest tests/test_temporal_tau.py
pytest tests/test_lifecycle.py
pytest tests/test_dm_metrics.py
pytest tests/test_sod_outputs.py
```

Golden outputs stored in: `tests/golden/v1_4/`

---

### Limitations

**v1.4 Scope**:
- SOD modules provide deterministic scaffolds only (no simulation engine)
- D/M metrics require explicit inputs (no automatic extraction)
- AAlmanac is local-only (no distributed sync)

**Future Versions**:
- Academic simulation primitives for SOD (v1.5)
- Real-time streaming integration (v1.5)
- LLM integration for counter-narrative generation (v1.6)

---

### References

- Canonical Ledger: `docs/canon/ABRAXAS_CANON_LEDGER.txt`
- SOD Specification: `docs/specs/sod_second_order_dynamics.md`
- Implementation Plan: `docs/plan/abx_v1_4_implementation_plan.md`
