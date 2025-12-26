# SOD (Second-Order Symbolic Dynamics) Specification

**Version**: 1.0 (Abraxas v1.4)
**Status**: Scaffold Only (No Simulation Engine)

---

## Overview

SOD provides deterministic frameworks for modeling narrative cascades, counter-narratives, epistemic fatigue, susceptibility profiles, and recovery trajectories. v1.4 implements deterministic scaffolds that emit scenario envelopes with falsifiers. Academic simulation primitives are deferred to future versions.

---

## Modules

### NCP (Narrative Cascade Predictor)

**Purpose**: Predicts cascade scenarios from τ + D/M inputs

**Inputs**:
- τ snapshots (τₕ, τᵥ, τₚ)
- D/M risk indices (IRI, MRI)
- Weather affinity scores
- Context data

**Outputs**: ScenarioEnvelope containing:
- Top-N cascade paths (sorted by probability)
- Each path includes:
  - Trigger (initiating event description)
  - Probability [0,1] (deterministic heuristic score)
  - Duration (hours)
  - Intermediate states
  - Terminus (final state)
- Falsifiers (counterfactual conditions)
- Confidence (LOW/MED/HIGH)

**Usage**:
```python
from abraxas.sod import NarrativeCascadePredictor, SODInput

ncp = NarrativeCascadePredictor(top_k=5, min_probability=0.1)
sod_input = SODInput(
    tau_snapshot=tau,
    risk_indices=risk,
    affinity_score=affinity,
    context={}
)

envelope = ncp.predict(sod_input, run_id="RUN-001")

for path in envelope.paths:
    print(f"{path.trigger}: {path.probability:.2f} → {path.terminus}")
```

---

### CNF (Counter-Narrative Forecaster)

**Purpose**: Generates counter-narrative strategies for cascade scenarios

**Inputs**: ScenarioEnvelope from NCP

**Outputs**: List of CounterNarrativeStrategy:
- Strategy description
- Intervention points (where/when to intervene)
- Effectiveness score [0,1]
- Resource requirements

**Usage**:
```python
from abraxas.sod import CounterNarrativeForecaster

cnf = CounterNarrativeForecaster(effectiveness_threshold=0.3)
strategies = cnf.forecast(scenario_envelope)

for strategy in strategies:
    print(f"{strategy.description}: {strategy.effectiveness_score:.2f}")
    print(f"  Intervention points: {strategy.intervention_points}")
```

---

### EFTE (Epistemic Fatigue Threshold Engine)

**Purpose**: Models declining engagement under repetition saturation

**Inputs**:
- Exposure count
- Time window (hours)
- RRS score (Repetition/Redundancy Score)
- Engagement trend (time-series)

**Outputs**: FatigueThreshold:
- Threshold [0,1] (current fatigue level)
- Saturation risk (LOW/MED/HIGH)
- Exposure density (exposures/hour)
- Declining engagement flag

**Usage**:
```python
from abraxas.sod import EpistemicFatigueThresholdEngine

efte = EpistemicFatigueThresholdEngine(saturation_threshold=0.7)
fatigue = efte.compute_fatigue(
    exposure_count=100,
    time_window_hours=24,
    rrs_score=0.8,
    engagement_trend=[0.9, 0.85, 0.8, 0.7, 0.6]
)

print(f"Fatigue: {fatigue.threshold:.2f}, Risk: {fatigue.saturation_risk}")
```

---

### SPM (Susceptibility Profile Mapper)

**Purpose**: Maps demographic/context features to susceptibility per weather type

**Inputs**:
- Demographic factors (dict)
- Historical affinities (dict mapping weather type → affinity score)

**Outputs**: SusceptibilityProfile:
- Weather affinities (dict mapping weather type → susceptibility [0,1])
- Demographic factors (preserved)
- Historical resonance [0,1]

**Usage**:
```python
from abraxas.sod import SusceptibilityProfileMapper

spm = SusceptibilityProfileMapper()
profile = spm.map_profile(
    demographic_factors={"age": 25, "region": "urban"},
    historical_affinities={"MW-01": 0.7, "MW-03": 0.8}
)

print(f"Susceptibility to MW-03: {profile.weather_affinities['MW-03']:.2f}")
```

---

### RRM (Recovery & Re-Stabilization Model)

**Purpose**: Models return to baseline after cascade disruption

**Inputs**:
- Cascade severity [0,1]
- Counter-narrative interventions (list)
- Current time (optional, for return date calculation)

**Outputs**: RecoveryTimeline:
- Stabilization probability [0,1]
- Recovery duration (hours)
- Intervention impact [0,1]
- Baseline return date (ISO8601Z, optional)

**Usage**:
```python
from abraxas.sod import RecoveryReStabilizationModel

rrm = RecoveryReStabilizationModel(baseline_recovery_hours=336)
timeline = rrm.model_recovery(
    cascade_severity=0.7,
    interventions=counter_strategies,
    current_time_utc="2025-12-25T12:00:00Z"
)

print(f"Stabilization: {timeline.stabilization_probability:.2f}")
print(f"Recovery: {timeline.recovery_duration_hours}h")
print(f"Return date: {timeline.baseline_return_date}")
```

---

## Data Models

### ScenarioEnvelope
```python
@dataclass(frozen=True)
class ScenarioEnvelope:
    scenario_id: str
    paths: List[ScenarioPath]
    falsifiers: List[str]
    confidence: str  # LOW/MED/HIGH
    provenance: Provenance
```

### ScenarioPath
```python
@dataclass(frozen=True)
class ScenarioPath:
    path_id: str
    trigger: str
    probability: float  # [0,1]
    duration_hours: int
    intermediates: List[str]
    terminus: str
```

---

## Deterministic Heuristics (v1.4)

**NCP Path Generation**:
- Viral spread: High τᵥ (> 0.5), probability = min(τᵥ / 2.0, 1.0)
- Coordinated amplification: MRI > 60 AND CUS > 0.7
- Slow decay: Low τᵥ (< 0.1), high τₕ (> 168h)
- Rapid collapse: High IRI (> 70)
- Revival wave: Positive τᵥ + low τₕ (< 48h)

**CNF Strategy Selection**:
- Early intervention: High-probability paths (> 0.5)
- Credibility injection: Coordinated campaigns
- Inoculation: Viral spread patterns
- Decay acceleration: Slow decay paths
- Revival prevention: Revival wave detection

**EFTE Fatigue Calculation**:
- Base fatigue = min(exposure_density * RRS, 1.0)
- Boost if engagement declining (1.5x multiplier)
- Saturation risk: HIGH if threshold ≥ 0.7, MED if ≥ 0.4, else LOW

---

## Falsifiers

**Purpose**: Counterfactual conditions that would invalidate scenario

**Examples**:
- Velocity reversal: τᵥ becomes negative when currently positive
- Integrity restoration: IRI drops below 30 from high values
- Platform intervention: Content removal or throttling
- External disruption: Competing narrative emergence

**Usage**: Include falsifiers in scenario envelopes for transparency and scenario invalidation detection.

---

## Limitations (v1.4)

**What SOD v1.4 Is**:
- Deterministic heuristic scaffolds
- Scenario envelope generators
- Risk estimators (not simulators)

**What SOD v1.4 Is NOT**:
- Stochastic simulation engine
- Predictive model with temporal evolution
- Agent-based model
- Real-time streaming system

**Future Development**:
- Academic simulation primitives (v1.5)
- Monte Carlo scenario sampling (v1.5)
- Temporal evolution models (v1.6)
- LLM integration for narrative generation (v1.6)

---

## Testing

All SOD modules have deterministic golden tests:

```bash
pytest tests/test_sod_outputs.py
```

**Test Coverage**:
- NCP scenario generation
- CNF strategy generation
- EFTE fatigue computation
- SPM profile mapping
- RRM recovery modeling

---

## References

- Main Specification: `docs/specs/v1_4_temporal_adversarial.md`
- Canonical Ledger: `docs/canon/ABRAXAS_CANON_LEDGER.txt`
- Implementation: `abraxas/sod/`
