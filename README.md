<div align="center">

# Abraxas

### Deterministic Symbolic Intelligence & Linguistic Weather System

*Provenance-embedded compression detection, memetic drift analysis, and self-healing infrastructure for edge deployment.*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Core Features](#core-features)
- [Architecture](#architecture)
- [CLI Reference](#cli-reference)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Testing](#testing)
- [Documentation](#documentation)
- [Project Status](#project-status)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**Abraxas** is a production-grade symbolic intelligence system that:

- **Detects linguistic compression patterns** (eggcorns like "apex twin" → "aphex twin")
- **Tracks memetic drift** and lifecycle dynamics across domains
- **Operates as an always-on edge appliance** with self-healing capabilities
- **Generates deterministic provenance** for every linguistic event

Think of it as a **weather system for language** — detecting symbol compression, mapping affective drift, and forecasting symbolic evolution.

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

### Design Principles

| Principle | Description |
|-----------|-------------|
| **Determinism** | Same inputs always produce same outputs with SHA-256 provenance |
| **Dual-Lane Architecture** | Prediction and diagnostics stay strictly separated |
| **Edge-Ready** | Optimized for Jetson Orin with systemd and atomic updates |
| **Full-Stack** | Python SCO/ECO core + TypeScript orchestration + React UI |

> **AI Assistants**: Start with [CLAUDE.md](CLAUDE.md) for the comprehensive development guide.

---

## Quick Start

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

# Install Node.js dependencies
npm install

# Run system diagnostic
abx doctor
```

### First Analysis

```bash
# Analyze text for symbolic compression
python -m abraxas.cli.sco_run \
  --records tests/records.json \
  --lexicon tests/lexicon.json \
  --out events.jsonl \
  --domain music

# Start the chat UI
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
# Start TypeScript development server (hot reload)
npm run dev

# Run tests
pytest tests/    # Python
npm test         # TypeScript
```

---

## Core Features

### Symbolic Compression Detection (SCO/ECO)

Detect when language users compress symbols while preserving intent.

| Tier | Description | Thresholds |
|------|-------------|------------|
| **ECO_T1** | Eggcorn compression | Phonetic similarity ≥0.85, STI delta ≥0.18 |
| **SCO_T2** | General compression | Moderate thresholds with provenance |

**Metrics**: STI (Symbolic Transparency Index), CP (Compression Pressure), IPS (Inter-Phonetic Similarity), RDV (Replacement Direction Vector)

```json
{
  "tier": "ECO_T1",
  "original_token": "aphex twin",
  "replacement_token": "apex twin",
  "compression_pressure": 1.42,
  "symbolic_transparency_index": 0.45,
  "rdv": {"humor": 0.0, "intimacy": 0.6, "irony": 0.0}
}
```

### Weather Engine

Transform compression events into memetic weather patterns:

- **Symbolic Drift** — intensity of symbol replacement
- **Transparency Flux** — rate of semantic clarification/obscuration
- **RDV Tracking** — humor, aggression, authority, intimacy, nihilism, irony
- **Compression Stability** — eggcorn formation rate

### Oracle Pipeline

Deterministic forecasting with multi-phase architecture:

- **Oracle v1** — Daily oracle generation from correlation deltas
- **Oracle v2** — Signal → Compression → Forecast → Narrative assembly
- **6-Gate Governance** — Provenance, falsifiability, redundancy, rent, ablation, stabilization

### Scenario Envelope Runner (SER)

Deterministic scenario execution with:
- Cascade sheets and contamination advisories
- Weather/D/M/Almanac snapshot loading
- Full provenance tracking

### Anagram Sweep Engine (ASE)

Deterministic anagram mining for current-events feeds:

```bash
abraxas-ase run --in items.jsonl --out out/ase --date 2026-01-24 \
  --pfdi-state out_prev/ase/pfdi_state.json
```

### SDCT (Symbolic Domain Cartridge Template)

**ABX-Runes Enforced**: SDCT domains are invoked via rune contracts only. Engine does not call cartridges directly.

| Rune ID | Domain | Description |
|---------|--------|-------------|
| `sdct.text_subword.v1` | text.subword.v1 | Text subword motif extraction |
| `sdct.digit.v1` | digit.v1 | Digit n-gram motif extraction |

```python
from abraxas_ase.runes import invoke_rune

# Engine invokes via rune_id
result = invoke_rune("sdct.text_subword.v1", {"items": items}, ctx)

# Direct cartridge imports in engine are FORBIDDEN
# from abraxas_ase.domains.text_subword import TextSubwordCartridge  # Never!
```

To add a new cartridge:
- Create a domain module in `abraxas_ase/domains/`.
- Add a rune wrapper in `abraxas_ase/runes/` and register it in `abraxas_ase/runes/catalog.v0.yaml`.
- Register the domain in `abraxas_ase/domains/registry.py`.

See `abraxas_ase/runes/catalog.v0.yaml` for full rune catalog.

### Shadow Detectors & Metrics

Observe-only analytical layer (never influences predictions):

| Component | Purpose |
|-----------|---------|
| **Shadow Metrics** | SEI, CLIP, NOR, PTS, SCG, FVC |
| **Compliance Detector** | Lexical overlap vs novel recombination |
| **Meta-Awareness Detector** | Algorithmic/manipulation discourse |
| **Negative Space Detector** | Topic dropout and visibility asymmetry |

### Self-Healing Infrastructure

Production-grade reliability for edge deployment:

- **Drift Detection** — git SHA, config, assets, dependencies tracking
- **Watchdog** — automatic service restart on health check failures
- **Atomic Updates** — zero-downtime deployments with rollback
- **Systemd Integration** — managed lifecycle for Jetson Orin

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     ABRAXAS ECOSYSTEM                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TypeScript/Express Layer                                       │
│  └─ API Routes, Weather Engine, Chat UI, Task Registry          │
│                       │                                         │
│  Python SCO/ECO Core  ▼                                         │
│  └─ Symbolic Compression, Phonetics, STI, RDV, Tau Operators   │
│                       │                                         │
│  Orin Boot Spine      ▼                                         │
│  └─ Drift Detection, Overlay Lifecycle, Atomic Updates         │
│                       │                                         │
│  Data Layer           ▼                                         │
│  └─ Decodo API, SQLite/PostgreSQL, JSONL Ledgers, AAlmanac     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Dual-Lane Architecture

Abraxas enforces strict separation between prediction and diagnostics:

| Lane | Purpose | Characteristics |
|------|---------|-----------------|
| **Prediction Lane** | Truth-pure forecasting | Morally agnostic, accuracy-focused |
| **Shadow Lane** | Observe-only diagnostics | Never influences predictions |
| **Lane Guard (ϟ₇)** | Enforces separation | Promotion requires calibration evidence |

See [docs/specs/dual_lane_architecture.md](docs/specs/dual_lane_architecture.md) for full specification.

### ABX-Runes Coupling

All cross-subsystem communication flows through capability contracts:

```python
# Correct: Via capability contract
from abraxas.runes.capabilities import invoke_capability

result = invoke_capability("oracle.v2.run", inputs, ctx)

# Forbidden: Direct imports
# from abraxas.oracle import run_oracle  # Never do this
```

See [docs/migration/abx_runes_coupling.md](docs/migration/abx_runes_coupling.md) for details.

---

## CLI Reference

### Core Commands

```bash
abx doctor          # System diagnostics
abx up              # Start HTTP server
abx smoke           # Run deterministic smoke test
abx ui              # Start chat UI server
abx ingest          # Start data ingestion
abx admin           # Print admin handshake JSON
```

### Overlay & Drift Management

```bash
abx assets sync     # Generate asset manifest
abx overlay list    # List installed overlays
abx drift check     # Check for configuration drift
abx watchdog        # Start health monitoring
abx update          # Atomic update with rollback
```

### Analysis Commands

```bash
# SCO analysis
python -m abraxas.cli.sco_run --records <file> --lexicon <file> --out <file>

# v1.4 unified CLI
python -m abraxas.cli.abx_run_v1_4 \
  --observations data/obs.json \
  --format both \
  --artifacts cascade_sheet,contamination_advisory

# Resonance narratives
abx resonance-narrative --envelope <file> --out <file>
```

### ASE Commands

```bash
# Run anagram sweep
abraxas-ase run --in items.jsonl --out out/ase --date 2026-01-24

# Update lexicon
python -m abraxas_ase.tools.lexicon_update --in lexicon_sources --out abraxas_ase

# Promote candidates
python -m abraxas_ase.tools.promote_lanes \
  --candidates out/ase/candidates.jsonl \
  --lanes-dir lexicon_sources/lanes \
  --apply
```

---

## API Reference

### Health Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/healthz` | Liveness check |
| GET | `/readyz` | Readiness with provenance |

### SCO Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sco/analyze` | Run compression detection |
| POST | `/api/sco/weather` | Generate weather signals |
| GET | `/api/sco/lexicons` | List available lexicons |

### Chat Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/handshake` | Discover modules |
| POST | `/chat` | Send messages |
| GET | `/data/latest` | Inspect ingested data |

---

## Configuration

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
sudo systemctl enable abraxas-core abx-ingest abx-ui abx-watchdog
sudo systemctl enable abx-update.timer
sudo systemctl status abraxas-core abx-ingest abx-ui
```

---

## Testing

```bash
# Python tests
pytest tests/
pytest tests/ -v --cov=abraxas

# TypeScript tests
npm test
npm run test:coverage

# Smoke test (deterministic)
abx smoke

# Acceptance suite
python tools/acceptance/run_acceptance_suite.py

# Seal release validation
python -m scripts.seal_release --run_id seal --tick 0 --runs 12
```

---

## Documentation

### Core Guides

| Document | Description |
|----------|-------------|
| [CLAUDE.md](CLAUDE.md) | AI assistant development guide |
| [README_SCO.md](README_SCO.md) | SCO stack documentation |
| [README_ORIN.md](README_ORIN.md) | Edge deployment infrastructure |
| [INTEGRATION_SCO.md](INTEGRATION_SCO.md) | TypeScript/Python integration |
| [DEPLOYMENT_SCO.md](DEPLOYMENT_SCO.md) | Production deployment |

### Specifications

| Document | Description |
|----------|-------------|
| [Dual-Lane Architecture](docs/specs/dual_lane_architecture.md) | Prediction/shadow separation |
| [Metric Governance](docs/specs/metric_governance.md) | 6-gate promotion system |
| [Shadow Detectors](docs/detectors/shadow_detectors_v0_1.md) | Observe-only pattern detection |
| [ABX-Runes Coupling](docs/migration/abx_runes_coupling.md) | Capability contract migration |

### Additional Resources

| Document | Description |
|----------|-------------|
| [Overlay Contract](docs/overlay_contract.md) | Overlay initialization workflow |
| [Neon-Genie Adapter](docs/integration/neon_genie_adapter.md) | Symbolic generation integration |
| [SLANG-HIST v1](docs/SLANG-HIST.v1.md) | Historical slang seed corpus |
| [Canonical Ledger](docs/canon/ABRAXAS_CANON_LEDGER.txt) | Canonical patterns |

---

## Project Status

### Current Version: v2.2.3 (January 2026)

**Recent Additions:**
- Rune handlers & kernel routing (weather, SER, daemon, edge deploy)
- SLANG-HIST v1 seed corpus (1450+ historical entries)
- Neon-Genie ABX-Runes adapter
- Oracle v2 factory wiring with lifecycle integration
- Comprehensive failure inventory (98+ cataloged test failures)

### Completed Features

- SCO/ECO symbolic compression detection
- Oracle Pipeline v1 & v2 with governance
- Shadow Detectors v0.1 & Shadow Metrics
- Dual-Lane Architecture with Lane Guard
- 6-Gate Metric Governance System
- Phase Detection Engine
- Domain Compression Engines (DCE)
- Anagram Sweep Engine (ASE)
- Self-Healing Infrastructure & Orin Boot Spine
- ABX-Runes capability contracts

### Roadmap

See [ROADMAP.md](ROADMAP.md) for the full priority stack.

**Next priorities:**
- Resonance Narratives (human-readable output layer)
- UI Dashboard (after Oracle v2 artifacts stabilize)
- Multi-Domain Analysis expansion

---

## Contributing

Contributions welcome. Abraxas is deterministic and provenance-first:

1. All changes must pass `abx smoke` deterministic tests
2. Include SHA-256 provenance for new linguistic events
3. Maintain backward compatibility for API endpoints
4. Follow existing code style (TypeScript/Python)
5. Network installs forbidden; PyYAML is vendored

See [CONFLICT_RESOLUTION_GUIDE.md](CONFLICT_RESOLUTION_GUIDE.md) for merge strategies.

---

## License

MIT License — see [LICENSE](LICENSE).

---

<div align="center">

**Built for deterministic symbolic intelligence at the edge**

*Abraxas — Where language becomes weather*

[GitHub](https://github.com/scrimshawlife-ctrl/Abraxas) · [Issues](https://github.com/scrimshawlife-ctrl/Abraxas/issues)

</div>
