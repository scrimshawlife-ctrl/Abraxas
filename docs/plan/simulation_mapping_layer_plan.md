# Simulation Mapping Layer (SML) Implementation Plan

## Overview

The Simulation Mapping Layer (SML) provides a deterministic bridge between academic simulation model parameters and Abraxas operational knobs (MRI, IRI, τ). This enables future integration of academic models without modifying core Abraxas infrastructure.

## Design Philosophy

**MRI (Manipulation Risk Index) Mapping**:
- Push/spread parameters: transmission rates, influence weights, sharing probabilities
- Amplification mechanisms: bot density, algorithmic boost, bridge density
- Contact intensification: homophily, network degree, media fields

**IRI (Integrity Risk Index) Mapping**:
- Damping/redirect parameters: recovery rates, skeptic compartments, bounded confidence
- Defensive mechanisms: correction effectiveness, sanctions, adaptive trust
- Robustness factors: redundancy, moderation, deactivation rates

**τ (Temporal Dynamics) Mapping**:
- Timing parameters: incubation delays, inter-layer lags, propagation windows
- Memory parameters: non-Markovian kernels, argument-memory depth, content lifespan
- Update schedules: inertia, relaxation, observation horizons

## Integration with v1.4

SML is designed to be compatible with existing v1.4 architecture:

- **Consumes**: No Abraxas data structures (standalone)
- **Produces**: KnobVector compatible with SOD inputs
- **Connects to**: abraxas/sod/sim_adapter.py for scenario generation

## New Modules

### abraxas/sim_mappings/
- `types.py` - Typed dataclasses for papers, models, params, knobs
- `normalizers.py` - Deterministic normalization functions
- `family_maps.py` - Family-specific mapping rules
- `mapper.py` - Core mapping logic
- `registry.py` - Paper reference registry

### abraxas/sod/sim_adapter.py
- Converts KnobVector to SOD-compatible priors
- Pure function module (no SOD imports if not present)

## Data Storage

- `data/sim_sources/papers.json` - Known paper references
- `data/sim_sources/examples/*.json` - Example mappings (optional)
- `data/sim_sources/mappings/` - Saved mapping results (CLI output)

## Model Families Supported

1. **DIFFUSION_SIR**: SIR/SEIR models with compartments
2. **OPINION_DYNAMICS**: Voter models, DeGroot, bounded confidence
3. **ABM_MISINFO**: Agent-based misinformation models
4. **NETWORK_CASCADES**: Threshold/cascade models
5. **GAME_THEORETIC**: Evolutionary game theory, inspection games

## Mapping Rules (Family-Level)

### DIFFUSION_SIR
- **MRI**: β (transmission), c2/ads (external boost), k (degree), mixing
- **IRI**: γ (recovery), skeptic rates, defensive modifiers
- **τ**: incubation delays, inter-layer lag, memory kernels

### OPINION_DYNAMICS
- **MRI**: w_ij (influence weights), homophily, media field
- **IRI**: ε (bounded confidence), stubbornness, repulsion
- **τ**: update schedule, inertia α, memory depth

### ABM_MISINFO
- **MRI**: share probability, bot density, algorithmic boost
- **IRI**: correction effectiveness, sanctions, trust dynamics
- **τ**: inter-event times, exposure-action delays, content lifespan

### NETWORK_CASCADES
- **MRI**: p_ij (activation prob), thresholds (lower = higher MRI), bridges
- **IRI**: deactivation, robustness, moderation removal
- **τ**: temporal windows, propagation delays

### GAME_THEORETIC
- **MRI**: propagandist effort, payoff reach, selection strength
- **IRI**: sanction density p_C, penalties, defender budgets
- **τ**: update schedule, observation horizon, discount factors

## Deterministic Guarantees

- No random number generation
- No external API calls
- No ML models (only rule-based normalization)
- Confidence based on evidence completeness:
  - HIGH: ≥80% key params present, all numeric
  - MED: 40-79% key params present
  - LOW: <40% key params present

## Normalization Strategies

- **minmax_clip**: x normalized to [0,1] given [min, max]
- **logistic_clip**: sigmoid-like mapping with k (steepness) and x0 (midpoint)
- **piecewise_bucket**: threshold-based bucketing

All normalizers are deterministic with conservative defaults.

## Testing Strategy

- Golden tests for each model family
- Tiny synthetic fixtures (no real paper data in tests)
- Confidence degradation tests (remove params, verify confidence drops)
- Explanation tests (verify param citations in output)

## CLI Integration

Non-breaking CLI command:

```bash
abx sim-map \
  --family DIFFUSION_SIR \
  --params beta=0.3 gamma=0.1 delay=2 k=8 \
  --paper_id PMC12281847 \
  --save
```

## Files NOT Modified

- Existing v1.4 modules (temporal_tau, integrity, sod)
- Existing CLI commands
- Existing tests

## Success Criteria

- All tests pass with golden outputs
- CLI produces stable JSON
- KnobVector integrates with SOD adapter
- Documentation includes mapping table template
- No breaking changes to v1.4

## Future Extensions (Out of Scope)

- Automatic parameter extraction from PDFs
- Machine learning calibration
- Real-time simulation execution
- Multi-paper fusion
