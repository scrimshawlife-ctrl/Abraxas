<div align="center">

# 🜏 Abraxas

### Deterministic Symbolic Intelligence & Linguistic Weather System

*Provenance-embedded compression detection, memetic drift analysis, and self-healing infrastructure for edge deployment.*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Quick Start](#-quick-start) • [Architecture](#-architecture) • [Features](#-features) • [Documentation](#-documentation) • [Project Status](#-project-status)

> **AI assistants**: start with [`.github/AI_ASSISTANT_GUIDE.md`](.github/AI_ASSISTANT_GUIDE.md) and [`.github/QUICK_REFERENCE.md`](.github/QUICK_REFERENCE.md).

</div>

---

## 🎯 What is Abraxas?

**Abraxas** is a production-grade symbolic intelligence system that detects linguistic compression patterns, tracks memetic drift, and operates as an always-on edge appliance with self-healing capabilities. Think of it as a **weather system for language**—detecting symbol compression (eggcorns like “apex twin” → “aphex twin”), mapping affective drift, and generating deterministic provenance for every linguistic event.

### At a Glance

- **Deterministic by design** — every output is reproducible with SHA-256 provenance
- **Dual-lane architecture** — prediction and diagnostics stay strictly separated
- **Edge-ready** — optimized for Jetson Orin with systemd and atomic updates
- **Full-stack** — Python SCO/ECO core + TypeScript orchestration + UI tooling

### Core Capabilities

- **Symbolic Compression Detection (SCO/ECO)** — quantify when opaque symbols are replaced with semantically transparent substitutes
- **Weather Engine** — transform linguistic events into memetic weather patterns and drift signals
- **Scenario Envelope Runner (SER)** — deterministic forecasting with cascade sheets and contamination advisories
- **Governance Registry** — discover components, track rent-manifest coverage, and record approvals
- **Always-On Daemon** — continuous ingestion via Decodo API with chat-style interaction
- **Self-Healing Infrastructure** — drift detection, watchdog monitoring, atomic updates
- **Orin-Ready Edge Deployment** — Jetson Orin systemd integration
- **Provenance-First Design** — every event includes a SHA-256 hash for auditability
- **Anagram Sweep Engine (ASE)** — deterministic anagram mining for current-events feeds (Tier-1/2 + PFDI drift baseline)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- (Optional) NVIDIA Jetson Orin for edge deployment

### Installation

```bash
# Clone repository
git clone https://github.com/scrimshawlife-ctrl/Abraxas.git
cd Abraxas

# Install Python dependencies
pip install -e .

# Install LENS optional dependencies
pip install -e ".[lens]"

# Install Node.js dependencies
npm install

# Run system diagnostic
abx doctor

# Check optional deps for LENS
abx diag deps

# Overlay contract
cat docs/overlay_contract.md
```

### Run Your First Analysis

```bash
# Analyze text for symbolic compression
python -m abraxas.cli.sco_run \
  --records tests/records.json \
  --lexicon tests/lexicon.json \
  --out events.jsonl \
  --domain music

# Start the always-on daemon
abx ui

# Start continuous ingestion (requires Decodo credentials)
abx ingest
```

### Run ASE (Anagram Sweep Engine)

```bash
# Analyze a JSONL current-events feed for deterministic anagram signals
abraxas-ase run --in items.jsonl --out out/ase --date 2026-01-24 \
  --pfdi-state out_prev/ase/pfdi_state.json
```

Outputs:
- `out/ase/daily_report.json`
- `out/ase/ledger_append.jsonl`
- `out/ase/pfdi_state.json`

### ASE Lexicon Automation

```bash
# Regenerate lexicon artifacts from sources
python -m abraxas_ase.tools.lexicon_update --in lexicon_sources --out abraxas_ase

# CI check to ensure generated lexicon is up to date
python -m abraxas_ase.tools.lexicon_update --check --in lexicon_sources --out abraxas_ase
```

### Lexicon expansion loop

```bash
# Update candidate snapshot from daily report
python -m abraxas_ase.tools.candidate_update \
  --report out/ase/daily_report.json \
  --date 2026-01-24 \
  --candidates out/ase/candidates.jsonl \
  --out-metrics out/ase/candidate_decisions.json

# Promote lanes and update core list (dry run unless --apply)
python -m abraxas_ase.tools.promote_lanes \
  --candidates out/ase/candidates.jsonl \
  --lanes-dir lexicon_sources/lanes \
  --core-file lexicon_sources/subwords_core.txt \
  --apply
```

### Export packs

```bash
python -m abraxas_ase.tools.export_pack \
  --report out/ase/daily_report.json \
  --outdir out/ase/exports \
  --tier academic
```

### Chronoscope

```bash
python -m abraxas_ase.tools.chronoscope_update \
  --state out/ase/chronoscope_state.json \
  --input out/ase/exports/pack_enterprise \
  --tier enterprise \
  --rules default_rules/watchlist_rules.enterprise.json \
  --outdir out/ase/chronoscope
```

### Development Server

```bash
# Start TypeScript development server
npm run dev

# Run tests
npm test
pytest tests/
```

---

## 🏗️ Architecture

Abraxas is a **multi-layer stack** combining Python linguistic analysis with TypeScript orchestration and edge infrastructure.

### ABX-Runes Coupling Architecture

**Design constraint**: all cross-subsystem communication flows through ABX-Runes capability contracts.

```
┌──────────────────────────────────────────────────────────┐
│                  ABX Runtime Layer                       │
│                                                          │
│   ✅ Uses: abraxas.runes.capabilities                   │
│   ✅ invoke_capability("oracle.v2.run", inputs, ctx)    │
│   ❌ Never: from abraxas.oracle import run_oracle       │
└──────────────────┬───────────────────────────────────────┘
                   │
          ABX-Runes Capability Contract
          (JSON Schema + Provenance Envelope)
                   │
┌──────────────────▼───────────────────────────────────────┐
│              ABRAXAS Core Engine                         │
│                                                          │
│   Rune Adapters expose capabilities:                    │
│   • oracle.v2.run         - Oracle pipeline             │
│   • memetic.profiles      - Temporal analysis           │
│   • forecast.classify     - Forecast classification     │
│   • evidence.load         - Evidence bundles            │
│   • ... (20+ capabilities planned)                      │
└──────────────────────────────────────────────────────────┘
```

**Benefits:**
- **Determinism**: inputs/outputs validated against JSON schemas
- **Provenance**: every invocation tracked with SHA-256 hashes
- **Testability**: subsystems tested independently
- **Deployability**: supports multi-process architectures
- **Governance**: policy enforcement at the capability boundary

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ABRAXAS ECOSYSTEM                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  TypeScript/Express Layer (Node.js)                      │  │
│  │  • API Routes & Express Server                           │  │
│  │  • Weather Engine Integration                            │  │
│  │  • Chat UI & Admin Handshake                             │  │
│  │  • Task Registry & ERS Scheduling                        │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   │                                             │
│  ┌────────────────▼─────────────────────────────────────────┐  │
│  │  Python SCO/ECO Core                                     │  │
│  │  • Symbolic Compression Operator                         │  │
│  │  • Phonetic & Semantic Analysis                          │  │
│  │  • Transparency Index (STI) Calculation                  │  │
│  │  • Replacement Direction Vector (RDV)                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Orin Boot Spine (Edge Infrastructure)                   │  │
│  │  • Drift Detection & Health Monitoring                   │  │
│  │  • Overlay Lifecycle Management                          │  │
│  │  • Atomic Updates with Rollback                          │  │
│  │  • Systemd Integration                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Data Layer                                              │  │
│  │  • Decodo Web Scraping API Integration                  │  │
│  │  • SQLite Storage with Provenance                        │  │
│  │  • JSONL Event Persistence                               │  │
│  │  • AAlmanac Ledger                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **SCO/ECO Stack** | Python | Linguistic compression detection & analysis |
| **Weather Engine** | TypeScript | Memetic drift pattern generation |
| **Orin Spine** | Python | Edge deployment infrastructure |
| **Chat UI** | Express/React | Admin interface & module discovery |
| **Ingestion Engine** | Python | Continuous data acquisition via Decodo |
| **Self-Healing Layer** | Python/Systemd | Watchdog, drift detection, atomic updates |

---

## 🔀 Dual-Lane Architecture

**Critical design**: Abraxas enforces strict separation between prediction and diagnostics.

```
┌─────────────────────────────────────────────────────────────┐
│                  ABRAXAS DUAL-LANE SYSTEM                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PREDICTION LANE (Truth-Pure)      SHADOW LANE (Observe)   │
│  ════════════════════               ════════════════════    │
│                                                             │
│  ┌──────────────────┐             ┌──────────────────┐     │
│  │ Oracle Pipeline  │             │ Shadow Detectors │     │
│  │ Forecast Engine  │             │ • Compliance     │     │
│  │ SOD Operators    │             │ • Meta-Awareness │     │
│  │ DCE Compression  │             │ • Negative Space │     │
│  └────────┬─────────┘             └────────┬─────────┘     │
│           │                                │               │
│           │                                ▼               │
│           │                      ┌──────────────────┐      │
│           │                      │ Shadow Metrics   │      │
│           │                      │ SEI/CLIP/NOR/    │      │
│           │                      │ PTS/SCG/FVC      │      │
│           │                      └────────┬─────────┘      │
│           │                                │               │
│           │         ┌──────────────────────┘ evidence only │
│           │         │                                      │
│           ▼         ▼                                      │
│      ┌────────────────────────┐                           │
│      │   LANE GUARD (ϟ₇)      │ ◄── Promotion Ledger      │
│      │  ════════════════      │                           │
│      │  • Check PROMOTED flag │                           │
│      │  • Calibration only    │                           │
│      │  • NO ethical veto     │                           │
│      └────────┬───────────────┘                           │
│               │                                            │
│               ▼                                            │
│      ┌─────────────────┐                                  │
│      │ Forecast Output │                                  │
│      └─────────────────┘                                  │
│                                                            │
└─────────────────────────────────────────────────────────────┘
```

### Core Principles

1. **Prediction is morally agnostic**
   - Forecast accuracy is the only success metric
   - No ethical, risk, or diagnostic constraints on predictions
   - Full spectrum forecasting across all domains
   - Diagnostics never alter prediction

2. **Shadow lane is observe-only**
   - Computes diagnostic signals (manipulation markers, psychological load, etc.)
   - Attaches evidence as annotations only
   - Never influences prediction behavior

3. **Lane Guard enforces separation** (ABX-Runes ϟ₇)
   - Prevents shadow outputs from leaking into prediction
   - Requires explicit PROMOTION via governance system
   - Validates promotion criteria: calibration, stability, redundancy only

---

## ⚡ Features

### Symbolic Compression Detection

Detect when language users compress symbols while preserving intent.

- **ECO_T1 (Eggcorn)** — high phonetic similarity (≥0.85) + semantic transparency delta (≥0.18)
- **SCO_T2 (General Compression)** — moderate thresholds with provenance tracking
- **Metrics** — STI, CP, IPS, SLC, RDV with deterministic scoring

Example detected event:
```json
{
  "tier": "ECO_T1",
  "original_token": "aphex twin",
  "replacement_token": "apex twin",
  "compression_pressure": 1.42,
  "symbolic_transparency_index": 0.45,
  "rdv": {
    "humor": 0.0,
    "intimacy": 0.6,
    "irony": 0.0
  }
}
```

### Weather Engine Integration

Transform compression events into memetic weather patterns:

- **Symbolic Drift** — intensity of symbol replacement
- **Transparency Flux** — rate of semantic clarification/obscuration
- **RDV Tracking** — humor, aggression, authority, intimacy, nihilism, irony
- **Compression Stability** — eggcorn formation rate

### Lexicon Engine v1

Domain-scoped, versioned token-weight mapping with deterministic compression:

```python
from abraxas.lexicon import LexiconEngine, LexiconPack, LexiconEntry, InMemoryLexiconRegistry

# Create a lexicon pack
pack = LexiconPack(
    domain="slang",
    version="1.0.0",
    entries=(
        LexiconEntry("cap", 0.9, {"tag": "negation"}),
        LexiconEntry("no_cap", 1.1, {"tag": "assertion"}),
    ),
    created_at_utc="2025-12-20T00:00:00Z",
)

# Register and compress
registry = InMemoryLexiconRegistry()
engine = LexiconEngine(registry)
engine.register(pack)

result = engine.compress(
    "slang",
    ["cap", "no_cap", "unknown"],
    run_id="RUN-123"
)
# result.matched == ("cap", "no_cap")
# result.weights_out == {"cap": 0.9, "no_cap": 1.1}
# result.provenance.inputs_hash — SHA256 of inputs
```

### Oracle Pipeline v1

Deterministic daily oracle generation from correlation deltas:

```python
from datetime import date
from abraxas.oracle import DeterministicOracleRunner, OracleConfig, CorrelationDelta

runner = DeterministicOracleRunner(git_sha="abc123", host="prod-01")
config = OracleConfig(half_life_hours=24.0, top_k=10)

deltas = [
    CorrelationDelta("slang", "crypto", "diamond_hands", 1.5, "2025-12-20T12:00:00Z"),
    CorrelationDelta("idiom", "tech", "move_fast", 0.7, "2025-12-19T18:00:00Z"),
]

artifact = runner.run_for_date(date(2025, 12, 20), deltas, config)
# artifact.output — ranked signals with decay weighting
# artifact.signature — deterministic SHA256 signature
# artifact.provenance — full execution metadata
```

**Features:**
- **Deterministic signatures** — same inputs always produce same artifact signature
- **Time-weighted decay** — recent signals weighted higher with configurable half-life
- **Provenance-embedded** — every artifact includes inputs hash, config hash, git SHA
- **Modular design** — composable transforms: decay, score_deltas, render_oracle
- **Golden test coverage** — 26 tests including signature stability verification

### Oracle v2 Governance Layer

Additive compliance and mode routing on top of v1 scoring:

```python
from abraxas.oracle.v2.wire import build_v2_block

# v2 block automatically added to oracle output
v2 = build_v2_block(
    checks={
        "v1_golden_pass_rate": 1.0,
        "drift_budget_violations": 0,
        "evidence_bundle_overflow_rate": 0.0,
        "ci_volatility_correlation": 0.72,
        "interaction_noise_rate": 0.22,
    },
    router_input={
        "max_band_width": 42.0,
        "max_MRS": 85.0,
        "negative_signal_alerts": 0,
        "thresholds": {"BW_HIGH": 20.0, "MRS_HIGH": 70.0},
    },
    config_hash="...",
)
# v2 contains: compliance (RED/YELLOW/GREEN), mode_decision (SNAPSHOT/ANALYST/RITUAL)
```

**Features:**
- **Compliance reporting** — deterministic RED/YELLOW/GREEN status based on v1 regression checks
- **Mode routing** — priority-based selection: user override → compliance RED → high uncertainty/risk → default
- **Provenance lock** — stable fingerprint for mode decision reproducibility
- **Additive-only** — v1 outputs preserved; v2 block appended to `output["v2"]`
- **Golden tests** — 5 deterministic tests for compliance and router logic

### Always-On Daemon

Run Abraxas as a persistent service:

- **Continuous Ingestion** — scheduled scraping via Decodo API
- **Chat Interface** — LLM-like interaction with module discovery
- **Admin Handshake** — dynamic capability detection
- **SQLite Storage** — provenance-stamped document persistence

### Self-Healing Infrastructure

Production-grade reliability for edge deployment:

- **Drift Detection** — git SHA, config, assets, dependencies tracking
- **Watchdog** — automatic service restart on health check failures
- **Atomic Updates** — zero-downtime deployments with rollback
- **Systemd Integration** — managed lifecycle for Jetson Orin

---

## 📋 Project Status

### ✅ Completed

- **SCO/ECO Core** — full symbolic compression detection pipeline
- **Orin Boot Spine** — edge infrastructure scaffolding
- **TypeScript Integration** — Express API bridge to Python stack
- **Weather Engine** — signal transformation and narrative generation
- **Always-On Daemon** — ingestion engine and chat UI
- **Self-Healing Layer** — drift detection, watchdog, atomic updates
- **Systemd Services** — production deployment units
- **Lexicon Engine v1** — domain-scoped, versioned token-weight mapping
- **Oracle Pipeline v1** — deterministic oracle generation from correlation deltas
- **Abraxas v1.4** — temporal & adversarial expansion
- **ABX-Runes v1.4** — rune-sigil generation pipeline + operator system
- **SIG KPI Metrics** — Symbolic Intelligence Gain tracking (WO-66 through WO-81)
- **Kernel Phase System** — 5-phase execution model (OPEN/ALIGN/ASCEND/CLEAR/SEAL)
- **6-Gate Metric Governance** — anti-hallucination promotion framework
- **Simulation Mapping Layer** — 22 academic papers → Abraxas variable translation
- **WO-100 Acquisition Infrastructure** — anchor resolution, reupload detection, forecast accuracy
- **Shadow Structural Metrics** — observe-only analytical layer (SEI, CLIP, NOR, PTS, SCG, FVC)
- **Shadow Detectors v0.1** — compliance/remix, meta-awareness, negative space detectors
- **Dual-Lane Architecture + Lane Guard** — strict separation with ABX-Runes ϟ₇ enforcement
- **Abraxas v1.5** — Predictive Intelligence Layer (Q1 2025 critical path complete)
  - **Domain Compression Engines (DCE)** — lifecycle-aware, lineage-tracked compression
  - **Oracle Pipeline v2** — signal → compression → forecast → narrative assembly
  - **Phase Detection Engine** — cross-domain alignment, synchronicity, early warnings

### Abraxas v1.4: Temporal & Adversarial Expansion

#### τ (Tau) Operator: Temporal Metrics

- **τₕ (Tau Half-Life)**: symbolic persistence under declining reinforcement (hours)
- **τᵥ (Tau Velocity)**: emergence/decay slope from time-series (events/day)
- **τₚ (Tau Phase Proximity)**: distance to next lifecycle boundary [0,1]

```python
from abraxas.core.temporal_tau import TauCalculator, Observation

calculator = TauCalculator(git_sha="abc123")
snapshot = calculator.compute_snapshot(observations, run_id="RUN-001")

print(f"τₕ = {snapshot.tau_half_life:.2f} hours")
print(f"τᵥ = {snapshot.tau_velocity:.2f} events/day")
print(f"Confidence: {snapshot.confidence.value}")
```

#### D/M Layer: Information Integrity Metrics

Risk/likelihood estimators for information integrity assessment (not truth adjudication):

**Artifact Integrity**: PPS, PCS, MMS, SLS, EIS
**Narrative Manipulation**: FLS, EIL, OCS, RRS, MPS, CIS
**Network/Campaign**: CUS, SVS, BAS, MDS

**Composite Risk Indices**:
- **IRI** (Integrity Risk Index): [0,100]
- **MRI** (Manipulation Risk Index): [0,100]

```python
from abraxas.integrity import compute_composite_risk

risk = compute_composite_risk(artifact_integrity, narrative_manipulation, network_campaign)
print(f"IRI = {risk.iri:.1f}, MRI = {risk.mri:.1f}")
```

#### AAlmanac: Write-Once, Annotate-Only Ledger

Lifecycle state machine for symbolic evolution tracking:

**States**: Proto → Front → Saturated → Dormant → Archived

```python
from abraxas.slang.a_almanac_store import AAlmanacStore

store = AAlmanacStore()
term_id = store.create_entry_if_missing(term="cap", class_id="slang", ...)
state, tau = store.compute_current_state(term_id)
```

#### SOD (Second-Order Symbolic Dynamics)

Deterministic scaffolds for narrative cascade modeling:

- **NCP** (Narrative Cascade Predictor)
- **CNF** (Counter-Narrative Forecaster)
- **EFTE** (Epistemic Fatigue Threshold Engine)
- **SPM** (Susceptibility Profile Mapper)
- **RRM** (Recovery & Re-Stabilization Model)

```python
from abraxas.sod import NarrativeCascadePredictor, SODInput

ncp = NarrativeCascadePredictor(top_k=5)
envelope = ncp.predict(sod_input, run_id="RUN-001")
```

#### Artifact Generators

- **Cascade Sheet** — tabular summary of cascade paths
- **Manipulation Surface Map** — heatmap data for D/M metrics
- **Contamination Advisory** — high-risk artifact alerts
- **Trust Drift Graph Data** — time-series for τₕ and IRI/MRI
- **Oracle Delta Ledger** — diff between current and prior snapshots
- **Integrity Brief** — daily ledger health + delta summary

#### v1.4 CLI

```bash
python -m abraxas.cli.abx_run_v1_4 \
  --observations data/obs.json \
  --format both \
  --artifacts cascade_sheet,contamination_advisory \
  --output-dir data/runs/v1_4
```

**Features**:
- Delta-only mode (default): emits only changed fields
- JSON/Markdown dual output
- Deterministic provenance embedding
- Confidence bands (LOW/MED/HIGH)

**Documentation**:
- [v1.4 Specification](docs/specs/v1_4_temporal_adversarial.md)
- [SOD Specification](docs/specs/sod_second_order_dynamics.md)
- [Canonical Ledger](docs/canon/ABRAXAS_CANON_LEDGER.txt)

### Recent Updates (v1.5.0 — December 2025)

**Abraxas v1.5: Predictive Intelligence Layer** — transforms Abraxas from descriptive → **predictive**

#### Phase 1: Domain Compression Engines (DCE)
- Versioned lexicon framework with SHA-256 lineage tracking
- Domain-specific operators (politics, media, finance, conspiracy)
- Integration with STI/RDV/SCO pipeline
- Lifecycle-aware compression (proto → front → saturated → dormant → archived)
- **Files:** 3 modules, 1,162 lines

#### Phase 2: Oracle Pipeline v2
- Unified Signal → Compression → Forecast → Narrative assembly
- Real component integration (LifecycleEngine, TauCalculator, weather, resonance)
- 6-gate governance system (provenance, falsifiability, redundancy, rent, ablation, stabilization)
- Deterministic provenance bundles with SHA-256 tracking
- Governance layer with compliance reporting and deterministic mode routing (SNAPSHOT/ANALYST/RITUAL)
- **Files:** 3 modules + governance + example, 1,239 lines

#### Phase 3: Phase Detection Engine
- Cross-domain phase alignment detection (2+ domains in same phase)
- Synchronicity mapping (domain X → domain Y lag patterns)
- Early warning system for phase transitions
- Drift-resonance coupling detection (cascade risk assessment)
- **Files:** 4 modules, 991 lines

**Total Impact:** 12 files, 3,392 lines — Abraxas is now predictive.

#### Dual-Lane Architecture: Shadow Diagnostics + Truth-Pure Prediction

Abraxas implements a **dual-lane architecture** (see [Dual-Lane Architecture](#-dual-lane-architecture)):

1. **Shadow Lane (Observe-Only Diagnostics)**
   - Cambridge Analytica-derived metrics (SEI, CLIP, NOR, PTS, SCG, FVC)
   - Pattern detectors (compliance/remix, meta-awareness, negative space)
   - **Lane Guard enforcement** — prevents shadow signals from influencing prediction
   - **No system influence** — pure observation and measurement
   - ABX-Runes ϟ₇ access control (SSO - Shadow Structural Observer)
   - SEED compliant with SHA-256 provenance

2. **Prediction Lane (Truth-Pure Forecasting)**
   - Domain Compression Engines (DCE)
   - Oracle Pipeline v2 with 6-gate governance
   - Phase Detection Engine
   - **Morally agnostic** — forecast accuracy is the only success metric
   - **Active forecasting** — generates predictions and narratives

**Philosophy**: Shadow lane describes what is happening psychologically; prediction lane forecasts what comes next symbolically. Lane Guard ensures they never interfere. See `docs/specs/dual_lane_architecture.md` for full specification.

---

## 🧭 TVM Oracle Skeleton + Influence/Synchronicity (Canonical)

**Canonical flow (shadow-only by default):**
Sources → Metrics (Shadow) → **TVM Vector Framing (V1–V15)** → **ABX-INFLUENCE_DETECT (ICS)** → **ABX-INFLUENCE_WEIGHT** → **ABX-SYNCHRONICITY_MAP (SE)** → MDA Domain Graph → Oracle Output

**Non-exclusionary intake**: symbolic domains (astrology, numerology, geomagnetic, Schumann, etc.) are accepted when structured inputs exist; no domain legitimacy priors are allowed.

**Seed baseline**: deterministic 2025 year-in-review seed packs provide historical substrate for influence/synchronicity calibration.

```bash
abraxas seed --year 2025 --out data/year_seed/2025/seedpack.v0.1.json
```

---

## 📊 Latest Updates (December 2025)

### PR #51 — Dual-Lane Architecture with Shadow Detectors + Lane Guard (2025-12-30)

**Critical implementation**: separates prediction (truth-pure) from diagnostics (observe-only).

- **Shadow Detectors v0.1** (`abraxas/detectors/shadow/`)
  - Compliance vs Remix detector — lexical overlap vs novel recombination
  - Meta-Awareness detector — algorithmic/manipulation discourse patterns
  - Negative Space detector — topic dropout and visibility asymmetry
  - Deterministic registry with SHA-256 provenance

- **Lane Guard** (`abraxas/detectors/shadow/lane_guard.py`)
  - Enforces prediction/shadow separation (ABX-Runes ϟ₇)
  - Rejects promotions based on ethical/risk/diagnostic criteria
  - Allows calibration/stability/redundancy criteria only
  - Promotion ledger with hash-chain verification

- **Tests**: 28 tests passing (18 detector tests + 10 lane guard tests)
- **Documentation**: `docs/specs/dual_lane_architecture.md`

**Design guarantees**:
- Prediction is morally agnostic (never blocked by ethical signals)
- Shadow outputs are observe-only annotations
- Lane Guard prevents shadow leakage into forecast
- Promotion requires evidence: calibration + stability + redundancy
- Full SHA-256 provenance tracking

**Non-negotiable**: diagnostics never alter prediction.

### v1.4.1 Updates (Merged December 2025)

**4 major PRs** — governance, acquisition, and infrastructure consolidation:

1. **PR #22** — 6-Gate Metric Governance System
2. **PR #28** — WO-100: Acquisition & Analysis Infrastructure
3. **PR #20** — Kernel Phase System
4. **PR #36** — Documentation enhancements

**Total:** 120 files changed, 15,654 additions, 466 deletions

**Latest merged pull requests:**
- **#29** — Codex: Conduct Repo Topology Scan and Indexing
- **#27** — Add SIG KPI Metrics (Symbolic Intelligence Gain)
- **#26** — Implement Canonical Daily Run Orchestrator
- **#25** — Implement Metric Target Binding for Portfolios
- **#24** — Rent Enforcement v0.1
- **#23** — Resolve PR Conflicts
- **#21** — Abraxas Update Agent
- **#19** — Emergent Metrics Shadow System
- **#18** — Abraxas v1.4 Implementation

**Recent work orders (WO-66 through WO-100):**
- **WO-100**: Acquisition & Analysis Infrastructure (anchor resolution, reupload detection, forecast accuracy)
- **WO-81**: Attribution Hardening
- **WO-80**: Delta Scoring + Self-Calibration
- **WO-79**: Anchor→Claim Relation Classifier
- **WO-78**: Online Resolver Operator
- **WO-77.1**: Tiered Online Sourcing with Provider Fallbacks
- **WO-77**: Execution Adapter + Task Ledger
- **WO-76**: Acquisition Planner from Stability Deficits
- **WO-75**: Time-to-Truth (TTT) Curves + Claim Stabilization Half-Life
- **WO-73**: Two-Axis Truth Contamination Map
- **WO-72**: Evidence Graph + Claim Support/Contradiction Metrics
- **WO-71**: Anchor-Level Evidence Ledger + Proof Integrity Score
- **WO-70**: Anti-Goodhart Guardrails + Confidence Bands + Regime-Shift Detector
- **WO-69**: SIG Snapshot Ledger + Proper Outcome Attribution
- **WO-68**: Task Outcome Ledger + Learned ROI Weights
- **WO-67**: Signal ROI Scheduler for economic task selection
- **WO-66**: SIG KPI (Symbolic Intelligence Gain) metrics system

### ✅ Q1 2025 Critical Path — Complete

> See [ROADMAP.md](ROADMAP.md) for the canon-aligned priority stack.

1. **Domain Compression Engines (DCEs)** — versioned, lifecycle-tracked lexicons
   - Status: **Core Spine** ✓
   - Provides: foundation for Oracle v2, Phase Detection, Multi-Domain Analysis

2. **Oracle Pipeline v2** — unified Signal → Compression → Forecast → Narrative
   - Status: **Operational** ✓
   - Integrates: LifecycleEngine, TauCalculator, weather, resonance, 6-gate governance

3. **Phase Detection Engine** — cross-domain phase alignment + synchronicity
   - Status: **Operational** ✓
   - Capabilities: alignment detection, synchronicity mapping, early warnings, cascade risk
   - **Abraxas is now predictive** ✓

### 🚀 Next — High-Value Extensions (Q2 2025)

4. **Resonance Narratives** — human-readable output layer
5. **UI Dashboard** — delayed until Oracle v2 artifacts stabilize

### ⏳ Later — Infrastructure & Scale (Q3–Q4 2025)

- PostgreSQL migration (when artifact volume demands it)
- WebSocket integration (for real-time phase-based systems)
- Mobile UI (surface area only, minimal epistemic value)
- Ritual System (symbolic modulation, locked behind Oracle v2)
- Multi-Domain Analysis — crypto, idiom, slang, technical jargon
- Event Correlation — cross-domain drift pattern detection

**Prioritization philosophy:** epistemic leverage over engineering familiarity.

---

## 📖 Documentation

### Core Modules

- **[CLAUDE.md](CLAUDE.md)** — AI assistant development guide
- **[Dual-Lane Architecture](docs/specs/dual_lane_architecture.md)** — prediction vs shadow lane separation
- **[SCO Stack](README_SCO.md)** — Symbolic Compression Operator documentation
- **[Orin Spine](README_ORIN.md)** — edge deployment and infrastructure
- **[Integration Guide](INTEGRATION_SCO.md)** — TypeScript/Python integration
- **[Deployment Guide](DEPLOYMENT_SCO.md)** — production deployment
- **[Conflict Resolution Guide](CONFLICT_RESOLUTION_GUIDE.md)** — merge conflict strategies

### CLI Reference

```bash
# Orin commands
abx doctor          # System diagnostics
abx up              # Start HTTP server
abx smoke           # Run deterministic smoke test
abx assets sync     # Generate asset manifest
abx overlay list    # List installed overlays
abx drift check     # Check for configuration drift
abx watchdog        # Start health monitoring
abx update          # Atomic update with rollback
abx ingest          # Start data ingestion
abx ui              # Start chat UI server
abx admin           # Print admin handshake JSON

# SCO analysis
python -m abraxas.cli.sco_run --records <file> --lexicon <file> --out <file>

# Resonance Narratives
abx resonance-narrative --envelope <file> --out <file> --previous <file>
```

### API Endpoints

```bash
# Health checks
GET  /healthz              # Liveness
GET  /readyz               # Readiness with provenance

# SCO analysis
POST /api/sco/analyze      # Run compression detection
POST /api/sco/weather      # Generate weather signals
GET  /api/sco/lexicons     # List available lexicons

# Chat UI
GET  /admin/handshake      # Discover modules
POST /chat                 # Send messages
GET  /data/latest          # Inspect ingested data
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ABX_ROOT` | `/opt/aal/abraxas` | Root installation directory |
| `ABX_PROFILE` | `orin` | Runtime profile (orin/dev) |
| `ABX_PORT` | `8765` | HTTP server port |
| `ABX_UI_PORT` | `8780` | Chat UI port |
| `ABX_DB` | `.aal/state/abx.sqlite` | SQLite database path |
| `DECODO_AUTH_B64` | (required) | Decodo API credentials |

### Systemd Services

For production deployment on Jetson Orin:

```bash
# Core services
sudo systemctl enable abraxas-core
sudo systemctl enable abx-ingest
sudo systemctl enable abx-ui
sudo systemctl enable abx-watchdog
sudo systemctl enable abx-update.timer

# Check status
sudo systemctl status abraxas-core abx-ingest abx-ui
```

---

## 🧪 Testing

```bash
# Python tests
pytest tests/

# TypeScript tests
npm test
npm run test:coverage

# Smoke test (deterministic)
abx smoke

# Acceptance suite (writes artifacts to out/acceptance/)
python tools/acceptance/run_acceptance_suite.py

# Seal release validation (writes artifacts to artifacts_seal/ and artifacts_gate/)
python -m scripts.seal_release --run_id seal --tick 0 --runs 12

# Runtime infrastructure tests (policy snapshots, retention, concurrency)
pytest tests/test_runtime_infrastructure.py

# E2E test
curl -X POST http://localhost:5000/api/sco/analyze \
  -H "Content-Type: application/json" \
  -d '{"texts": ["I love Aphex Twins"], "domain": "music"}'
```

---

## 🤝 Contributing

Contributions welcome. Abraxas is deterministic and provenance-first:

1. All changes must pass `abx smoke` deterministic tests
2. Include SHA-256 provenance for new linguistic events
3. Maintain backward compatibility for API endpoints
4. Follow existing code style (TypeScript/Python)
5. Network installs are forbidden; PyYAML is vendored (do not pip/apt install)

---

## 📄 License

MIT License — see [LICENSE](LICENSE).

---

## 🔗 Links

- **GitHub**: [scrimshawlife-ctrl/Abraxas](https://github.com/scrimshawlife-ctrl/Abraxas)
- **Issues**: [Report bugs or request features](https://github.com/scrimshawlife-ctrl/Abraxas/issues)
- **Decodo API**: [Web Scraping API](https://decodo.com)

---

<div align="center">

**Built for deterministic symbolic intelligence at the edge**

*Abraxas • Where language becomes weather*

</div>
