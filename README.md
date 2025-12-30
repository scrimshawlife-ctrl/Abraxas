<div align="center">

# 🜏 Abraxas

### Deterministic Symbolic Intelligence & Linguistic Weather System

*Provenance-embedded compression detection, memetic drift analysis, and self-healing infrastructure for edge deployment*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Quick Start](#-quick-start) • [Architecture](#-architecture) • [Features](#-features) • [Documentation](#-documentation) • [AI Assistant Guide](.github/AI_ASSISTANT_GUIDE.md) • [Project Status](#-project-status)

> **For AI Assistants (ChatGPT, Claude, etc.)**: See [`.github/AI_ASSISTANT_GUIDE.md`](.github/AI_ASSISTANT_GUIDE.md) for quick orientation and [`.github/QUICK_REFERENCE.md`](.github/QUICK_REFERENCE.md) for ultra-condensed reference.

</div>

---

## 🎯 What is Abraxas?

**Abraxas** is a production-grade symbolic intelligence system that detects linguistic compression patterns, tracks memetic drift, and operates as an always-on edge appliance with self-healing capabilities.

Think of it as a **weather system for language** — detecting when symbols compress ("eggcorns" like "apex twin" → "aphex twin"), tracking affective drift, and generating deterministic provenance for every linguistic event.

### Core Capabilities

- **🔬 Symbolic Compression Detection (SCO/ECO)** — Detect and quantify when opaque symbols are replaced with semantically transparent substitutes
- **🌦️ Weather Engine** — Transform linguistic events into memetic weather patterns and drift signals
- **📊 Scenario Envelope Runner (SER)** — Deterministic forecasting driven by simulation priors; generates cascade sheets and contamination advisories without requiring full simulation
- **🤖 Always-On Daemon** — Continuous data ingestion via Decodo API with chat-like interaction interface
- **🛡️ Self-Healing Infrastructure** — Drift detection, watchdog monitoring, and atomic updates with rollback
- **⚡ Orin-Ready Edge Deployment** — Optimized for NVIDIA Jetson Orin with systemd integration
- **🔒 Provenance-First Design** — Every event includes SHA-256 hash for reproducibility and auditability

---

## 🚀 Quick Start

### Prerequisites

```bash
# System requirements
- Python 3.11+
- Node.js 18+
- (Optional) NVIDIA Jetson Orin for edge deployment
```

### Installation

```bash
# Clone repository
git clone https://github.com/scrimshawlife-ctrl/Abraxas.git
cd Abraxas

# Install Python dependencies
pip install -e .

# Install Node.js dependencies
npm install

# Run system diagnostic
abx doctor
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

Abraxas operates as a **multi-layer stack** combining Python linguistic analysis with TypeScript orchestration:

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

**CRITICAL DESIGN**: Abraxas implements a **dual-lane architecture** that enforces strict separation between prediction and diagnostics:

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

1. **Prediction is Morally Agnostic**
   - Forecast accuracy is the ONLY success metric
   - No ethical, risk, or diagnostic constraints on predictions
   - Full spectrum forecasting across all domains
   - **NON-NEGOTIABLE**: Diagnostics never alter prediction

2. **Shadow Lane is Observe-Only**
   - Computes diagnostic signals (manipulation markers, psychological load, etc.)
   - Attaches evidence as **annotations only**
   - **NEVER** influences prediction behavior
   - Exists to inform human operators, not constrain forecasts

3. **Lane Guard Enforces Separation** (ABX-Runes ϟ₇)
   - Prevents shadow outputs from leaking into prediction
   - Requires explicit PROMOTION via governance system
   - Validates promotion criteria: **calibration, stability, redundancy ONLY**
   - **REJECTS** promotion based on ethical/risk/diagnostic criteria

This design ensures **high-fidelity forecasting** and **rich diagnostic capabilities** without compromise.

---

## ⚡ Features

### Symbolic Compression Detection

Detect when language users compress symbols while preserving intent:

- **ECO_T1 (Eggcorn)** — High phonetic similarity (≥0.85) + semantic transparency delta (≥0.18)
- **SCO_T2 (General Compression)** — Moderate thresholds with provenance tracking
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

- **Symbolic Drift** — Intensity of symbol replacement
- **Transparency Flux** — Rate of semantic clarification/obscuration
- **RDV Tracking** — Humor, aggression, authority, intimacy, nihilism, irony
- **Compression Stability** — Eggcorn formation rate

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
- **Deterministic signatures** — Same inputs always produce same artifact signature
- **Time-weighted decay** — Recent signals weighted higher with configurable half-life
- **Provenance-embedded** — Every artifact includes inputs hash, config hash, git SHA
- **Modular design** — Composable transforms: decay, score_deltas, render_oracle
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
        "max_band_width": 15.0,
        "max_MRS": 85.0,
        "negative_signal_alerts": 0,
        "thresholds": {"BW_HIGH": 20.0, "MRS_HIGH": 70.0},
    },
    config_hash="...",
)
# v2 contains: compliance (RED/YELLOW/GREEN), mode_decision (SNAPSHOT/ANALYST/RITUAL)
```

**Features:**
- **Compliance reporting** — Deterministic RED/YELLOW/GREEN status based on v1 regression checks
- **Mode routing** — Priority-based selection: user override → compliance RED → high uncertainty/risk → default
- **Provenance lock** — Stable fingerprint for mode decision reproducibility
- **Additive-only** — v1 outputs preserved; v2 block appended to `output["v2"]`
- **Golden tests** — 5 deterministic tests for compliance and router logic

### Always-On Daemon

Run Abraxas as a persistent service:

- **Continuous Ingestion** — Scheduled scraping via Decodo API
- **Chat Interface** — LLM-like interaction with module discovery
- **Admin Handshake** — Dynamic capability detection
- **SQLite Storage** — Provenance-stamped document persistence

### Self-Healing Infrastructure

Production-grade reliability for edge deployment:

- **Drift Detection** — Git SHA, config, assets, dependencies tracking
- **Watchdog** — Automatic service restart on health check failures
- **Atomic Updates** — Zero-downtime deployments with rollback
- **Systemd Integration** — Managed lifecycle for Jetson Orin

---

## 📋 Project Status

### ✅ Completed

- [x] **SCO/ECO Core** — Full symbolic compression detection pipeline
- [x] **Orin Boot Spine** — Edge infrastructure scaffolding
- [x] **TypeScript Integration** — Express API bridge to Python stack
- [x] **Weather Engine** — Signal transformation and narrative generation
- [x] **Always-On Daemon** — Ingestion engine and chat UI
- [x] **Self-Healing Layer** — Drift detection, watchdog, atomic updates
- [x] **Systemd Services** — Production deployment units
- [x] **Lexicon Engine v1** — Domain-scoped, versioned token-weight mapping
- [x] **Oracle Pipeline v1** — Deterministic oracle generation from correlation deltas
- [x] **Abraxas v1.4** — Temporal & Adversarial Expansion
- [x] **ABX-Runes v1.4** — Comprehensive rune-sigil generation pipeline + operator system
- [x] **SIG KPI Metrics** — Symbolic Intelligence Gain tracking (WO-66 through WO-81)
- [x] **CLAUDE.md** — Comprehensive AI assistant development guide
- [x] **Kernel Phase System** — 5-phase execution model (OPEN/ALIGN/ASCEND/CLEAR/SEAL)
- [x] **6-Gate Metric Governance** — Anti-hallucination promotion framework
- [x] **Simulation Mapping Layer** — 22 academic papers → Abraxas variable translation
- [x] **WO-100 Acquisition Infrastructure** — Anchor resolution, reupload detection, forecast accuracy
- [x] **Shadow Structural Metrics** — Cambridge Analytica-derived observe-only analytical layer (SEI, CLIP, NOR, PTS, SCG, FVC)
- [x] **Shadow Detectors v0.1** — Pattern detectors for compliance/remix, meta-awareness, negative space
- [x] **Dual-Lane Architecture + Lane Guard** — Strict separation between prediction (truth-pure) and shadow (observe-only) with ABX-Runes ϟ₇ enforcement
- [x] **Abraxas v1.5** — Predictive Intelligence Layer (**Q1 2025 Critical Path Complete**)
  - [x] **Domain Compression Engines (DCE)** — Lifecycle-aware, lineage-tracked compression
  - [x] **Oracle Pipeline v2** — Signal → Compression → Forecast → Narrative assembly
  - [x] **Phase Detection Engine** — Cross-domain alignment, synchronicity, early warnings

### Abraxas v1.4: Temporal & Adversarial Expansion

**Version 1.4.0** introduces three foundational layers for temporal dynamics, adversarial resilience, and second-order narrative modeling:

#### τ (Tau) Operator: Temporal Metrics

Three complementary temporal metrics for symbolic lifecycle tracking:

- **τₕ (Tau Half-Life)**: Symbolic persistence under declining reinforcement (hours)
- **τᵥ (Tau Velocity)**: Emergence/decay slope from time-series (events/day)
- **τₚ (Tau Phase Proximity)**: Distance to next lifecycle boundary [0,1]

```python
from abraxas.core.temporal_tau import TauCalculator, Observation

calculator = TauCalculator(git_sha="abc123")
snapshot = calculator.compute_snapshot(observations, run_id="RUN-001")

print(f"τₕ = {snapshot.tau_half_life:.2f} hours")
print(f"τᵥ = {snapshot.tau_velocity:.2f} events/day")
print(f"Confidence: {snapshot.confidence.value}")
```

#### D/M Layer: Information Integrity Metrics

Risk/likelihood estimators for information integrity assessment (NOT truth adjudication):

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

- **NCP** (Narrative Cascade Predictor): Predicts cascade scenarios
- **CNF** (Counter-Narrative Forecaster): Generates counter-strategies
- **EFTE** (Epistemic Fatigue Threshold Engine): Models declining engagement
- **SPM** (Susceptibility Profile Mapper): Maps susceptibility profiles
- **RRM** (Recovery & Re-Stabilization Model): Models recovery trajectories

```python
from abraxas.sod import NarrativeCascadePredictor, SODInput

ncp = NarrativeCascadePredictor(top_k=5)
envelope = ncp.predict(sod_input, run_id="RUN-001")
```

#### Artifact Generators

Five specialized output formats:

- **Cascade Sheet**: Tabular summary of cascade paths
- **Manipulation Surface Map**: Heatmap data for D/M metrics
- **Contamination Advisory**: High-risk artifact alerts
- **Trust Drift Graph Data**: Time-series for τₕ and IRI/MRI
- **Oracle Delta Ledger**: Diff between current and prior snapshots

#### v1.4 CLI

```bash
python -m abraxas.cli.abx_run_v1_4 \
  --observations data/obs.json \
  --format both \
  --artifacts cascade_sheet,contamination_advisory \
  --output-dir data/runs/v1_4
```

**Features**:
- Delta-only mode (default): Emits only changed fields
- JSON/Markdown dual output
- Deterministic provenance embedding
- Confidence bands (LOW/MED/HIGH)

**Documentation**:
- [v1.4 Specification](docs/specs/v1_4_temporal_adversarial.md)
- [SOD Specification](docs/specs/sod_second_order_dynamics.md)
- [Canonical Ledger](docs/canon/ABRAXAS_CANON_LEDGER.txt)

### 📊 Recent Updates (v1.5.0 — December 2025)

**Abraxas v1.5: Predictive Intelligence Layer** — Critical path completion transforms Abraxas from descriptive → **predictive**

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

**Total Impact:** 12 files, 3,392 lines, **Abraxas is now predictive**

#### Dual-Lane Architecture: Shadow Diagnostics + Truth-Pure Prediction

Abraxas implements a **dual-lane architecture** (see [Dual-Lane Architecture](#-dual-lane-architecture) section) with strict lane separation:

1. **Shadow Lane (Observe-Only Diagnostics)**:
   - Observe-only Cambridge Analytica-derived metrics (SEI, CLIP, NOR, PTS, SCG, FVC)
   - Pattern detectors (compliance/remix, meta-awareness, negative space)
   - **Lane Guard enforcement** — prevents shadow signals from influencing prediction
   - **No system influence** — pure observation and measurement
   - ABX-Runes ϟ₇ access control (SSO - Shadow Structural Observer)
   - SEED compliant with SHA-256 provenance

2. **Prediction Lane (Truth-Pure Forecasting)**:
   - Domain Compression Engines (DCE)
   - Oracle Pipeline v2 with 6-gate governance
   - Phase Detection Engine
   - **Morally agnostic** — forecast accuracy is the ONLY success metric
   - **Active forecasting** — generates predictions and narratives

**Philosophy**: Shadow lane describes *what is happening psychologically*, prediction lane forecasts *what comes next symbolically*. Lane Guard ensures these never interfere. See `docs/specs/dual_lane_architecture.md` for full specification.

---

### 📊 Latest Updates (December 2025)

#### PR #51 — Dual-Lane Architecture with Shadow Detectors + Lane Guard (2025-12-30)

**CRITICAL IMPLEMENTATION**: Separates prediction (truth-pure) from diagnostics (observe-only)

- **Shadow Detectors v0.1** (`abraxas/detectors/shadow/`):
  - Compliance vs Remix detector — lexical overlap vs novel recombination
  - Meta-Awareness detector — algorithmic/manipulation discourse patterns
  - Negative Space detector — topic dropout and visibility asymmetry
  - Deterministic registry with SHA-256 provenance

- **Lane Guard** (`abraxas/detectors/shadow/lane_guard.py`):
  - Enforces prediction/shadow separation (ABX-Runes ϟ₇)
  - REJECTS promotions based on ethical/risk/diagnostic criteria
  - ONLY allows calibration/stability/redundancy criteria
  - Promotion ledger with hash-chain verification

- **Tests**: 28 tests passing (18 detector tests + 10 lane guard tests)
- **Documentation**: `docs/specs/dual_lane_architecture.md`

**Design Guarantees**:
- Prediction is morally agnostic (NEVER blocked by ethical signals)
- Shadow outputs are observe-only annotations
- Lane Guard prevents shadow leakage into forecast
- Promotion requires evidence: calibration + stability + redundancy
- Full SHA-256 provenance tracking

**NON-NEGOTIABLE**: Diagnostics never alter prediction.

---

### 📊 v1.4.1 Updates (Merged December 2025)

**4 Major PRs** — Governance, acquisition, and infrastructure consolidation:

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
- **WO-100**: Acquisition & Analysis Infrastructure (Anchor resolution, reupload detection, forecast accuracy)
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

### ✅ Q1 2025 Critical Path — COMPLETE

> **See [ROADMAP.md](ROADMAP.md) for full canon-aligned priority stack**

**All critical path items completed** — Abraxas has transitioned from **descriptive → predictive**

1. ✅ **Domain Compression Engines (DCEs)** — Versioned, lifecycle-tracked lexicons
   - Status: **CORE SPINE** ✓
   - Provides: Foundation for Oracle v2, Phase Detection, Multi-Domain Analysis

2. ✅ **Oracle Pipeline v2** — Unified Signal → Compression → Forecast → Narrative
   - Status: **OPERATIONAL** ✓
   - Integrates: LifecycleEngine, TauCalculator, weather, resonance, 6-gate governance

3. ✅ **Phase Detection Engine** — Cross-domain phase alignment + synchronicity
   - Status: **OPERATIONAL** ✓
   - Capabilities: Alignment detection, synchronicity mapping, early warnings, cascade risk
   - **Abraxas is now predictive, not descriptive** ✓

### 🚀 NEXT — High-Value Extensions (Q2 2025)

4. **Resonance Narratives** — Human-readable output layer
5. **UI Dashboard** (delayed until Oracle v2 artifacts stabilize)

### ⏳ LATER — Infrastructure & Scale (Q3-Q4 2025)

- PostgreSQL Migration (when artifact volume demands it)
- WebSocket Integration (when phase-based system needs real-time)
- Mobile UI (pure surface area, minimal epistemic value)
- Ritual System (symbolic modulation—locked behind Oracle v2)
- Multi-Domain Analysis — Crypto, idiom, slang, technical jargon
- Event Correlation — Cross-domain drift pattern detection

**Prioritization Philosophy:** Epistemic leverage over engineering familiarity

---

## 📖 Documentation

### Core Modules

- **[CLAUDE.md](CLAUDE.md)** — AI Assistant Development Guide (comprehensive codebase documentation)
- **[Dual-Lane Architecture](docs/specs/dual_lane_architecture.md)** — Prediction vs Shadow lane separation specification
- **[SCO Stack](README_SCO.md)** — Symbolic Compression Operator documentation
- **[Orin Spine](README_ORIN.md)** — Edge deployment and infrastructure
- **[Integration Guide](INTEGRATION_SCO.md)** — TypeScript/Python integration
- **[Deployment Guide](DEPLOYMENT_SCO.md)** — Production deployment
- **[Conflict Resolution Guide](CONFLICT_RESOLUTION_GUIDE.md)** — Merge conflict resolution strategies

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

# E2E test
curl -X POST http://localhost:5000/api/sco/analyze \
  -H "Content-Type: application/json" \
  -d '{"texts": ["I love Aphex Twins"], "domain": "music"}'
```

---

## 🤝 Contributing

Contributions welcome! This project follows deterministic, provenance-first design principles:

1. All changes must pass `abx smoke` deterministic tests
2. Include SHA-256 provenance for new linguistic events
3. Maintain backward compatibility for API endpoints
4. Follow existing code style (TypeScript/Python)

---

## 📄 License

MIT License — See [LICENSE](LICENSE) file for details.

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
