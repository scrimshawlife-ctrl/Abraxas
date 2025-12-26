# Simulation Mapping Layer (SML) Specification

**Version**: 1.0
**Status**: Production
**Compatibility**: Abraxas v1.4+

---

## Overview

The Simulation Mapping Layer (SML) provides a deterministic bridge between academic simulation model parameters and Abraxas operational knobs (MRI, IRI, τ). This enables future integration of academic models without modifying core Abraxas infrastructure.

SML is a **parameter bridge**, not a simulation engine. It translates published model parameters into Abraxas-compatible metrics for scenario generation.

---

## Mapping Philosophy

### MRI (Manipulation Risk Index) Mapping

**Push/Spread/Amplification Parameters**:
- Transmission rates (β, contact rates)
- Influence weights (w_ij, homophily)
- Sharing probabilities
- Bot density / algorithmic boost
- Network degree / bridge density
- External forcing (media fields, advertising)

**Principle**: Higher values = stronger propagation = higher MRI

### IRI (Integrity Risk Index) Mapping

**Damping/Redirect/Defense Parameters**:
- Recovery/forgetting rates (γ, deactivation)
- Skeptic compartments / immune populations
- Bounded confidence (ε, stubbornness)
- Correction effectiveness
- Sanctions / moderation removal
- Defensive modifiers / trust dynamics

**Principle**: Higher values = stronger resistance = higher IRI

### τ (Temporal Dynamics) Mapping

**Timing/Memory Parameters**:
- **τ_latency**: Delays, incubation periods, inter-layer lags, propagation windows
- **τ_memory**: Memory kernels, argument depth, content lifespan, discount factors

**Principle**: Temporal structure affects cascade onset and persistence

---

## Model Families

### DIFFUSION_SIR (SIR/SEIR Compartment Models)

**MRI Parameters**:
- `beta` (β): Transmission rate per contact
- `c2`, `ads`: External boost/advertising
- `k`: Network degree (higher = more contacts)
- `mixing`: Mixing parameter (higher = less structure)

**IRI Parameters**:
- `gamma` (γ): Recovery/forgetting rate
- `skeptic_rate`: Skeptic compartment transition
- `immune_rate`: Immune compartment transition
- `defensive_mod`: Defensive modifiers reducing β

**τ Parameters**:
- `delay`, `incubation`: Incubation/exposure delay
- `inter_layer_lag`: Multi-layer model lag
- `memory_kernel`: Non-Markovian memory

**Key Params for Evidence**: beta, gamma, k, delay

---

### OPINION_DYNAMICS (Voter, DeGroot, Bounded Confidence)

**MRI Parameters**:
- `w`, `w_ij`: Influence weight (higher = stronger influence)
- `homophily`: Homophily parameter (higher = echo chambers)
- `media_field`: Mass media field strength

**IRI Parameters**:
- `epsilon` (ε): Bounded confidence (lower = more selective)
- `stubbornness`: Zealot/stubborn parameter
- `repulsion`: Negative influence

**τ Parameters**:
- `update_schedule`: Update timing parameter
- `alpha` (α): Inertia/relaxation (lower = faster updates)
- `memory_depth`: Argument memory depth

**Key Params for Evidence**: w, epsilon, alpha, update_schedule

---

### ABM_MISINFO (Agent-Based Misinformation Models)

**MRI Parameters**:
- `share_prob`: Sharing probability
- `bot_density`: Bot density
- `bot_activity`: Bot activity rate
- `algo_boost`: Algorithmic amplification

**IRI Parameters**:
- `correction_eff`: Correction effectiveness
- `sanction`: Sanction parameter
- `downrank`: Downranking parameter
- `trust_adaptive`: Adaptive trust dynamics

**τ Parameters**:
- `inter_event_time`: Time between events
- `exposure_action_delay`: Delay between exposure and action
- `content_lifespan`: Content memory/lifespan

**Key Params for Evidence**: share_prob, bot_density, correction_eff, content_lifespan

---

### NETWORK_CASCADES (Threshold/Cascade Models)

**MRI Parameters**:
- `p`, `p_ij`: Edge activation probability
- `threshold`: Adoption threshold (**INVERTED**: lower = higher MRI)
- `bridge_density`: Bridge density

**IRI Parameters**:
- `deactivation_rate`: Deactivation/recovery rate
- `robustness`: Network robustness
- `redundancy`: Redundancy parameter
- `moderation_removal`: Moderation removal rate

**τ Parameters**:
- `delay`, `propagation_delay`: Propagation delay
- `temporal_window`: Temporal window parameter

**Key Params for Evidence**: p, threshold, deactivation_rate, delay

---

### GAME_THEORETIC (Evolutionary Game Theory, Inspection Games)

**MRI Parameters**:
- `effort`: Propagandist effort/investment
- `payoff_reach`: Payoff reach incentive
- `selection_strength`: Selection strength (higher = faster spread)

**IRI Parameters**:
- `sanction_prob` (p_C): Sanction probability
- `sanction_penalty`: Sanction penalty cost
- `defender_budget`: Defender budget

**τ Parameters**:
- `update_schedule`: Update schedule parameter
- `observation_horizon`: Observation horizon
- `discount`: Discount factor (lower = shorter horizon)
- `campaign_horizon`: Campaign time horizon

**Key Params for Evidence**: effort, sanction_prob, sanction_penalty, discount

---

## Confidence Scoring

Confidence is based on **evidence completeness**:

- **HIGH**: ≥80% key params present, all numeric
- **MED**: 40-79% key params present
- **LOW**: <40% key params present

**Key params** are family-specific (see above).

---

## Normalization Strategies

### minmax_clip
Linear normalization to [0,1] given [min, max]:
```
normalized = (x - min) / (max - min), clamped to [0,1]
```

### logistic_clip
Sigmoid-like normalization:
```
normalized = 1 / (1 + exp(-k * (x - x0)))
```
- k: steepness parameter
- x0: midpoint

### piecewise_bucket
Threshold-based bucketing for discrete levels.

---

## Default Parameter Ranges

Conservative defaults used when paper doesn't specify:

| Parameter | Range | Units |
|-----------|-------|-------|
| beta (β) | [0.0, 1.0] | per contact |
| gamma (γ) | [0.0, 1.0] | rate |
| k (degree) | [1.0, 50.0] | count |
| delay | [0.0, 14.0] | days |
| w (influence) | [0.0, 1.0] | weight |
| epsilon (ε) | [0.0, 1.0] | threshold |
| share_prob | [0.0, 1.0] | probability |
| bot_density | [0.0, 0.5] | fraction |
| p (activation) | [0.0, 1.0] | probability |
| threshold | [0.0, 1.0] | threshold |
| effort | [0.0, 10.0] | units |
| discount | [0.0, 1.0] | factor |

---

## Paper Registry

SML maintains a canonical registry of academic papers at `data/sim_sources/papers.json`.

**Registry Structure**:
```json
{
  "papers": [
    {
      "paper_id": "PMC12281847",
      "title": "A discrete SIR epidemic model incorporating media impact",
      "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC12281847/",
      "year": null,
      "notes": "SIR model with media impact (c2 parameter)"
    }
  ],
  "count": 21,
  "metadata": {
    "last_updated": "2025-12-26",
    "notes": "..."
  }
}
```

**Registry Functions**:
```python
from abraxas.sim_mappings.registry import (
    load_paper_refs,      # Load all papers
    get_paper_ref,        # Get specific paper by ID
    list_papers,          # List papers with summary info
    find_by_keyword,      # Search by keyword in title/notes
)

# Example: Find all SIR-related papers
sir_papers = find_by_keyword("SIR")
```

---

## Paper Mapping Table

The mapping table (`data/sim_sources/paper_mapping_table.csv`) provides qualitative parameter scaffolds for all registered papers.

**CSV Format**:
```csv
paper_id,model_family,mri_params,iri_params,tau_params,notes
PMC12281847,DIFFUSION_SIR,beta; c2,gamma,delay; incubation,SIR with media impact
```

**Parameter Lists**: Semicolon-delimited parameter names (no numeric values)

**Usage**:
```python
from abraxas.sim_mappings.importers import import_mappings_from_csv

# Load all mapping scaffolds
mappings = import_mappings_from_csv("data/sim_sources/paper_mapping_table.csv")

# Each MappingResult has:
#   - paper: PaperRef (from registry)
#   - family: ModelFamily
#   - input_params: List[ModelParam] (names only, no values)
#   - mapped: KnobVector (stub with LOW confidence, all zeros)
```

**Paper Parameter Example Stubs**: Located in `data/sim_sources/examples/{paper_id}.json`

---

## Multi-Paper Aggregation

SML supports aggregating multiple papers into a single set of SOD priors using confidence-weighted averaging.

**Confidence Weights**:
- HIGH: 1.0
- MED: 0.75
- LOW: 0.5

**Usage**:
```python
from abraxas.sod.sim_adapter import aggregate_multi_paper_priors
from abraxas.sim_mappings import map_paper_model

# Map multiple papers
mapping1 = map_paper_model(paper1, family1, params1)
mapping2 = map_paper_model(paper2, family2, params2)

# Aggregate into single SOD priors
aggregated_priors = aggregate_multi_paper_priors([mapping1, mapping2])

# Result includes:
#   - All standard SOD priors
#   - aggregated_knobs: Weighted mean knobs
#   - sources: List of paper IDs
#   - weights: Per-paper confidence weights
#   - total_papers: Number of papers aggregated
#   - aggregate_confidence: Maximum confidence level
```

---

## SOD Integration

SML outputs (`KnobVector`) can be converted to SOD-compatible priors via `abraxas.sod.sim_adapter`:

```python
from abraxas.sim_mappings import map_params_to_knobs
from abraxas.sod.sim_adapter import convert_knobs_to_sod_priors

# Map params to knobs
knobs = map_params_to_knobs(family, params)

# Convert to SOD priors
sod_priors = convert_knobs_to_sod_priors(knobs.to_dict())

# Use in SOD scenario generation
# sod_priors contains:
#   - cascade_branching_prob
#   - cascade_damping_factor
#   - cascade_onset_lag_hours
#   - cascade_tail_length_hours
#   - max_cascade_depth
```

---

## Usage Examples

### Example 1: DIFFUSION_SIR Model

```python
from abraxas.sim_mappings import (
    ModelFamily,
    ModelParam,
    PaperRef,
    map_paper_model,
)

# Define paper
paper = PaperRef(
    paper_id="PMC12281847",
    title="SIR Model for Misinformation",
    url="https://example.com",
    year=2024,
)

# Define parameters
params = [
    ModelParam(name="beta", symbol="β", value=0.3, units="per day"),
    ModelParam(name="gamma", symbol="γ", value=0.1, units="per day"),
    ModelParam(name="k", value=10.0, description="Network degree"),
    ModelParam(name="delay", value=2.0, units="days"),
]

# Map to knobs
result = map_paper_model(paper, ModelFamily.DIFFUSION_SIR, params)

print(f"MRI: {result.mapped.mri:.2f}")
print(f"IRI: {result.mapped.iri:.2f}")
print(f"τ_latency: {result.mapped.tau_latency:.2f}")
print(f"τ_memory: {result.mapped.tau_memory:.2f}")
print(f"Confidence: {result.mapped.confidence}")
print(f"Explanation: {result.mapped.explanation}")
```

### Example 2: CLI Usage

```bash
# Map parameters from command line
abx sim-map \
  --family DIFFUSION_SIR \
  --params beta=0.3 gamma=0.1 k=10 delay=2 \
  --paper_id PMC12281847 \
  --save

# Output JSON to stdout and save to data/sim_sources/mappings/
```

---

## Deterministic Guarantees

- **No randomness**: All normalizations are deterministic
- **No external APIs**: Pure local computation
- **No ML models**: Rule-based normalization only
- **Stable outputs**: Same inputs always produce same KnobVector
- **Provenance**: All params include provenance field for tracking

---

## Future Extensions

- Automatic parameter extraction from PDFs using LLM-based parsing
- Machine learning calibration based on real-world observations
- Real-time simulation execution (currently only scaffolding/priors)
- Dynamic parameter tuning based on feedback loops
- Network topology extraction from academic figures

---

## References

- Implementation: `abraxas/sim_mappings/`
- SOD Adapter: `abraxas/sod/sim_adapter.py` (includes multi-paper aggregation)
- Paper Registry: `data/sim_sources/papers.json`
- Paper Mapping Table: `data/sim_sources/paper_mapping_table.csv`
- Example Stubs: `data/sim_sources/examples/{paper_id}.json`
- CSV Importer: `abraxas/sim_mappings/importers.py`
- CLI Tool: `abraxas/cli/sim_map.py`
- Tests: `tests/test_sim_mappings_*.py`
