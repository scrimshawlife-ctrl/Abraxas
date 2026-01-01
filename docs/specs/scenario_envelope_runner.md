# Scenario Envelope Runner (SER)

## Purpose

The Scenario Envelope Runner provides **deterministic scenario forecasting** driven by simulation priors, without requiring a full simulation engine.

SER bridges the gap between:
- Academic paper evidence (via paper registry + mapping table)
- Simulation parameter knobs (MRI, IRI, tau_memory, tau_latency)
- Operational forecasts (cascade sheets, contamination advisories)

## Architecture

```
Papers → Mapping Table → Sim Priors → Envelopes → SOD Bundle → Artifacts
```

### Flow

1. **Input**: Base simulation priors (MRI, IRI, tau_memory, tau_latency)
2. **Envelope Generation**: Create 4 deterministic variants (baseline, high_MRI, high_IRI, long_tau)
3. **SOD Execution**: Run NCP/CNF/EFTE for each envelope (optional; graceful fallback)
4. **Artifact Export**: Generate cascade sheets + contamination advisories
5. **Delta Tracking**: Compare to previous run; write only if changed

### Components

```
abraxas/scenario/
├── types.py          # ScenarioInput, ScenarioEnvelope, ScenarioRunResult
├── envelopes.py      # Deterministic envelope generator
├── runner.py         # Scenario orchestrator
└── __init__.py

abraxas/sod/
└── runner.py         # SOD bundle adapter (NCP+CNF+EFTE with try/except guards)

abraxas/artifacts/
├── scenario_cascade_sheet.py
└── scenario_contamination_advisory.py

abraxas/cli/
└── scenario_run.py   # CLI command
```

## Envelopes

SER generates **4 standard envelopes** from base priors:

### 1. Baseline
- **Modulation**: None (as-is priors)
- **Purpose**: Reference scenario
- **Falsifiers**:
  - Observed spread diverges significantly from baseline MRI
  - Damping dynamics violate baseline IRI assumptions

### 2. Push Spread Up
- **Modulation**: MRI +0.15 (clipped to [0,1])
- **Purpose**: Test high memetic resonance scenario
- **Falsifiers**:
  - Phrase rigidity (MDS) increases while spread stays flat
  - Cross-cluster correlations decrease despite high MRI

### 3. Damping Up
- **Modulation**: IRI +0.15 (clipped to [0,1])
- **Purpose**: Test high intervention responsiveness
- **Falsifiers**:
  - Intervention response time lengthens despite high IRI
  - Counter-narrative effectiveness shows no improvement

### 4. Memory Long
- **Modulation**: tau_memory +0.20, tau_latency +0.10 (clipped)
- **Purpose**: Test extended temporal dynamics
- **Falsifiers**:
  - Narrative persistence decays faster than tau_memory predicts
  - Latency effects disappear earlier than tau_latency window

## Confidence Levels

Confidence is computed **deterministically**:

- **HIGH**: All 4 knobs present (MRI, IRI, tau_memory, tau_latency) AND 2+ source papers
- **MED**: All 4 knobs present but only 1 source paper
- **LOW**: Otherwise (missing knobs or no source papers)

## Artifacts

### Cascade Sheet

**Purpose**: Summarize top cascade paths per envelope

**Contents**:
- Top 3 paths per envelope (from NCP output)
- Trigger descriptions
- Probability scores
- Duration estimates
- Confidence bands
- Falsifiers per envelope
- Provenance block

**Formats**: JSON, Markdown

### Contamination Advisory

**Purpose**: Report saturation and risk indices

**Contents**:
- **SSI (Synthetic Saturation Index)**:
  - If SLS present: SSI = clamp(SLS, 0, 1)
  - Else: Derived from evidence completeness (low evidence → low SSI, not high)
- **MRI/IRI** (scaled to 0-100 if available)
- **Skepticism Mode Guidance** by tier:
  - **Psychonaut**: Plain language, no moralizing
  - **Analyst**: Method notes, determinism emphasis
  - **Enterprise**: Risk timing, operational guidance

**Formats**: JSON, Markdown

## CLI Usage

```bash
# Basic run with defaults
python -m abraxas.cli.scenario_run

# Specify papers (future: loads from registry)
python -m abraxas.cli.scenario_run --paper_ids PMC12281847,PMC10250073

# Override simulation priors
python -m abraxas.cli.scenario_run \
  --mri 0.65 \
  --iri 0.70 \
  --tau_latency 0.4 \
  --tau_memory 0.6

# Output formats
python -m abraxas.cli.scenario_run --format json
python -m abraxas.cli.scenario_run --format md
python -m abraxas.cli.scenario_run --format both  # default

# Delta-only mode (skip write if unchanged)
python -m abraxas.cli.scenario_run --delta_only true  # default
python -m abraxas.cli.scenario_run --delta_only false

# Contamination advisory tier
python -m abraxas.cli.scenario_run --tier analyst

# Focus on specific cluster (cascade sheet)
python -m abraxas.cli.scenario_run --focus_cluster "crypto_discourse"
```

## Output Structure

```
out/scenarios/<run_id>/
├── scenario_result.json
├── cascade_sheet.json
├── cascade_sheet.md
├── contamination_advisory.json
└── contamination_advisory.md

data/runs/
└── last_scenario_snapshot.json  # For delta comparison
```

## Integration with Simulation Engine (Future)

Currently, SER uses a **stub adapter** for SOD modules (NCP/CNF/EFTE). When a full simulation engine is available:

**Replace in `abraxas/scenario/runner.py`:**

```python
# Current (stub)
result = run_scenarios(
    base_priors=priors,
    sod_runner=run_sod_bundle,  # Stub adapter
    context=context
)

# Future (with sim engine)
from my_sim_engine import run_simulation

result = run_scenarios(
    base_priors=priors,
    sod_runner=lambda ctx, priors: run_simulation(ctx, priors, full_mode=True),
    context=context
)
```

The `sod_runner` callable is the **only integration point**. All other components remain unchanged.

## Determinism Guarantees

- **No randomness**: All envelope variants are pre-specified
- **Stable ordering**: Envelopes always generated in same order
- **Canonical serialization**: JSON output uses `sort_keys=True`
- **Hash-based diffing**: Delta detection via deterministic hashing
- **Reproducible**: Same inputs → same outputs (given same SOD modules)

## Non-Breaking Design

- **Optional imports**: SOD runner uses try/except guards
- **Graceful fallback**: Missing modules return empty but well-formed structures
- **No modifications** to existing SOD modules (NCP, CNF, EFTE)
- **Additive only**: New package (`abraxas/scenario/`) + new artifacts

## Example Workflow

```python
from abraxas.scenario import run_scenarios
from abraxas.sod.runner import run_sod_bundle

# Define base priors
base_priors = {
    "MRI": 0.6,
    "IRI": 0.55,
    "tau_memory": 0.5,
    "tau_latency": 0.3,
}

# Build context
context = {
    "run_id": "scenario_20250101_120000",
    "source_count": 2,
    "weather": None,
    "dm_snapshot": None,
}

# Run scenarios
result = run_scenarios(
    base_priors=base_priors,
    sod_runner=run_sod_bundle,
    context=context,
)

# Access envelopes
for envelope in result.envelopes:
    print(f"Envelope: {envelope.label}")
    print(f"Confidence: {envelope.confidence}")
    print(f"Paths: {len(envelope.outputs.get('ncp', {}).get('paths', []))}")
```

## Testing

All tests use **golden outputs** for determinism verification:

```bash
# Run scenario tests
pytest tests/test_scenario_envelopes.py
pytest tests/test_scenario_runner_determinism.py
pytest tests/test_artifact_scenario_cascade_sheet.py
pytest tests/test_artifact_contamination_advisory.py
```

Golden files:
```
tests/golden/scenario/
├── envelopes_baseline.json
├── scenario_result.json
├── cascade_sheet.json
├── cascade_sheet.md
├── contamination_advisory.json
└── contamination_advisory.md
```

## Compliance

- **SEED**: Deterministic, provenance tracking, entropy minimization
- **ABX-Core**: Modular, typed (dataclasses), golden tests
- **No network calls**: All operations local

## Future Extensions

1. **Paper Registry Integration**: Auto-load priors from registry + mapping table
2. **Weather Engine Integration**: Pull current weather snapshot
3. **D/M Metrics Integration**: Pull demand/manipulation snapshots
4. **Almanac Integration**: Historical context
5. **Full Simulation Engine**: Replace stub adapter with real sim primitives
6. **Multi-Cluster Analysis**: Extend focus_cluster to multi-cluster mode
7. **Threshold Tuning**: Configurable envelope deltas (currently hardcoded)
