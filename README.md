<div align="center">

# 🜏 Abraxas

### Deterministic Symbolic Intelligence & Linguistic Weather System

*Provenance-embedded compression detection, memetic drift analysis, and self-healing infrastructure for edge deployment*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Quick Start](#-quick-start) • [Architecture](#-architecture) • [Features](#-features) • [Documentation](#-documentation) • [Project Status](#-project-status)

</div>

---

## 🎯 What is Abraxas?

**Abraxas** is a production-grade symbolic intelligence system that detects linguistic compression patterns, tracks memetic drift, and operates as an always-on edge appliance with self-healing capabilities.

Think of it as a **weather system for language** — detecting when symbols compress ("eggcorns" like "apex twin" → "aphex twin"), tracking affective drift, and generating deterministic provenance for every linguistic event.

### Core Capabilities

- **🔬 Symbolic Compression Detection (SCO/ECO)** — Detect and quantify when opaque symbols are replaced with semantically transparent substitutes
- **🌦️ Weather Engine** — Transform linguistic events into memetic weather patterns and drift signals
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

### 🚧 In Progress

- [ ] **Real LLM Integration** — Replace stub chat engine with local/remote LLM
- [ ] **UI Dashboard** — React components for weather visualization
- [ ] **Expanded Lexicons** — Domain-specific compression dictionaries
- [ ] **PostgreSQL Migration** — Scale beyond SQLite for production
- [ ] **WebSocket Integration** — Real-time compression event streaming

### 🎯 Roadmap

- [ ] **Oracle Pipeline** — Daily oracle generation from drift signals
- [ ] **Ritual System** — Rune-based symbolic modulation
- [ ] **Multi-Domain Analysis** — Crypto, idiom, slang, technical jargon
- [ ] **Event Correlation** — Cross-domain drift pattern detection
- [ ] **Mobile UI** — Edge device management interface

### 📊 Recent Updates

See recent pull requests and commits:
- **#8** — Integrate Operator Auto-Synthesis (OAS) into Abraxas Slang System
- **#7** — Add always-on Abraxas daemon with Decodo ingestion and chat UI
- Pydantic dependency and OAS module integration
- Self-healing layer with watchdog and atomic updates

---

## 📖 Documentation

### Core Modules

- **[SCO Stack](README_SCO.md)** — Symbolic Compression Operator documentation
- **[Orin Spine](README_ORIN.md)** — Edge deployment and infrastructure
- **[Integration Guide](INTEGRATION_SCO.md)** — TypeScript/Python integration
- **[Deployment Guide](DEPLOYMENT_SCO.md)** — Production deployment

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
