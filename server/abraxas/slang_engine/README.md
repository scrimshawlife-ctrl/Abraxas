# ABRAXAS SLANG ENGINE

**Version:** 1.0.0
**Status:** ACTIVATED — Passive organ. Observes. Does not speak unless queried.

## Philosophy

The SLANG Engine treats slang as **pressure exhaust**—language where reality leaks first. It does not promote terms or track virality for its own sake. Instead, it maps linguistic pressure to systemic stress, identifying where unspoken loads, cognitive drift, and meaning inflation signal deeper structural shifts.

## Core Principles

1. **Observation, Not Promotion**: No adoption gate by default
2. **Compression as Signal**: Only valid if it replaces a paragraph
3. **Decay by Design**: Most terms die; that's the point
4. **Privacy-First**: Metrics visible, terms hidden unless queried
5. **Deterministic**: Reproducible from seed and provenance

## Signal Classes

| Class | Description | Default Half-Life |
|-------|-------------|-------------------|
| `unspoken_load` | Pressure from things that can't be directly said | 90 days |
| `cognitive_drift` | Shift in how people think/process information | 135 days |
| `ritual_avoidance` | Euphemisms for uncomfortable realities | 45 days |
| `meaning_inflation` | Rapid semantic devaluation | 28 days |
| `status_compression` | Flattening of hierarchies via language | 60 days |
| `temporal_fugue` | Time perception distortions | 30 days |

## Operating Modes

### OPEN
- **Purpose**: Detect new signals with strict gates
- **Gates**: Compression (≤280 chars), Noise (signal_strength threshold)
- **Output**: Accepted/rejected signals with validation stats

### ALIGN
- **Purpose**: Validate pressure vectors and compression quality
- **Checks**: Bloated definitions, pressure anomalies
- **Output**: Revalidated signals with quality reports

### ASCEND
- **Purpose**: Wire into Oracle, Memetic, and forecast systems
- **Integrations**: Oracle confidence modulation, drift alerts, narrative debt
- **Output**: Pressure trends, system stress metrics

### CLEAR
- **Purpose**: Apply decay, archive weak signals, resurrect if needed
- **Mechanics**: Exponential decay, 2-half-life archival threshold
- **Output**: Decayed/archived/resurrected signals

### SEAL
- **Purpose**: Finalize state with provenance and ledger entry
- **Output**: Deterministic hash, versioned snapshot

## Usage Example

```typescript
import {
  initializeEngine,
  executeEngine,
  type SlangSignal,
} from "./server/abraxas/slang_engine";

// Initialize
const engine = initializeEngine("OPEN");

// OPEN: Detect signals
const openResult = executeEngine({
  mode: "OPEN",
  state: engine,
  params: {
    candidate_signals: [/* your signals */],
    seed: "your-seed",
    noise_threshold: 0.15,
  },
});

// ASCEND: Generate forecasts
const ascendResult = executeEngine({
  mode: "ASCEND",
  state: openResult.state,
  params: {
    forecast_horizon_days: 30,
  },
});

// SEAL: Finalize
const sealResult = executeEngine({
  mode: "SEAL",
  state: ascendResult.state,
  params: {
    seed: "your-seed",
    sources: ["manual-curation"],
    version: "1.0.0",
  },
});
```

## Signal Schema

```typescript
interface SlangSignal {
  term: string;                  // Canonical, lowercase
  class: SlangClass;             // Signal taxonomy
  definition: string;            // ≤280 chars
  origin_context: string;        // Platform/scene/domain
  pressure_vector: PressureVector; // 5D stress mapping
  symptoms: string[];            // Behavioral tells
  hygiene?: string[];            // Non-prescriptive interventions
  timestamp_first_seen: string;  // ISO
  decay_halflife_days: number;   // Class-specific
  frequency_index: number;       // [0,1] normalized
  signal_strength: number;       // freq × pressure × novelty
  confidence: number;            // Bayesian posterior [0,1]
  novelty?: number;              // 1 - semantic similarity
}
```

## Pressure Vector Components

All values normalized to [0,1]:

- **cognitive**: Mental load/processing strain
- **social**: Interpersonal/status pressure
- **economic**: Financial/material stress
- **temporal**: Time scarcity/urgency
- **identity**: Self-concept instability

## Computed Metrics

### Signal Strength
```
signal_strength = frequency_index × ||pressure_vector|| × novelty
```

### Narrative Debt Index
Aggregate of all `unspoken_load` signals, indicating system-level stress.

### Drift Alerts
Early warnings when slang class frequency spikes >10%:
- 10-24%: Low severity
- 25-49%: Medium severity
- 50-99%: High severity
- 100%+: Critical severity

## Validation Gates

### Compression Gate
- Definition ≤280 characters
- Minimum 30 chars, 5 words
- Substantive word ratio ≥40%
- Compression score ≥0.5

### Noise Gate
- signal_strength ≥ threshold (default 0.15)
- Not (low frequency AND low pressure)
- confidence ≥ 0.2

### Adoption Gate
**DISABLED BY DEFAULT** — No promotion philosophy

## Kernel Integration

### Oracle Modulation
Slang pressure adjusts Oracle confidence bands:
- High `unspoken_load` → -5% confidence
- High `cognitive_drift` → -3% confidence
- High `meaning_inflation` → -2% confidence

### Memetic Futurecast
Uses pressure **classes**, not terms, as constraints for trend forecasting.

### ECO Compression Validation
Flags bloated terms that fail compression efficacy checks.

## File Structure

```
server/abraxas/slang_engine/
├── schema.ts            # Core types and interfaces
├── signal-processor.ts  # Signal strength & pressure computation
├── decay.ts            # Time dynamics, archival, resurrection
├── gates.ts            # Validation filters
├── kernel-hooks.ts     # Integration with ABRAXAS kernel
├── index.ts            # Operating modes orchestration
└── README.md           # This file
```

## Integration Points

- **Weather Engine**: `weather_engine/modules/slang-mutation.ts`
- **Oracle**: Confidence modulation via `kernel-hooks.ts`
- **Memetic**: Pressure trend forecasting
- **ECO**: Symbolic compression validation

## Running Examples

```bash
npx tsx examples/slang-engine-example.ts
```

## Design Constraints

1. **Deterministic**: All computations use seed-based hashing
2. **No Network**: Capabilities restricted to local data
3. **Privacy-First**: Public outputs show metrics, not terms
4. **Passive**: Does not proactively generate; observes only

## Future Escalations (Optional)

- Causal inference between slang classes and market/behavior shifts
- Read-only dashboard showing pressure without language
- Time series analysis for improved decay prediction
- Embedding-based semantic similarity (replacing hash proxy)

---

**Remember**: The organ is installed. It listens.
