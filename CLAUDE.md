# CLAUDE.md - AI Assistant Development Guide for Abraxas

**Last Updated:** 2025-12-29
**Version:** 1.4.1
**Purpose:** Comprehensive guide for AI assistants working with the Abraxas codebase

---

## Recent Updates (v1.4.1)

**2025-12-29** - Merged 4 major PRs consolidating governance, acquisition, and infrastructure:

1. **PR #20** - Python cache patterns + kernel phase system
   - Enhanced `.gitignore` for comprehensive Python cache handling
   - Added 5-phase kernel system (OPEN/ALIGN/ASCEND/CLEAR/SEAL)
   - Overlay lifecycle management improvements

2. **PR #22** - Anti-hallucination metric governance system
   - 6-gate promotion framework for emergent metrics
   - Simulation mapping layer with 22 academic papers
   - 75+ test cases for metric evaluation
   - Hash-based provenance chain verification
   - **Philosophy**: "Metrics are Contracts, not Ideas"

3. **PR #28** - WO-100: Acquisition & analysis infrastructure
   - Anchor → URL resolution system
   - Reupload storm detection
   - Forecast accuracy tracking with horizon bands
   - Manipulation front detection & metrics
   - Media origin verification
   - 40+ new ABX modules with ledger systems

4. **PR #36** - Documentation enhancements
   - Comprehensive README improvements
   - Quick start guide
   - Architecture overview

**Total Changes**: 120 files changed, 15,654 additions, 466 deletions

---

## Table of Contents

1. [Repository Overview](#repository-overview)
2. [Architecture & Structure](#architecture--structure)
3. [Development Workflows](#development-workflows)
4. [Key Conventions & Principles](#key-conventions--principles)
5. [Module Organization](#module-organization)
6. [Testing Patterns](#testing-patterns)
7. [Common Development Tasks](#common-development-tasks)
8. [Git Workflow](#git-workflow)
9. [Integration Points](#integration-points)
10. [Important Files & Directories](#important-files--directories)

---

## Repository Overview

### What is Abraxas?

**Abraxas** is a production-grade symbolic intelligence system that:
- Detects linguistic compression patterns (SCO/ECO)
- Tracks memetic drift and lifecycle dynamics
- Operates as an always-on edge appliance with self-healing capabilities
- Generates deterministic provenance for every linguistic event
- Provides "weather forecasts" for language and symbolic patterns

Think of it as a **weather system for language** — detecting when symbols compress, tracking affective drift, and generating deterministic provenance.

### Core Technology Stack

- **Python 3.11+**: Core linguistic analysis, operators, pipelines
- **TypeScript 5.6+**: API server, orchestration, UI components
- **Node.js 18+**: Express server, Weather Engine, integrations
- **SQLite/PostgreSQL**: Data persistence
- **React 18**: UI components (client/)
- **Drizzle ORM**: Database management
- **Vite**: Build tooling
- **Pytest**: Python testing
- **Vitest**: TypeScript testing

### Project Philosophy

Abraxas follows strict **deterministic, provenance-first design principles**:

1. **Determinism**: Same inputs always produce same outputs
2. **Provenance**: Every artifact includes SHA-256 hash for reproducibility
3. **Write-Once, Annotate-Only**: Canonical state is immutable
4. **Anti-Hallucination**: Metrics are contracts, not ideas
5. **Rent-Payment**: Complexity must justify its existence
6. **Edge-Ready**: Optimized for NVIDIA Jetson Orin deployment

---

## Architecture & Structure

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ABRAXAS ECOSYSTEM v4.2.0                     │
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
│  │  • Temporal Tau Operator (τ)                             │  │
│  │  • D/M Layer (Information Integrity)                     │  │
│  │  • SOD (Second-Order Dynamics)                           │  │
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
│  │  • SQLite/PostgreSQL Storage                             │  │
│  │  • JSONL Event Persistence                               │  │
│  │  • AAlmanac Ledger (Write-Once)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
Abraxas/
├── abraxas/                    # Python core modules
│   ├── core/                   # Core utilities (provenance, metrics, tau)
│   ├── operators/              # Symbolic operators (SCO, etc.)
│   ├── linguistic/             # Linguistic analysis utilities
│   ├── pipelines/              # Processing pipelines
│   ├── cli/                    # CLI entry points
│   │   └── sim_map.py          # Simulation mapping CLI
│   ├── lexicon/                # Lexicon engine v1
│   ├── oracle/                 # Oracle pipeline v1
│   ├── slang/                  # Slang analysis & AAlmanac
│   ├── integrity/              # D/M layer (information integrity)
│   ├── sod/                    # Second-Order Dynamics
│   │   └── sim_adapter.py      # Simulation adapter for SOD
│   ├── weather/                # Weather engine (Python)
│   ├── kernel/                 # Execution kernel (5-phase ASCEND)
│   │   ├── __init__.py         # Exports run_phase, Phase, execute_ascend
│   │   ├── entry.py            # Phase router (OPEN/ALIGN/ASCEND/CLEAR/SEAL)
│   │   └── ascend_ops.py       # Whitelisted ASCEND operations
│   ├── shadow_metrics/         # Shadow Structural Metrics (observe-only analytical layer)
│   │   ├── __init__.py         # Access control and version
│   │   ├── core.py             # Core types and utilities
│   │   ├── sei.py              # Sentiment Entropy Index
│   │   ├── clip.py             # Cognitive Load Intensity Proxy
│   │   ├── nor.py              # Narrative Overload Rating
│   │   ├── pts.py              # Persuasive Trajectory Score
│   │   ├── scg.py              # Social Contagion Gradient
│   │   ├── fvc.py              # Filter Velocity Coefficient
│   │   └── patch_registry.py   # Incremental patch tracking
│   ├── detectors/              # Pattern detectors
│   │   └── shadow/             # Shadow detectors (feed evidence to shadow_metrics)
│   │       ├── __init__.py     # Package exports
│   │       ├── types.py        # Base detector types
│   │       ├── registry.py     # Detector registry
│   │       ├── compliance_remix.py       # Compliance vs Remix detector
│   │       ├── meta_awareness.py         # Meta-Awareness detector
│   │       └── negative_space.py         # Negative Space / Silence detector
│   ├── overlay/                # Overlay management
│   ├── drift/                  # Drift detection
│   ├── storage/                # Data persistence
│   ├── decodo/                 # Decodo API integration
│   ├── backtest/               # Backtesting system
│   ├── learning/               # Active learning loops
│   ├── evolution/              # Metric evolution
│   ├── metrics/                # Metric governance (6-gate promotion)
│   │   ├── governance.py       # Candidate metrics & promotion system
│   │   ├── evaluate.py         # MetricEvaluator with 6 gates
│   │   ├── registry_io.py      # CandidateRegistry & PromotionLedger
│   │   ├── hashutil.py         # Provenance hash utilities
│   │   └── cli.py              # Metric governance CLI
│   ├── simulation/             # Simulation mapping layer
│   │   ├── add_metric.py       # Metric candidate creation from papers
│   │   ├── registries/         # Metric, outcome, rune, simvar registries
│   │   ├── schemas/            # JSON schemas for validation
│   │   ├── validation.py       # Schema validation utilities
│   │   └── examples/           # Exemplar implementations
│   ├── sim_mappings/           # Academic paper → Abraxas variable mappings
│   │   ├── mapper.py           # Core mapping engine
│   │   ├── family_maps.py      # Family-specific mappings (ABM, diffusion, etc.)
│   │   ├── normalizers.py      # Variable name normalization
│   │   ├── importers.py        # CSV/JSON import utilities
│   │   └── registry.py         # Paper registry management
│   ├── scoreboard/             # Scoreboard system
│   ├── forecast/               # Forecasting
│   ├── scenario/               # Scenario envelope runner
│   ├── evidence/               # Evidence management
│   ├── governance/             # Governance policies
│   ├── policy/                 # Policy enforcement
│   ├── economics/              # Economics models
│   ├── conspiracy/             # Conspiracy detection
│   ├── disinfo/                # Disinformation analysis
│   └── ...                     # Additional modules
│
├── abx/                        # ABX runtime & utilities
│   ├── cli.py                  # Main ABX CLI entry point
│   ├── core/                   # Core ABX utilities
│   ├── runtime/                # Runtime management
│   ├── server/                 # ABX server components
│   ├── ingest/                 # Data ingestion
│   ├── ui/                     # UI components
│   ├── assets/                 # Asset management
│   ├── overlays/               # Overlay modules
│   ├── operators/              # ABX operators
│   ├── bus/                    # Event bus
│   ├── store/                  # Storage utilities
│   ├── util/                   # Utility functions
│   ├── codex/                  # Codex integration
│   │
│   ├── # WO-100: Acquisition & Analysis Modules
│   ├── acquisition_execute.py  # Task executor with ROI calculation
│   ├── task_ledger.py          # Task lifecycle event tracking
│   ├── anchor_url_resolver.py  # Anchor → URL resolution
│   ├── reupload_storm_detector.py # Reupload pattern detection
│   ├── media_origin_verify.py  # Media fingerprint verification
│   ├── manipulation_metrics.py # Manipulation front detection
│   ├── manipulation_fronts_to_tasks.py # Front → task generation
│   │
│   ├── # Forecast & Oracle Modules
│   ├── oracle_ingest.py        # Oracle result ingestion
│   ├── forecast_accuracy.py    # Forecast accuracy tracking
│   ├── forecast_ledger.py      # Forecast storage & retrieval
│   ├── forecast_review_state.py # Review state management
│   ├── horizon.py              # Horizon band definitions
│   ├── review_scheduler.py     # Review scheduling system
│   │
│   ├── # AAlmanac & Slang Processing
│   ├── aalmanac.py             # AAlmanac ledger management
│   ├── aalmanac_enrich.py      # AAlmanac enrichment
│   ├── aalmanac_tau.py         # Temporal Tau processing
│   ├── slang_extract.py        # Slang candidate extraction
│   ├── slang_migration.py      # Slang lifecycle migration
│   │
│   ├── # Weather & Task Orchestration
│   ├── mimetic_weather.py      # Memetic weather calculation
│   ├── weather_to_tasks.py     # Weather → task generation
│   ├── cycle_runner.py         # Cycle execution runner
│   ├── task_union.py           # Task union operations
│   ├── task_union_ledger.py    # Union ledger tracking
│   ├── task_roi_report.py      # Task ROI reporting
│   │
│   ├── # Binding & Pollution Analysis
│   ├── term_claim_binder.py    # Term ↔ claim binding
│   ├── truth_pollution.py      # Truth pollution metrics
│   │
│   └── providers/              # External provider adapters
│       └── fetch_adapter.py    # HTTP fetch adapter
│
├── server/                     # TypeScript Express server
│   ├── index.ts                # Server entry point
│   ├── routes.ts               # Main route definitions
│   ├── abraxas.ts              # Abraxas integration
│   ├── abraxas-server.ts       # Abraxas routes setup
│   ├── storage.ts              # Storage abstraction
│   ├── replitAuth.ts           # Replit authentication
│   ├── abraxas/                # Abraxas server modules
│   │   ├── integrations/       # Python bridge, external APIs
│   │   ├── pipelines/          # TS pipelines
│   │   ├── routes/             # Module-specific routes
│   │   ├── weather/            # Weather engine modules
│   │   └── tests/              # Server tests
│   ├── alive/                  # ALIVE system routes
│   └── integrations/           # External integrations
│
├── client/                     # React frontend
│   ├── src/                    # React source code
│   │   ├── components/         # React components
│   │   ├── hooks/              # Custom hooks
│   │   ├── lib/                # Client utilities
│   │   └── pages/              # Page components
│   └── public/                 # Static assets
│
├── shared/                     # Shared TypeScript code
│   └── schema.ts               # Drizzle schema definitions
│
├── tests/                      # Python tests
│   ├── fixtures/               # Test fixtures
│   ├── golden/                 # Golden test data
│   ├── helpers/                # Test helpers
│   └── test_*.py               # Test files
│
├── data/                       # Data storage
│   ├── acquire/                # Acquisition data
│   ├── backtests/              # Backtest results
│   ├── evolution/              # Evolution ledgers
│   ├── forecast/               # Forecast data
│   ├── rent_manifests/         # Rent manifests
│   ├── run_plans/              # Run plans
│   ├── vector_maps/            # Vector maps
│   └── sim_sources/            # Simulation sources & paper data
│       ├── papers.json         # Academic paper metadata
│       ├── paper_mapping_table.csv # Paper → variable mappings
│       └── examples/           # Example paper extracts (PMC, arXiv, etc.)
│
├── out/                        # Output artifacts
│   ├── reports/                # Generated reports
│   ├── evolution_ledgers/      # Evolution outputs
│   └── ledger/                 # Append-only JSONL ledgers
│       ├── aalmanac.jsonl      # AAlmanac entries
│       ├── aalmanac_events.jsonl # AAlmanac lifecycle events
│       ├── task_ledger.jsonl   # Task execution events
│       ├── task_outcomes.jsonl # Task outcome tracking
│       ├── oracle_runs.jsonl   # Oracle execution history
│       ├── forecast_outcomes.jsonl # Forecast accuracy results
│       ├── manipulation_metrics.jsonl # Manipulation front metrics
│       ├── media_origin_ledger.jsonl # Media verification results
│       ├── reupload_fronts.jsonl # Reupload detection results
│       ├── binder_ledger.jsonl # Term-claim bindings
│       ├── union_ledger.jsonl  # Task union operations
│       ├── scheduler_ledger.jsonl # Review scheduling events
│       └── slang_candidates.jsonl # Slang candidate tracking
│
├── docs/                       # Documentation
│   ├── canon/                  # Canonical documentation
│   │   └── ABRAXAS_CANON_LEDGER.txt
│   ├── specs/                  # Specification documents
│   │   ├── metric_governance.md # 6-gate metric promotion system
│   │   ├── simulation_architecture.md # Simulation layer architecture
│   │   ├── simulation_mapping_layer.md # Paper → variable mappings
│   │   ├── paper_triage_rules.md # Paper triage & classification
│   │   └── paper_mapping_table_template.csv # Mapping table template
│   └── plan/                   # Implementation plans
│       └── simulation_mapping_layer_plan.md # Mapping layer implementation
│
├── systemd/                    # Systemd service files
├── scripts/                    # Utility scripts
├── tools/                      # Development tools
├── examples/                   # Example code
├── registry/                   # Registry files
│   ├── metrics_candidate.json  # Metric candidate registry
│   └── examples/               # Example candidate metrics
│       └── candidate_MEDIA_COMPETITION_MISINFO_PRESSURE.json
│
├── schemas/                    # JSON schemas
│   └── metric_candidate.schema.json # Metric candidate validation schema
│
├── package.json                # Node.js dependencies
├── pyproject.toml              # Python project config
├── tsconfig.json               # TypeScript config
├── vite.config.ts              # Vite build config
├── vitest.config.ts            # Vitest test config
├── drizzle.config.ts           # Drizzle ORM config
├── tailwind.config.ts          # Tailwind CSS config
│
├── README.md                   # Main README
├── README_SCO.md               # SCO stack documentation
├── README_ORIN.md              # Orin spine documentation
├── INTEGRATION_SCO.md          # Integration guide
├── DEPLOYMENT_SCO.md           # Deployment guide
├── CONFLICT_RESOLUTION_GUIDE.md # Merge conflict guide
├── design_guidelines.md        # Design guidelines
├── CHANGELOG.md                # Changelog
└── CLAUDE.md                   # This file
```

---

## Development Workflows

### Initial Setup

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

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials
```

### Development Server

```bash
# Start TypeScript development server (hot reload)
npm run dev

# Start production server
npm run build
npm start

# Start Python CLI tools
python -m abraxas.cli.sco_run --help
abx --help
```

### Running Tests

```bash
# Python tests
pytest tests/                    # Run all tests
pytest tests/test_oracle_runner.py  # Run specific test
pytest -v                        # Verbose output
pytest --cov=abraxas            # With coverage

# TypeScript tests
npm test                         # Run all tests
npm run test:watch              # Watch mode
npm run test:ui                 # UI mode
npm run test:coverage           # With coverage

# Smoke test (deterministic)
abx smoke
```

### Type Checking

```bash
# TypeScript type checking
npm run check

# Python type hints (if using mypy)
mypy abraxas/
```

### Building for Production

```bash
# Build TypeScript
npm run build

# The build creates:
# - dist/index.js (server bundle)
# - client/dist/ (client bundle)
```

---

## Key Conventions & Principles

### 1. Determinism

**CRITICAL**: All operations must be deterministic. Same inputs → same outputs.

- Use stable sorting (e.g., `sorted()` with explicit key)
- No random operations without fixed seeds
- Timestamps should be ISO8601 with 'Z' timezone
- SHA-256 hashes for all provenance tracking

### 2. Provenance-First Design

Every artifact includes provenance metadata:

```python
from abraxas.core.provenance import Provenance, hash_canonical_json

# Example provenance creation
provenance = Provenance(
    run_id="RUN-001",
    started_at_utc=Provenance.now_iso_z(),
    inputs_hash=hash_canonical_json(inputs),
    config_hash=hash_canonical_json(config),
    git_sha="abc123",
    host="prod-01"
)
```

### 3. Write-Once, Annotate-Only

Canonical data (like AAlmanac) is **write-once, annotate-only**:

- Create entries once with immutable core fields
- Modifications happen via annotations (append-only)
- Never mutate existing canonical entries
- See `docs/canon/ABRAXAS_CANON_LEDGER.txt` for canonical patterns

### 4. Naming Conventions

#### Python

- **Files**: `snake_case.py` (e.g., `temporal_tau.py`, `symbolic_compression.py`)
- **Classes**: `PascalCase` (e.g., `TauCalculator`, `SymbolicCompressionEvent`)
- **Functions**: `snake_case` (e.g., `compute_snapshot`, `hash_canonical_json`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_THRESHOLD`, `MAX_ITERATIONS`)
- **Private**: `_leading_underscore` (e.g., `_internal_helper`)

#### TypeScript

- **Files**: `kebab-case.ts` (e.g., `sco-bridge.ts`, `weather-engine.ts`)
- **Classes/Types**: `PascalCase` (e.g., `WeatherModule`, `ProvenanceBundle`)
- **Functions**: `camelCase` (e.g., `analyzeSymbolPool`, `computeRisk`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `API_BASE_URL`, `DEFAULT_PORT`)
- **React Components**: `PascalCase` files and exports

#### Module Naming Patterns

- **Operators**: `<name>_operator.py` or just `<name>.py` in `operators/`
- **Pipelines**: `<name>_pipeline.py` in `pipelines/`
- **CLI tools**: `<name>_run.py` or `<name>.py` in `cli/`
- **Tests**: `test_<name>.py` in `tests/`

### 5. Data Structures

#### Pydantic Models (Python)

Prefer Pydantic for data validation:

```python
from pydantic import BaseModel, Field

class MyModel(BaseModel):
    name: str = Field(..., description="The name")
    value: float = Field(default=0.0, description="The value")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
```

#### Zod Schemas (TypeScript)

Use Zod for TypeScript validation:

```typescript
import { z } from 'zod';

const MySchema = z.object({
  name: z.string(),
  value: z.number().default(0.0),
});

type MyType = z.infer<typeof MySchema>;
```

### 6. Error Handling

#### Python

```python
# Use specific exceptions
class AbraxasError(Exception):
    """Base exception for Abraxas errors."""
    pass

class ValidationError(AbraxasError):
    """Raised when validation fails."""
    pass

# Raise with context
if not is_valid:
    raise ValidationError(f"Invalid input: {reason}")
```

#### TypeScript

```typescript
// Use Error subclasses
class AbraxasError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AbraxasError';
  }
}

// Or return Result types
type Result<T, E = Error> = { ok: true; value: T } | { ok: false; error: E };
```

### 7. Logging

#### Python

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Processing started")
logger.warning("Potential issue detected")
logger.error("Operation failed", exc_info=True)
```

#### TypeScript

```typescript
// Use console with structured logging
console.log('[INFO]', 'Processing started');
console.warn('[WARN]', 'Potential issue');
console.error('[ERROR]', 'Operation failed', error);
```

### 8. Configuration

- Environment variables in `.env` (never commit)
- Defaults in code or config files
- Use `os.getenv()` in Python, `process.env` in TypeScript
- Document all environment variables in `.env.example`

---

## Module Organization

### Python Core Modules

#### `abraxas/core/`

Core utilities used across the system:

- **`provenance.py`**: Provenance tracking, hashing utilities
- **`metrics.py`**: Metric calculation utilities
- **`temporal_tau.py`**: Temporal τ operator (τₕ, τᵥ, τₚ)
- **`canonical.py`**: Canonical data handling
- **`registry.py`**: Registry management
- **`scheduler.py`**: Task scheduling
- **`rendering.py`**: Output rendering utilities
- **`resonance_frame.py`**: Resonance frame calculations

#### `abraxas/operators/`

Symbolic operators:

- **`symbolic_compression.py`**: SCO/ECO operator
- Other operators as they're added

#### `abraxas/linguistic/`

Linguistic analysis utilities:

- **`phonetics.py`**: Soundex, phonetic keys
- **`similarity.py`**: Edit distance, IPS
- **`transparency.py`**: STI calculation
- **`rdv.py`**: Replacement Direction Vector (affect detection)
- **`tokenize.py`**: Token extraction, n-grams

#### `abraxas/cli/`

CLI entry points:

- **`sco_run.py`**: SCO analysis CLI
- **`abx_run_v1_4.py`**: v1.4 unified CLI
- **`scenario_run.py`**: Scenario envelope runner
- **`rent_check.py`**: Rent enforcement checker
- **`backtest.py`**: Backtesting CLI
- **`learning.py`**: Active learning CLI
- **`oasis_cli.py`**: OASIS pipeline CLI
- And many more...

#### `abraxas/lexicon/`

Lexicon engine v1:

- Domain-scoped, versioned token-weight mapping
- Deterministic compression with provenance
- See README.md for details

#### `abraxas/oracle/`

Oracle pipeline v1:

- Deterministic daily oracle generation
- Correlation delta processing
- Time-weighted decay

#### `abraxas/slang/`

Slang analysis & AAlmanac:

- **`a_almanac_store.py`**: Write-once ledger
- **`operators/`**: Slang-specific operators
- Lifecycle state machine

#### `abraxas/integrity/`

D/M layer (Disinformation/Misinformation):

- Information integrity metrics
- NOT truth adjudication—evidence-based risk scores
- Artifact integrity, narrative manipulation detection

#### `abraxas/sod/`

Second-Order Dynamics:

- **NCP**: Narrative Cascade Predictor
- **CNF**: Counter-Narrative Forecaster
- **EFTE**: Epistemic Fatigue Threshold Engine
- **SPM**: Susceptibility Profile Mapper
- **RRM**: Recovery & Re-Stabilization Model
- **`sim_adapter.py`**: Adapter for simulation variable integration

#### `abraxas/metrics/`

**Metric Governance System** - 6-gate anti-hallucination promotion framework:

- **`governance.py`**: Core governance types (CandidateMetric, CandidateStatus, EvidenceBundle, PromotionDecision)
- **`evaluate.py`**: MetricEvaluator implementing 6 promotion gates:
  1. **Provenance Gate**: SHA-256 hash chain verification
  2. **Falsifiability Gate**: Test specification & concrete failure modes
  3. **Non-Redundancy Gate**: Correlation analysis vs existing metrics
  4. **Rent-Payment Gate**: Complexity justification
  5. **Ablation Gate**: Removal impact validation
  6. **Stabilization Gate**: Temporal stability verification
- **`registry_io.py`**: CandidateRegistry, PromotionLedger, promotion workflow
- **`hashutil.py`**: Canonical JSON hashing, provenance chain verification
- **`cli.py`**: Command-line interface for metric governance operations

**Philosophy**: Metrics are Contracts, not Ideas. All emergent metrics must earn promotion through evidence.

#### `abraxas/simulation/`

**Simulation Mapping Layer** - Academic paper → Abraxas metric extraction:

- **`add_metric.py`**: Extract metric candidates from simulation papers
- **`registries/`**: Registry management for metrics, outcomes, runes, simvars
  - **`metric_registry.py`**: Metric definition storage
  - **`outcome_ledger.py`**: Simulation outcome tracking
  - **`rune_registry.py`**: Rune (symbolic binding) registry
  - **`simvar_registry.py`**: Simulation variable registry
- **`schemas/`**: JSON schemas for validation
  - `metric.schema.json`, `outcome_ledger.schema.json`, `rune_binding.schema.json`, `simvar.schema.json`
- **`validation.py`**: Schema validation utilities
- **`examples/`**: Exemplar implementations (e.g., `media_competition_exemplar.py`)

Supports 22 academic papers across ABM, diffusion, opinion dynamics, game theory, and cascade families.

#### `abraxas/sim_mappings/`

**Academic Paper → Abraxas Variable Mappings**:

- **`mapper.py`**: Core mapping engine for variable translation
- **`family_maps.py`**: Family-specific mappings:
  - Agent-Based Models (ABM)
  - Diffusion models
  - Opinion dynamics
  - Game theory
  - Cascade models
- **`normalizers.py`**: Variable name normalization (Greek letters, subscripts, etc.)
- **`importers.py`**: CSV/JSON import utilities for paper data
- **`registry.py`**: Paper registry management
- **`types.py`**: Type definitions for mapping system

Enables systematic extraction of simulation priors from academic literature.

#### `abraxas/kernel/`

**5-Phase Execution Kernel** (OPEN → ALIGN → ASCEND → CLEAR → SEAL):

- **`entry.py`**: Phase router with deterministic dispatch
- **`ascend_ops.py`**: Whitelisted ASCEND operations (no IO, no writes)
- **`__init__.py`**: Exports `run_phase`, `Phase`, `execute_ascend`, `OPS`

Provides scoped execution environment for overlay operations.

#### `abraxas/shadow_metrics/`

**Shadow Structural Metrics (Cambridge Analytica-derived)** - Observe-only analytical layer:

- **LOCKED MODULE**: v1.0.0 (2025-12-29)
- Six observe-only psychological manipulation metrics:
  - **SEI**: Sentiment Entropy Index
  - **CLIP**: Cognitive Load Intensity Proxy
  - **NOR**: Narrative Overload Rating
  - **PTS**: Persuasive Trajectory Score
  - **SCG**: Social Contagion Gradient
  - **FVC**: Filter Velocity Coefficient
- **Access Control**: ABX-Runes ϟ₇ (SSO) ONLY - direct access forbidden
- **No-Influence Guarantee**: Metrics observe but never affect system decisions
- **SEED Compliant**: Fully deterministic with SHA-256 provenance
- **Incremental Patch Only**: All modifications via versioned patches
- **Coexists with Predictive Layer**: Analytical/observational metrics complement v1.5 predictive capabilities
- See `docs/specs/shadow_structural_metrics.md` for full specification

#### `abraxas/detectors/shadow/`

**Shadow Detectors** - Pattern detectors that feed evidence to Shadow Structural Metrics:

- **Compliance vs Remix Detector**: Balance between rote repetition and creative remix
- **Meta-Awareness Detector**: Meta-level discourse about manipulation and algorithms
- **Negative Space / Silence Detector**: Topic dropout and visibility asymmetry
- **Registry**: `compute_all_detectors()` with deterministic provenance tracking
- See `docs/detectors/shadow_detectors_v0_1.md` for specification

### TypeScript Server Modules

#### `server/`

Main Express server:

- **`index.ts`**: Server entry point
- **`routes.ts`**: Route registration
- **`storage.ts`**: Storage abstraction
- **`abraxas.ts`**: Abraxas integration
- **`abraxas-server.ts`**: Abraxas route setup

#### `server/abraxas/`

Abraxas-specific server modules:

- **`integrations/`**: Python bridge, external APIs
  - **`sco-bridge.ts`**: Python SCO CLI bridge
- **`pipelines/`**: TypeScript pipelines
  - **`sco-analyzer.ts`**: TS wrapper for SCO
- **`routes/`**: Module-specific routes
  - **`sco-routes.ts`**: SCO API endpoints
- **`weather/`**: Weather engine modules
- **`tests/`**: Server-side tests

#### `client/src/`

React frontend:

- **`components/`**: Reusable UI components
- **`hooks/`**: Custom React hooks
- **`lib/`**: Client utilities
- **`pages/`**: Page components

### ABX Runtime

#### `abx/`

ABX runtime and utilities with **WO-100** acquisition & analysis modules:

**Core Runtime**:
- **`cli.py`**: Main CLI (`abx` command)
- **`core/`**: Core utilities
- **`runtime/`**: Runtime management
- **`server/`**: ABX server components
- **`ingest/`**: Data ingestion
- **`ui/`**: UI components
- **`overlays/`**: Overlay modules
- **`codex/`**: Codex integration

**WO-100: Acquisition & Analysis**:
- **`acquisition_execute.py`**: Task executor with ROI calculation and outcome tracking
- **`task_ledger.py`**: Task lifecycle event tracking (STARTED/COMPLETED/BLOCKED)
- **`anchor_url_resolver.py`**: Anchor → URL resolution system
- **`reupload_storm_detector.py`**: Reupload pattern detection via fingerprinting
- **`media_origin_verify.py`**: Media fingerprint verification
- **`manipulation_metrics.py`**: Manipulation front detection & metrics
- **`manipulation_fronts_to_tasks.py`**: Convert detected fronts to acquisition tasks

**Forecast & Oracle Systems**:
- **`oracle_ingest.py`**: Oracle result ingestion and processing
- **`forecast_accuracy.py`**: Forecast accuracy tracking & horizon band analysis
- **`forecast_ledger.py`**: Forecast storage & retrieval
- **`forecast_review_state.py`**: Review state management
- **`horizon.py`**: Horizon band definitions (near/medium/far)
- **`review_scheduler.py`**: Automated review scheduling system

**AAlmanac & Slang Processing**:
- **`aalmanac.py`**: AAlmanac ledger management (write-once, append-only)
- **`aalmanac_enrich.py`**: AAlmanac enrichment with context & metadata
- **`aalmanac_tau.py`**: Temporal Tau (τ) processing for AAlmanac entries
- **`slang_extract.py`**: Slang candidate extraction from observations
- **`slang_migration.py`**: Slang lifecycle state migration

**Weather & Task Orchestration**:
- **`mimetic_weather.py`**: Memetic weather calculation & signal generation
- **`weather_to_tasks.py`**: Weather signal → acquisition task generation
- **`cycle_runner.py`**: Cycle execution runner for orchestrated workflows
- **`task_union.py`**: Task union operations (merge, deduplicate, prioritize)
- **`task_union_ledger.py`**: Union operation ledger tracking
- **`task_roi_report.py`**: Task ROI reporting & analytics

**Binding & Pollution Analysis**:
- **`term_claim_binder.py`**: Term ↔ claim binding with ledger tracking
- **`truth_pollution.py`**: Truth pollution metrics & narrative contamination

**External Providers**:
- **`providers/fetch_adapter.py`**: HTTP fetch adapter for external sources

Key ABX commands:
```bash
abx doctor          # System diagnostics
abx up              # Start HTTP server
abx smoke           # Run deterministic smoke test
abx ui              # Start chat UI server
abx ingest          # Start data ingestion
```

---

## Testing Patterns

### Python Testing (Pytest)

#### Test File Structure

```python
# tests/test_example.py
import pytest
from abraxas.core.provenance import hash_canonical_json

def test_hash_canonical_json_determinism():
    """Test that hash_canonical_json produces deterministic results."""
    obj = {"b": 2, "a": 1}
    hash1 = hash_canonical_json(obj)
    hash2 = hash_canonical_json(obj)
    assert hash1 == hash2

@pytest.fixture
def sample_data():
    """Fixture providing sample test data."""
    return {"key": "value"}

def test_with_fixture(sample_data):
    """Test using a fixture."""
    assert sample_data["key"] == "value"
```

#### Golden Tests

Golden tests verify output matches expected:

```python
# tests/golden/ contains reference outputs
def test_oracle_output_matches_golden():
    result = run_oracle(inputs)
    expected = load_golden("oracle_output.json")
    assert result == expected
```

### TypeScript Testing (Vitest)

#### Test File Structure

```typescript
// server/abraxas/tests/example.test.ts
import { describe, it, expect } from 'vitest';
import { myFunction } from '../myModule';

describe('myFunction', () => {
  it('should return expected result', () => {
    const result = myFunction('input');
    expect(result).toBe('expected');
  });

  it('should handle edge cases', () => {
    expect(() => myFunction(null)).toThrow();
  });
});
```

### Test Organization

- **Unit tests**: Test individual functions/methods
- **Integration tests**: Test module interactions
- **Golden tests**: Verify deterministic output stability
- **Smoke tests**: Quick sanity checks (`abx smoke`)

---

## Common Development Tasks

### Adding a New Python Module

1. Create module file in appropriate directory:
   ```bash
   touch abraxas/mymodule/my_operator.py
   ```

2. Add `__init__.py` if new package:
   ```python
   # abraxas/mymodule/__init__.py
   from abraxas.mymodule.my_operator import MyOperator

   __all__ = ["MyOperator"]
   ```

3. Update `pyproject.toml` if adding new package:
   ```toml
   [tool.setuptools]
   packages = [..., "abraxas.mymodule"]
   ```

4. Add tests:
   ```bash
   touch tests/test_my_operator.py
   ```

5. Document in relevant README

### Adding a New API Endpoint

1. Create route handler in `server/routes.ts` or module-specific routes:
   ```typescript
   app.post('/api/myendpoint', isAuthenticated, async (req, res) => {
     try {
       const result = await myHandler(req.body);
       res.json(result);
     } catch (error) {
       res.status(500).json({ error: error.message });
     }
   });
   ```

2. Add TypeScript types in `shared/` if needed

3. Add tests in `server/abraxas/tests/`

4. Update API documentation

### Adding a New CLI Command

1. Create CLI module in `abraxas/cli/`:
   ```python
   # abraxas/cli/my_command.py
   import argparse

   def main():
       parser = argparse.ArgumentParser(description="My command")
       parser.add_argument("--input", required=True)
       args = parser.parse_args()
       # Implementation

   if __name__ == "__main__":
       main()
   ```

2. Add entry point in `pyproject.toml` if needed:
   ```toml
   [project.scripts]
   my-command = "abraxas.cli.my_command:main"
   ```

3. Update CLI documentation

### Working with Provenance

Always include provenance for deterministic operations:

```python
from abraxas.core.provenance import Provenance, hash_canonical_json

# Create provenance
prov = Provenance(
    run_id=f"RUN-{uuid.uuid4().hex[:8]}",
    started_at_utc=Provenance.now_iso_z(),
    inputs_hash=hash_canonical_json(inputs),
    config_hash=hash_canonical_json(config),
    git_sha=get_git_sha(),  # Optional
    host=socket.gethostname()  # Optional
)

# Include in output
output = {
    "result": my_result,
    "provenance": prov.__dict__
}
```

### Database Migrations (Drizzle)

```bash
# Generate migration
npm run db:push

# Migrations are auto-applied with drizzle-kit
```

---

## Git Workflow

### Branch Naming Convention

**CRITICAL**: Branch names must follow this pattern for push to work:

```
claude/<descriptive-name>-<session-id>
```

Examples:
- `claude/add-weather-engine-5XgrC`
- `claude/fix-tau-calculation-k7dXE`
- `claude/implement-new-operator-EmBu1`

The session ID at the end is required for git push authentication.

### Commit Message Conventions

Use clear, descriptive commit messages:

```bash
# Good
git commit -m "Add temporal tau operator with confidence bands"
git commit -m "Fix: Handle edge case in phonetic similarity calculation"
git commit -m "Refactor: Extract provenance logic to core module"

# Prefix patterns
# - Add: New feature
# - Fix: Bug fix
# - Refactor: Code restructure without behavior change
# - Update: Modify existing feature
# - Remove: Delete code/feature
# - Docs: Documentation only
# - Test: Add or modify tests
```

### Creating Commits

Follow the git safety protocol from the system instructions:

1. Check status and diff:
   ```bash
   git status
   git diff
   git log --oneline -5
   ```

2. Stage relevant files:
   ```bash
   git add <files>
   ```

3. Create commit with descriptive message:
   ```bash
   git commit -m "$(cat <<'EOF'
   Add comprehensive CLAUDE.md documentation

   - Repository overview and architecture
   - Development workflows and conventions
   - Module organization and testing patterns
   - Git workflow and integration points
   EOF
   )"
   ```

4. Verify commit:
   ```bash
   git log -1
   git status
   ```

### Pushing Changes

**CRITICAL**: Use `-u origin <branch-name>` and retry on network failures:

```bash
# Push with upstream tracking
git push -u origin claude/my-feature-5XgrC

# If network error, retry with exponential backoff:
# Wait 2s, try again
# Wait 4s, try again
# Wait 8s, try again
# Wait 16s, try again (max 4 retries)
```

### Creating Pull Requests

Use GitHub CLI (`gh`):

```bash
# Check current state
git status
git diff main...HEAD
git log main..HEAD

# Create PR with descriptive title and body
gh pr create --title "Add weather engine integration" --body "$(cat <<'EOF'
## Summary
- Implement weather engine module
- Add TypeScript bridge to Python operators
- Include comprehensive tests

## Test plan
- [x] Run pytest tests
- [x] Run npm test
- [x] Test API endpoints manually
- [x] Verify deterministic output
EOF
)"
```

### Merge Conflict Resolution

See `CONFLICT_RESOLUTION_GUIDE.md` for detailed strategies.

General principles:
- Prefer more complete implementation
- Keep provenance and determinism
- Always run tests after resolution
- Document deviations

---

## Integration Points

### Python ↔ TypeScript Bridge

TypeScript calls Python CLI via subprocess:

```typescript
// server/abraxas/integrations/sco-bridge.ts
import { spawn } from 'child_process';

export async function runSCOAnalysis(records: any[], domain: string) {
  return new Promise((resolve, reject) => {
    const python = spawn('python', [
      '-m', 'abraxas.cli.sco_run',
      '--records', recordsPath,
      '--domain', domain,
      '--out', outputPath
    ]);

    // Handle output, errors, completion
  });
}
```

### Express API ↔ React Frontend

Frontend calls backend via fetch/React Query:

```typescript
// client/src/hooks/useAnalysis.ts
import { useQuery } from '@tanstack/react-query';

export function useAnalysis(domain: string) {
  return useQuery({
    queryKey: ['analysis', domain],
    queryFn: async () => {
      const res = await fetch(`/api/sco/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain })
      });
      return res.json();
    }
  });
}
```

### Python CLI Usage

Direct CLI invocation for batch processing:

```bash
# SCO Analysis
python -m abraxas.cli.sco_run \
  --records data.json \
  --out events.jsonl \
  --domain music

# v1.4 Unified CLI
python -m abraxas.cli.abx_run_v1_4 \
  --observations data/obs.json \
  --format both \
  --artifacts cascade_sheet,contamination_advisory

# Scenario Runner
python -m abraxas.cli.scenario_run \
  --input scenario.json \
  --output results/
```

---

## Important Files & Directories

### Must-Read Documentation

1. **`README.md`**: Main project overview
2. **`docs/canon/ABRAXAS_CANON_LEDGER.txt`**: Canonical patterns and principles
3. **`README_SCO.md`**: SCO stack documentation
4. **`README_ORIN.md`**: Orin spine documentation
5. **`INTEGRATION_SCO.md`**: Python/TypeScript integration
6. **`DEPLOYMENT_SCO.md`**: Deployment guide
7. **`CONFLICT_RESOLUTION_GUIDE.md`**: Merge conflict resolution

### Configuration Files

- **`.env`**: Environment variables (never commit)
- **`.env.example`**: Environment variable template
- **`package.json`**: Node.js dependencies and scripts
- **`pyproject.toml`**: Python project configuration
- **`tsconfig.json`**: TypeScript compiler options
- **`vite.config.ts`**: Vite build configuration
- **`vitest.config.ts`**: Vitest test configuration
- **`drizzle.config.ts`**: Drizzle ORM configuration
- **`tailwind.config.ts`**: Tailwind CSS configuration

### Key Data Directories

- **`data/`**: Input data, manifests, maps
- **`out/`**: Output artifacts, reports
- **`tests/fixtures/`**: Test fixture data
- **`tests/golden/`**: Golden test reference data

### Ignore Patterns

See `.gitignore`:
- `node_modules/`, `__pycache__/`, `.pytest_cache/`
- `dist/`, `build/`, `*.egg-info/`
- `.env`, `*.log`, `.DS_Store`
- `abraxas.db`, `*.tar.gz`

---

## Quick Reference

### Common Commands

```bash
# Development
npm run dev              # Start dev server
npm run build            # Build for production
npm test                 # Run TypeScript tests
pytest tests/            # Run Python tests
abx doctor              # System diagnostics
abx smoke               # Quick smoke test

# Type checking
npm run check           # TypeScript type check
mypy abraxas/           # Python type check

# Database
npm run db:push         # Push schema changes

# Git
git status              # Check status
git diff                # View changes
git log --oneline -10   # Recent commits
```

### Environment Variables

```bash
# Required
SESSION_SECRET=<random-string>
DATABASE_URL=file:./abraxas.db

# Optional
GOOGLE_CLIENT_ID=<oauth-client-id>
GOOGLE_CLIENT_SECRET=<oauth-secret>
OPENAI_API_KEY=<api-key>
ANTHROPIC_API_KEY=<api-key>
DECODO_AUTH_B64=<decodo-credentials>
ABX_PORT=8765
ABX_UI_PORT=8780
```

### Key Concepts

**Core Operators & Metrics**:
- **SCO/ECO**: Symbolic Compression Operator / Eggcorn Compression Operator
- **STI**: Symbolic Transparency Index
- **RDV**: Replacement Direction Vector
- **τ (Tau)**: Temporal operator (τₕ, τᵥ, τₚ)
- **D/M Layer**: Disinformation/Misinformation metrics
- **SOD**: Second-Order Dynamics
- **AAlmanac**: Write-once, annotate-only symbolic ledger
- **SER**: Scenario Envelope Runner
- **Provenance**: SHA-256 tracked execution metadata

**Metric Governance (New in v1.4.1)**:
- **6-Gate Promotion**: Provenance, Falsifiability, Non-Redundancy, Rent-Payment, Ablation, Stabilization
- **Candidate Metrics**: Metrics are Contracts, not Ideas - must earn promotion through evidence
- **Evidence Bundle**: Required documentation for metric promotion
- **Promotion Ledger**: Append-only record of promotion decisions with hash chain

**Simulation Layer (New in v1.4.1)**:
- **Simulation Mapping**: Academic paper → Abraxas variable translation
- **Family Maps**: ABM, diffusion, opinion dynamics, game theory, cascade model mappings
- **Rune Registry**: Symbolic bindings between simulation variables and Abraxas metrics
- **SimVar**: Simulation variable definitions with normalization

**WO-100: Acquisition & Analysis (New in v1.4.1)**:
- **Anchor Resolution**: Anchor → URL resolution system
- **Reupload Storm**: Reupload pattern detection via fingerprinting
- **Manipulation Front**: Coordinated manipulation pattern detection
- **Forecast Horizon**: Near/medium/far horizon bands for forecast accuracy
- **Task ROI**: Return-on-investment tracking for acquisition tasks
- **Truth Pollution**: Narrative contamination metrics

**Kernel System (New in v1.4.1)**:
- **5-Phase Model**: OPEN → ALIGN → ASCEND → CLEAR → SEAL
- **ASCEND Operations**: Whitelisted execution environment (no IO, no writes)
- **Overlay Lifecycle**: Phase-based overlay management

---

## Additional Resources

### External Documentation

- **Decodo API**: Web scraping integration
- **Drizzle ORM**: Database ORM documentation
- **Pydantic**: Python data validation
- **Zod**: TypeScript schema validation
- **Vitest**: Test framework documentation

### Internal Documentation

**Specification Documents** (`docs/specs/`):
- `metric_governance.md` - 6-gate metric promotion system
- `simulation_architecture.md` - Simulation layer architecture
- `simulation_mapping_layer.md` - Paper → variable mappings
- `paper_triage_rules.md` - Paper triage & classification
- `paper_mapping_table_template.csv` - Mapping table template

**Implementation Plans** (`docs/plan/`):
- `simulation_mapping_layer_plan.md` - Mapping layer implementation

**Example Code**:
- `examples/` - General examples
- `abraxas/simulation/examples/` - Simulation exemplars (e.g., media_competition_exemplar.py)
- `registry/examples/` - Example candidate metrics
- `data/sim_sources/examples/` - 22 academic paper extracts

**Test Resources**:
- `tests/fixtures/` - Test fixture data
- `tests/golden/` - Golden test reference data
- New tests: `test_metric_governance.py`, `test_sim_mappings_*.py`, `test_promotion_ledger_chain.py`

---

## ABX-Runes Coupling Rules (MANDATORY)

**CRITICAL**: All cross-subsystem communication must flow through ABX-Runes capability contracts. Direct imports between `abx/` and `abraxas/` are forbidden.

### DO NOT Do This (Coupling Violation) ❌

```python
# ❌ WRONG - Direct import across subsystem boundary
from abraxas.oracle.v2.pipeline import run_oracle
from abraxas.memetic.metrics_reduce import reduce_provenance_means

result = run_oracle(observations, config)
means = reduce_provenance_means(profiles)
```

### DO This Instead (Rune Contract) ✅

```python
# ✅ CORRECT - Via capability contract
from abraxas.runes.capabilities import load_capability_registry
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext

# Create invocation context
ctx = RuneInvocationContext(
    run_id="RUN-001",
    caller="abx.mymodule",
    environment="production"
)

# Invoke oracle capability
oracle_result = invoke_capability(
    capability="oracle.v2.run",
    inputs={
        "run_id": "RUN-001",
        "observations": observations,
        "config": config,
        "seed": 42  # For determinism
    },
    ctx=ctx,
    strict_execution=True
)

# Extract results with provenance
oracle_output = oracle_result["oracle_output"]
provenance = oracle_result["provenance"]
```

### Allowed Exceptions

Only these `abraxas.*` imports are allowed in `abx/`:
- ✅ `abraxas.runes.*` - Rune system itself (capabilities, invoke, ctx, registry)
- ✅ `abraxas.core.provenance` - Provenance utilities (canonical_envelope, hash_canonical_json)
- ✅ Test files only: Any import for testing purposes

**All other imports must use capability contracts.**

### How to Add a New Capability

1. **Create JSON schemas** for inputs/outputs in `schemas/capabilities/`
2. **Create rune adapter** in the subsystem (thin wrapper, no core logic changes)
3. **Register capability** in `abraxas/runes/registry.json`
4. **Add golden test** proving determinism
5. **Update coupling lint** to verify violation count decreased

See `docs/migration/abx_runes_coupling.md` for detailed migration guide.

---

## Getting Help

### When Working on Tasks

1. **Check existing documentation**: README files, specs, guides
2. **Examine similar code**: Find patterns in existing modules
3. **Run tests**: Ensure changes don't break existing functionality
4. **Verify determinism**: Same inputs should produce same outputs
5. **Add provenance**: Include SHA-256 hashes for traceability
6. **Use capability contracts**: Never directly import across subsystems

### Best Practices for AI Assistants

1. **Read before modifying**: Always read files before editing
2. **Follow conventions**: Match existing code style and patterns
3. **Test changes**: Run tests to verify functionality
4. **Document changes**: Update relevant documentation
5. **Preserve determinism**: Maintain reproducible behavior
6. **Include provenance**: Track all transformations with hashes
7. **Avoid over-engineering**: Keep solutions simple and focused
8. **No security vulnerabilities**: Check for injection, XSS, etc.
9. **Respect ABX-Runes boundaries**: Use capability contracts, not direct imports

---

**End of CLAUDE.md**

*This document is maintained as part of the Abraxas project. When in doubt, refer to canonical documentation in `docs/canon/` and existing code patterns.*
