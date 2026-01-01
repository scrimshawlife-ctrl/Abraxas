# Abraxas Simulation Architecture

**Version**: 1.0
**Status**: Production
**Compatibility**: Abraxas v1.4+

---

## Overview

The Abraxas Simulation Architecture implements a deterministic, provenance-tracked simulation system for modeling misinformation ecosystems with:

- **Network Dynamics**: Graph evolution, community structure, link prediction
- **Game-Theoretic Media Actors**: Strategic misinformation deployment
- **Quantum-Inspired Operators**: Community detection (QUBO-style), link prediction (quantum walk)
- **Temporal Correlations**: State-over-time dependency tracking
- **Two-Layer Reality**: World (latent truth) + Media (perception/distortion)

---

## IMMUTABLE LAWS (Non-Negotiable)

### 1. No Metric Without Simulation
Every metric MUST map to ≥1 simulation variable via ABX-Runes.
Orphan metrics (no rune binding) are REJECTED at startup.

### 2. No Simulation Without Runes
All metric ⇄ simulation variable couplings MUST occur through ABX-Runes.
No direct metric → variable mutation is allowed.

### 3. Determinism First
- All simulations must be seedable
- Same seed + same inputs = same outputs
- Deterministic RNG required

### 4. Provenance Always
Every result must reference:
- Metric versions
- Rune versions
- Simulation schema version
- Input hashes
- SML training sources (paper IDs)

### 5. Complexity Pays Rent
Adding a metric must either:
- Reduce uncertainty
- Increase forecast accuracy
- Expose manipulation risk

Otherwise it is REJECTED.

### 6. Two-Layer Reality
Simulations MUST model:
- **World Layer**: Latent reality (true states, actual network topology, real beliefs)
- **Media Layer**: Distorted representation (propaganda, deepfakes, amplification, bots)

Metrics explicitly declare which layer(s) they observe.

### 7. Quantum-Inspired = Formal Structure
"Quantum-inspired" means mathematical structure analogous to quantum mechanics (superposition, measurement effects, interference) implemented deterministically in classical hardware. NOT actual quantum computing.

---

## Four Canonical Components

### A) Metric Registry (`abraxas/simulation/registries/metric_registry.py`)

**Purpose**: Canonical storage for all observable metrics.

**Each metric declares**:
- `metric_id`: Unique identifier (uppercase snake_case)
- `version`: Semantic version (MAJOR.MINOR.PATCH)
- `description`: What this metric measures
- `metric_class`: Category (integrity_risk, manipulation_risk, network_topology, etc.)
- `units`: Measurement units
- `valid_range`: Min/max bounds
- `decay_half_life`: Relevance decay (hours)
- `dependencies`: Other metrics this depends on
- `adversarial_risk`: Manipulation likelihood [0,1]
- `layer_scope`: ["world"] or ["media"] or ["world", "media"]
- `provenance`: Created timestamp, source, SML paper_refs

**Schema**: `abraxas/simulation/schemas/metric.schema.json`

### B) Simulation Variable Registry (`abraxas/simulation/registries/simvar_registry.py`)

**Purpose**: Canonical storage for latent world state variables.

**Each variable declares**:
- `var_id`: Unique identifier (lowercase snake_case)
- `version`: Semantic version
- `var_class`: Variable class (see Extended Classes below)
- `var_type`: Data type (continuous, discrete, categorical, graph, matrix, tensor)
- `bounds`: Range/categories/shape
- `prior_distribution`: Initialization distribution (may reference SML papers)
- `evolution_model`: Update rule (Markov, opinion dynamics, quantum walk, etc.)
- `coupling_capacity`: Max runes + allowed metric classes
- `layer`: "world" or "media"
- `provenance`: Created timestamp, source

**Extended Variable Classes**:
- `classical_state`: Standard numerical state
- `belief_state`: Opinion/belief distribution (quantum-inspired measurement)
- `context_operator`: Framing/context modulation (media layer)
- `interference_term`: Multi-path interference aggregation
- `persona_filter`: Observer-dependent state projection
- `network_state`: Graph topology
- `community_structure`: Partition/clustering
- `link_probability_field`: Predicted edge probabilities
- `media_actor_state`: Credibility, audience, reach
- `strategy_profile`: Strategic action probabilities
- `payoff_field`: Utility landscape
- `state_over_time`: Temporal correlation container
- `conformity_pressure`: Local peer pressure
- `peer_influence_field`: Spatial influence gradient

**Schema**: `abraxas/simulation/schemas/simvar.schema.json`

### C) ABX-Rune Binding Registry (`abraxas/simulation/registries/rune_registry.py`)

**Purpose**: MANDATORY coupler between metrics and simulation variables.

**Each rune declares** (ALL fields required):
- `rune_id`: Unique identifier (must start with "RUNE_")
- `version`: Semantic version
- `metric_id`: Which metric this binds
- `var_targets`: List of [{var_id, role: observe|influence|both}]
- `layer_targets`: ["world"] and/or ["media"]
- `state_model`: classical | quantum-inspired | hybrid
- `measurement_effect`: non-destructive | partial-collapse | hard-collapse
- `context_sensitivity`: [0,1] how much measurement depends on context
- `observer_model`: How metric reads variable state
  - `observer_type`: linear, probabilistic, threshold, contextual, network_aggregate, game_equilibrium, quantum_measurement
  - `parameters`: Observer-specific config
- `transition_model`: How metric updates variable state
  - `transition_type`: direct_update, opinion_shift, network_rewire, strategy_adapt, conformity_pressure, quantum_walk_step, community_reassignment, no_transition
  - `parameters`: Transition-specific config
- `noise_model`: Measurement uncertainty
  - `noise_type`: gaussian, poisson, uniform, adversarial, none
  - `parameters`: {base_stddev, adversarial_boost}
- `manipulation_model`: How manipulation distorts measurement
  - `manipulation_type`: deepfake, bot_amplification, algorithmic_distortion, astroturfing, none
  - `penetration_scaling`: How noise increases with synthetic content
  - `detection_threshold`: Level at which manipulation becomes detectable
- `constraints`: Hard bounds, conservation laws
- `provenance_manifest`: Created, input_hash, metric_version, var_versions, schema_version, **sml_training_sources**

**Schema**: `abraxas/simulation/schemas/rune_binding.schema.json`

### D) Outcome Ledger (`abraxas/simulation/registries/outcome_ledger.py`)

**Purpose**: Append-only log of simulation outcomes.

**CRITICAL**: No overwrites. No deletions. No "memory summaries."

**Each entry records**:
- `timestamp`: ISO 8601
- `sim_seed`: RNG seed
- `sim_version`: Simulation engine version
- `active_metrics`: [{metric_id, version}, ...]
- `active_runes`: [{rune_id, version}, ...]
- `prior_state_hash`: SHA-256 of state before step
- `prior_state_snapshot`: Minimal state snapshot
- `posterior_state_hash`: SHA-256 of state after step
- `posterior_state_snapshot`: Minimal state snapshot
- `predictions_issued`: Forecasts with confidence intervals
- `real_world_outcomes`: Observations (if available)
- `error_metrics`: RMSE, MAE, calibration error
- `confidence_deltas`: Per-metric confidence changes
- **`measurement_disturbance`**: Magnitude of state perturbation from measurement
- **`world_media_divergence`**: Divergence between world and media layers
- **`network_drift`**: Graph topology change magnitude
- **`strategy_shift`**: Media actor strategy delta (L2 norm)
- **`temporal_correlation_shift`**: Change in state-over-time correlation
- `community_stability`: Fraction of nodes maintaining community (optional)
- `conformity_pressure_avg`: Average conformity pressure (optional)

**Storage Format**: JSONL (append-only, line-oriented)

**Schema**: `abraxas/simulation/schemas/outcome_ledger.schema.json`

---

## SML Integration: Training Data Intake

The **Simulation Mapping Layer (SML)** serves as the training data intake system for Abraxas simulations.

### Data Flow

```
Academic Papers (data/sim_sources/papers.json)
    ↓
SML Parameter Mapping (abraxas/sim_mappings/)
    ↓ map_paper_model()
KnobVector (MRI, IRI, τ_latency, τ_memory)
    ↓
SOD Adapter (abraxas/sod/sim_adapter.py)
    ↓ convert_knobs_to_sod_priors()
SOD Priors (cascade_branching_prob, cascade_damping_factor, etc.)
    ↓
SimVarDefinition.prior_distribution.sml_source
    ↓
Simulation Variable Initialization
    ↓
RuneBinding.provenance_manifest.sml_training_sources
    ↓
Simulation Execution
    ↓
OutcomeEntry (with provenance chain)
```

### Example: Game-Theoretic Misinformation

**Paper**: ARXIV_SPATIAL_GAMES (from SML registry)

**Parameters**:
- `effort`: Propagandist effort → MRI
- `sanction_prob`: Sanction probability → IRI
- `discount`: Temporal discount factor → τ_memory

**SML Mapping**:
```python
from abraxas.sim_mappings import map_paper_model, ModelFamily, ModelParam, PaperRef

paper = PaperRef("ARXIV_SPATIAL_GAMES", "Spatial Games of Fake News", ...)
params = [
    ModelParam("effort", value=5.0),
    ModelParam("sanction_prob", value=0.3),
    ModelParam("discount", value=0.9),
]
mapping = map_paper_model(paper, ModelFamily.GAME_THEORETIC, params)

# mapping.mapped.mri ≈ 0.5  (from effort)
# mapping.mapped.iri ≈ 0.65 (from sanction_prob, sanction_penalty)
# mapping.mapped.tau_memory ≈ 0.1 (from discount, inverted)
```

**SOD Priors**:
```python
from abraxas.sod.sim_adapter import convert_knobs_to_sod_priors

sod_priors = convert_knobs_to_sod_priors(mapping.mapped.to_dict())

# sod_priors["cascade_branching_prob"] ≈ 0.5
# sod_priors["cascade_damping_factor"] ≈ 0.6
# sod_priors["cascade_tail_length_hours"] ≈ 55.2
```

**SimVar Initialization**:
```python
VAR_MISINFO_STRATEGY = SimVarDefinition(
    var_id="misinformation_strategy_mix",
    prior_distribution=PriorDistribution(
        distribution_type="uniform",
        parameters={"min": 0.0, "max": 0.5},  # Max = MRI from paper
        sml_source={
            "paper_id": "ARXIV_SPATIAL_GAMES",
            "knob_mapping": "MRI from effort parameter",
            "confidence": "HIGH",
        },
    ),
    ...
)
```

**Rune Provenance**:
```python
RUNE_MEDIA_COMPETITION = RuneBinding(
    ...
    provenance_manifest=ProvenanceManifest(
        ...
        sml_training_sources=["ARXIV_SPATIAL_GAMES", "PMC10924450"],
    ),
)
```

**Query Traceability**:
```
Question: "What papers informed the misinformation_strategy_mix variable?"
Answer: ARXIV_SPATIAL_GAMES (see VAR.prior_distribution.sml_source.paper_id)

Question: "What was the MRI value used?"
Answer: 0.5 (see VAR.prior_distribution.parameters.max, derived from effort=5.0)
```

---

## Startup Validation Gate

**Module**: `abraxas/simulation/validation.py`

**Function**: `run_startup_gate(metric_registry, simvar_registry, rune_registry, sim_seed)`

**CRITICAL Checks** (block execution if failed):
1. `sim_seed` is provided (determinism requirement)
2. No orphan metrics (metrics without rune bindings)
3. No unbound variables (vars referenced but not defined)
4. Rune coupling integrity (all metric_id/var_id references valid)
5. Variable class/type/bounds validity

**WARNING Checks** (logged but don't block):
- Circular metric dependencies

**Raises**:
- `RuntimeError` if any CRITICAL errors found

**Usage**:
```python
from abraxas.simulation import run_startup_gate

errors = run_startup_gate(
    metric_registry,
    simvar_registry,
    rune_registry,
    sim_seed=42,
)

# If critical errors exist, RuntimeError is raised
# Otherwise, warnings (if any) are returned
```

---

## Add Metric Procedure

**Module**: `abraxas/simulation/add_metric.py`

**Class**: `MetricAdditionPipeline`

**Tests Run**:
1. **Required Fields**: All mandatory fields present and valid
2. **Determinism**: Rune configured for deterministic execution
3. **Bounds Safety**: All bounds valid (min < max)
4. **Coupling Sanity**: Metric-rune-variable coupling is consistent
5. **Game Operator Sanity**: (if game-theoretic metric) Strategy transitions valid
6. **Network Operator Sanity**: (if network metric) Network transitions valid

**Workflow**:
```python
from abraxas.simulation import MetricAdditionPipeline

pipeline = MetricAdditionPipeline(metric_registry, simvar_registry, rune_registry)

success = pipeline.add_metric(
    metric=METRIC_MEDIA_COMPETITION,
    variables=[VAR_PUBLIC_OPINION, VAR_SOCIAL_NETWORK, ...],
    rune=RUNE_MEDIA_COMPETITION,
)

if success:
    print(pipeline.get_test_report())
    # All registries saved automatically
else:
    print(pipeline.get_test_report())
    # Check errors and fix
```

**Semantic Versioning**:
```python
from abraxas.simulation import bump_semantic_version

new_version = bump_semantic_version("1.2.3", "minor")
# Returns "1.3.0"
```

**Version Bump Rules**:
- **MAJOR**: Breaking changes to metric definition or rune semantics
- **MINOR**: New variables added, new rune bindings, backward-compatible changes
- **PATCH**: Bug fixes, documentation updates, no semantic changes

---

## Exemplar Implementation

**File**: `abraxas/simulation/examples/media_competition_exemplar.py`

**Demonstrates**:
- Full metric definition (MEDIA_COMPETITION_MISINFO_PRESSURE)
- All variable classes:
  - `belief_state`: public_opinion_belief_state
  - `context_operator`: media_framing_context
  - `media_actor_state`: media_actor_credibility
  - `strategy_profile`: misinformation_strategy_mix
  - `network_state`: social_network_graph
  - `community_structure`: community_assignment (quantum-inspired QUBO)
  - `link_probability_field`: link_probability_field (quantum walk)
  - `conformity_pressure`: conformity_pressure_field
  - `state_over_time`: state_over_time_correlations
- Hybrid rune binding (quantum-inspired + classical)
- Outcome ledger entry with all required deltas
- SML training data integration (ARXIV_SPATIAL_GAMES)

**Run Example**:
```python
from abraxas.simulation.examples.media_competition_exemplar import (
    METRIC_MEDIA_COMPETITION,
    RUNE_MEDIA_COMPETITION,
    VAR_PUBLIC_OPINION,
    # ... all other variables
)

from abraxas.simulation import MetricRegistry, SimVarRegistry, RuneRegistry

metric_registry = MetricRegistry()
simvar_registry = SimVarRegistry()
rune_registry = RuneRegistry()

# Register all components
metric_registry.register(METRIC_MEDIA_COMPETITION)
for var in [VAR_PUBLIC_OPINION, VAR_SOCIAL_NETWORK, ...]:
    simvar_registry.register(var)
rune_registry.register(RUNE_MEDIA_COMPETITION)

# Validate
from abraxas.simulation import run_startup_gate

errors = run_startup_gate(
    metric_registry,
    simvar_registry,
    rune_registry,
    sim_seed=42,
)

print(f"Validation: {len(errors)} warnings")
# Simulation ready to run
```

---

## References

- Implementation: `abraxas/simulation/`
- JSON Schemas: `abraxas/simulation/schemas/`
- Registries: `abraxas/simulation/registries/`
- Validation: `abraxas/simulation/validation.py`
- Add Metric: `abraxas/simulation/add_metric.py`
- Exemplar: `abraxas/simulation/examples/media_competition_exemplar.py`
- SML Integration: `abraxas/sim_mappings/` + `abraxas/sod/sim_adapter.py`
- Tests: `tests/test_simulation_*.py` (to be added)
