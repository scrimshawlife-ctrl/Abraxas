# SCO Integration Guide

Complete integration of Python Symbolic Compression Stack with TypeScript/Node.js Abraxas ecosystem.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     ABRAXAS ECOSYSTEM                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │ TypeScript   │◄────────┤ Python       │                     │
│  │ Express API  │  bridge │ SCO/ECO      │                     │
│  │              │         │ CLI          │                     │
│  └──────┬───────┘         └──────────────┘                     │
│         │                                                       │
│         ├─► Weather Engine ─► Memetic Weather Reports          │
│         ├─► Oracle Pipeline ─► Daily Oracle                    │
│         └─► Event Storage   ─► AAlmanac Ledger                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Module Inventory

### Python Stack (Core Analysis)

```
abraxas/
├── operators/symbolic_compression.py  # SCO/ECO operator
├── linguistic/                         # Linguistic utilities
│   ├── phonetics.py                   # Soundex, phonetic keys
│   ├── similarity.py                  # Edit distance, IPS
│   ├── transparency.py                # STI calculation
│   └── rdv.py                         # Affect detection
├── pipelines/sco_pipeline.py          # Batch processing
├── storage/events.py                  # JSONL persistence
└── cli/sco_run.py                     # CLI interface
```

### TypeScript Integration Layer

```
server/abraxas/
├── integrations/sco-bridge.ts         # Python CLI bridge
├── pipelines/sco-analyzer.ts          # TS wrapper pipeline
├── routes/sco-routes.ts               # Express API endpoints
└── weather_engine/modules/
    └── sco-compression.ts             # Weather module
```

## Integration Points

### 1. Direct CLI Usage (Python)

```bash
# Analyze corpus for compression events
python -m abraxas.cli.sco_run \
  --records corpus/records.json \
  --lexicon corpus/lexicon.json \
  --out events/sco_output.jsonl \
  --domain music
```

**Input:** `records.json`
```json
[
  {"id": "1", "text": "I love Aphex Twins."},
  {"id": "2", "text": "Apex Twin is a legend."}
]
```

**Input:** `lexicon.json`
```json
[
  {"canonical": "aphex twin", "variants": ["aphex twins", "apex twin"]}
]
```

**Output:** `sco_output.jsonl` (one event per line)
```json
{
  "event_type": "SymbolicCompressionEvent",
  "tier": "ECO_T1",
  "original_token": "aphex twin",
  "replacement_token": "aphex twins",
  "phonetic_similarity": 0.95,
  "compression_pressure": 1.42,
  ...
}
```

### 2. TypeScript API (Express Routes)

```typescript
// POST /api/sco/analyze
const response = await fetch('/api/sco/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    texts: [
      "I love Aphex Twins.",
      "Apex Twin is a legend."
    ],
    domain: "music"
  })
});

const result = await response.json();
// result.events: SymbolicCompressionEvent[]
// result.signals: { compressionPressure, driftIntensity, rdvVector }
```

### 3. Weather Engine Integration

```typescript
// POST /api/sco/weather
const weatherResponse = await fetch('/api/sco/weather', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    texts: corpusTexts,
    domain: "slang"
  })
});

const weather = await weatherResponse.json();
// weather.weatherSignal: SCOCompressionSignal
// weather.narrative: markdown report
// weather.signals: WeatherEngineSignal[]
```

## Workflows

### Workflow 1: Daily Slang Scan

**Goal:** Detect symbolic drift in social media corpus, feed into Weather Engine

```typescript
// server/abraxas/tasks/daily-slang-scan.ts
import { analyzeSCO, scoToWeatherSignals } from "../pipelines/sco-analyzer";
import { computeSCOCompression } from "../weather_engine/modules/sco-compression";

export async function dailySlangScan() {
  // 1. Fetch recent social media posts
  const posts = await fetchRecentPosts(sources);
  const texts = posts.map(p => p.text);

  // 2. Run SCO analysis
  const result = await analyzeSCO({
    texts,
    domain: "slang",
  });

  // 3. Compute weather signal
  const weatherSignal = computeSCOCompression(result.events);

  // 4. Feed into Weather Engine
  const signals = scoToWeatherSignals(result);
  await ingestWeatherSignals(signals);

  // 5. Store events in AAlmanac
  await storeEvents(result.events);

  return {
    eventCount: result.events.length,
    compressionPressure: weatherSignal.pressure,
    forecast: weatherSignal.forecast,
  };
}
```

**Scheduled execution** (via ERS):
```typescript
// server/abraxas/integrations/task-registry.ts
export const slangScanTask: SymbolicTask = {
  id: "daily_slang_scan",
  name: "Daily Slang Compression Scan",
  executor: dailySlangScan,
  schedule: { type: "cron", pattern: "0 9 * * *" }, // 9am daily
  metadata: {
    domain: "slang",
    pipeline: "sco_slang_scan",
  },
};
```

### Workflow 2: Brand Monitoring

**Goal:** Track brand name compression/corruption in user-generated content

```typescript
// Track how "ethereum" becomes "etherium"
const brandResult = await analyzeSCO({
  texts: userReviews,
  domain: "crypto",
  customLexicon: [
    { canonical: "ethereum", variants: ["etherium", "etherum"] },
    { canonical: "bitcoin", variants: ["bitcon", "bit coin"] },
  ],
});

// Alert if compression pressure exceeds threshold
if (brandResult.signals.compressionPressure > 1.5) {
  await sendAlert({
    type: "brand_drift",
    pressure: brandResult.signals.compressionPressure,
    events: brandResult.events.length,
  });
}
```

### Workflow 3: Ritual Integration

**Goal:** Use SCO events as ritual modifiers

```typescript
import { getTodaysRunes } from "../../runes";
import { analyzeSCO } from "../pipelines/sco-analyzer";

export async function ritualisticSCOScan(texts: string[]) {
  // 1. Get today's runes
  const runes = getTodaysRunes();

  // 2. Run SCO analysis
  const scoResult = await analyzeSCO({ texts, domain: "general" });

  // 3. Modulate weights based on RDV
  const rdv = scoResult.signals.rdvVector;
  const runeModulation = {
    humor: rdv.humor * 0.1,
    aggression: -rdv.aggression * 0.15,
    authority: rdv.authority * 0.05,
  };

  // 4. Create ritual context
  const ritual = {
    seed: runes.seed,
    date: new Date().toISOString(),
    deltas: [
      {
        feature_map: ["astro_rul_align", "gematria_alignment"],
        delta: runeModulation.humor,
      },
    ],
    sco_provenance: scoResult.metadata.provenance,
  };

  return ritual;
}
```

## Weather Engine Signals

SCO events map to Weather Engine metrics:

| SCO Metric | Weather Metric | Interpretation |
|------------|----------------|----------------|
| `compression_pressure` | `symbolic_drift` | How strongly symbols are being replaced |
| `semantic_transparency_delta` | `transparency_flux` | Rate of semantic clarification/obscuration |
| `rdv.humor` | `rdv_humor` | Humorous affect in compression |
| `rdv.aggression` | `rdv_aggression` | Aggressive tonality |
| `rdv.authority` | `rdv_authority` | Authoritative framing |
| `rdv.intimacy` | `rdv_intimacy` | Communal resonance |
| `rdv.nihilism` | `rdv_nihilism` | Nihilistic drift |
| `rdv.irony` | `rdv_irony` | Ironic distancing |
| `tierDistribution.eco_t1` | `compression_stability` | Eggcorn formation rate |

## API Endpoints

### `POST /api/sco/analyze`
Run SCO analysis on text corpus.

**Request:**
```json
{
  "texts": ["text1", "text2"],
  "domain": "music|idiom|crypto|general",
  "customLexicon": [{"canonical": "...", "variants": ["..."]}]
}
```

**Response:**
```json
{
  "events": [SymbolicCompressionEvent],
  "signals": {
    "compressionPressure": 1.42,
    "driftIntensity": 0.22,
    "rdvVector": {...}
  },
  "metadata": {
    "provenance": "sha256...",
    "eventCount": 12
  }
}
```

### `POST /api/sco/weather`
Generate Weather Engine signals from SCO analysis.

**Response includes:**
- `weatherSignal`: Full SCO weather signal
- `narrative`: Human-readable markdown report
- `signals`: Array of Weather Engine signals

### `GET /api/sco/lexicons`
List available default lexicons.

### `GET /api/sco/health`
Health check endpoint.

## Registry Integration

**Modules registered in `.abraxas/registry.json`:**

```json
{
  "modules": {
    "abraxas/integrations/sco-bridge": {
      "path": "server/abraxas/integrations/sco-bridge.ts",
      "type": "integration-adapter",
      "exports": ["scoBridge", "detectCompressionEvents", "extractWeatherSignals"]
    },
    "abraxas/pipelines/sco-analyzer": {
      "path": "server/abraxas/pipelines/sco-analyzer.ts",
      "type": "oracle-pipeline",
      "exports": ["analyzeSCO", "batchAnalyzeSCO", "scoToWeatherSignals"]
    }
  },
  "pipelines": {
    "sco_slang_scan": {
      "steps": [
        "sco-analyzer.analyzeSCO",
        "sco-analyzer.scoToWeatherSignals",
        "weather-oracle.ingestSignals"
      ],
      "deterministic": true,
      "entropy_budget": 0.35
    }
  }
}
```

## Example: Full Stack Integration

```typescript
// server/index.ts or main app file
import { registerSCORoutes } from "./abraxas/routes/sco-routes";

// Register routes
registerSCORoutes(app);

// Example usage in another module
import { analyzeSCO } from "./abraxas/pipelines/sco-analyzer";
import { computeSCOCompression } from "./abraxas/weather_engine/modules/sco-compression";

async function analyzeUserFeedback(feedbackTexts: string[]) {
  // Run SCO
  const result = await analyzeSCO({
    texts: feedbackTexts,
    domain: "idiom",
  });

  // Get weather
  const weather = computeSCOCompression(result.events);

  console.log(`[SCO] Detected ${result.events.length} compression events`);
  console.log(`[SCO] Pressure: ${weather.pressure}`);
  console.log(`[SCO] Forecast: ${weather.forecast}`);

  return {
    events: result.events,
    weather,
  };
}
```

## Testing

```bash
# Test Python stack
pytest tests/

# Test TypeScript bridge (requires Python env)
npm test

# E2E test
curl -X POST http://localhost:5000/api/sco/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["I love Aphex Twins"],
    "domain": "music"
  }'
```

## Dependencies

### Python
- Python 3.11+
- No external packages (stdlib only)

### TypeScript
- Node.js 18+
- Express (already in project)
- Existing Abraxas modules

## Next Steps

1. **Add to ERS scheduler** - Register `slangScanTask` for automatic execution
2. **Create UI component** - React component to display SCO weather in dashboard
3. **Expand lexicons** - Build domain-specific compression lexicons
4. **Event storage** - Pipe events to PostgreSQL/AAlmanac ledger
5. **Real-time scanning** - WebSocket integration for live compression detection

## Provenance

All SCO events include SHA-256 provenance hashes ensuring:
- Deterministic detection logic
- Reproducible results
- Audit trail for drift analysis
- Version control for transparency lexicons
