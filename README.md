# Abraxas

**Abraxas is a multi-surface repository for deterministic symbolic execution, governance-aware run artifacts, and operator-facing interfaces.** It combines a large Python runtime (ABX/AAL logic, runes, audit scripts, webpanel) with a TypeScript full-stack app (Express + React) and supporting schema/ledger surfaces.

## Overview

This repository is best understood as a **hybrid workspace** with multiple active execution paths rather than a single app:

- **Python core surfaces** (`abraxas/`, `abx/`, `aal_core/`, `abx_familiar/`) for deterministic pipelines, rune invocation, CLI operations, and artifact-linked governance flows.
- **Python webpanel** (`webpanel/`) exposing FastAPI routes/templates for operator workflows, run inspection, compare/export, and governance actions.
- **TypeScript app stack** (`server/`, `client/`, `shared/`) providing an Express API + React UI with auth, dashboards, and governance/artifact endpoints.
- **Operational scripts and artifacts** (`scripts/`, `artifacts_seal/`, `out/`, `docs/`) for audits, gates, attestations, and run-linked outputs.

## Why It Exists

From the code and docs in this repo, Abraxas is built to support **deterministic decisioning and reviewable execution**:

- enforce explicit run contracts,
- preserve traceable lineage (run IDs, artifacts, linkage fields),
- provide operator-visible routing/governance surfaces,
- and emit machine-checkable artifacts suitable for validation and audit.

## Features

### Implemented (high-confidence from wired code + commands)

- **Deterministic rune execution envelope (AAL core)** with schema-aligned fields including `run_id`, `artifact_id`, `rune_id`, `status`, `inputs/outputs`, provenance, and correlation/ledger pointers.
- **Rune catalog + schema surfaces** in `aal_core` for registry and artifact validation.
- **ABX CLI surface** with subcommands for doctor/up/smoke/acceptance, drift/watchdog/update, overlay management, and governance/apply/log operations.
- **Oracle API (FastAPI)** with endpoints for lexicon registration and deterministic oracle runs plus websocket streaming bridge.
- **Webpanel FastAPI app** with compare/export/governance/operator/run routes and template-backed UI pages.
- **TypeScript full-stack app** (Express + React + Vite) with auth wiring, health endpoints, dashboard/governance/artifact routes, and shared schema usage.
- **Large audit/gate script inventory** in `scripts/` including baseline enforcement, runbook checks, attestation, closure readiness, and many governance scorecards.
- **Automated CI canary workflow** (`.github/workflows/abx_familiar_canary.yml`) running governance gates + focused tests.

### Partial / experimental / scaffolded (present but not consistently production-wired)

- **Mixed-readiness docs and entrypoints**: root docs reference different operational narratives (oracle API, Orin boot spine, operator console refinement).
- **Placeholder or transitional quality surfaces**: `make lint` is explicitly a placeholder, and some docs mention license file not currently present in repo root.
- **Broad subsystem footprint** across many packages/modules where maturity appears uneven (some strongly tested/wired, others primarily structural).
- **Node + Python dual-stack operability** appears active, but end-to-end unified onboarding is not fully consolidated in a single canonical runbook.

## Architecture

At a high level, the repository follows:

`Input/context -> deterministic processing/rune wrappers -> artifact envelope -> validator/operator surfaces`

Key layers:

1. **Execution + contracts (Python)**
   - `aal_core/runes/executor.py` defines normalized rune artifact emission.
   - `aal_core/schemas/rune_execution_artifact.v1.json` defines required envelope contract.
   - `aal_core/runes/catalog.v0.yaml` tracks registered rune IDs and contract refs.

2. **Runtime + CLI (Python)**
   - `abx/cli.py` is the major CLI entrypoint with many operational subcommands.
   - `abraxas/runes/invoke.py` handles rune/capability invocation, schema checks, and ledger records.

3. **Service/API surfaces**
   - `abraxas/api/app.py` + `abraxas/api/routes.py`: FastAPI oracle + lexicon API and websocket stream.
   - `webpanel/app.py` + `webpanel/routes/*`: operator/governance/run/export UI routes.
   - `server/index.ts` + `server/routes.ts`: TypeScript API server and route registration.

4. **UI surfaces**
   - `client/src/*`: React application shell, page/component routing, dashboard panels.
   - `webpanel/templates/*`: server-rendered HTML templates for panel routes.

5. **Validation + evidence**
   - `tests/`, `webpanel/test_*.py`, `abx_familiar/tests/`, and CI canary workflow.
   - `scripts/` and `artifacts_seal/`/`out/` for run-linked validation outputs.

## Repository Layout

```text
.
├── aal_core/                 # rune catalog, schema contracts, execution envelope wrapper
├── abraxas/                  # core Python modules (api, oracle, runes, metrics, overlays, etc.)
├── abx/                      # ABX runtime + major CLI + governance/ops modules
├── abx_familiar/             # familiar canary/runtime surfaces and focused tests
├── webpanel/                 # FastAPI web panel + templates + panel tests
├── server/                   # TypeScript Express server routes/integrations
├── client/                   # React frontend (Vite)
├── shared/                   # shared TS schemas/types
├── scripts/                  # extensive audit/gate/attestation scripts
├── tests/                    # broad Python test suite
├── docs/                     # architecture/audit/spec/plan docs
└── artifacts_seal/, out/     # generated artifacts and validator-facing outputs
```

## Getting Started

> ⚠️ This repo has multiple runtime surfaces. Start with one path first.

### Prerequisites

- Python 3.8+
- Node.js + npm (for TS app stack)

### Python install (editable)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Optional extras:

```bash
pip install -e ".[dev]"
pip install -e ".[server]"
```

### Node install

```bash
npm install
```

### Environment

A starter env file is available at `.env.example` (OAuth/session keys, DB URL, governance + ALIVE secrets).

## Run, Build, Test, Validate

Only commands evidenced in this repo are listed below.

| Purpose | Command |
|---|---|
| Show ABX CLI help | `python -m abx.cli -h` |
| Run oracle CLI help | `python -m abraxas.oracle.cli -h` |
| Start Python webpanel (dev) | `python -m webpanel.run` |
| Start oracle FastAPI app | `uvicorn abraxas.api.app:app --reload` |
| Python test suite via Make | `make test` |
| Focused webpanel refinement test | `pytest -q webpanel/test_operator_console_refinement.py` |
| Familiar canary tests | `pytest abx_familiar/tests` |
| TypeScript dev server | `npm run dev` |
| TypeScript build | `npm run build` |
| TypeScript type check | `npm run check` |
| TypeScript tests | `npm run test` |
| Artifact seal flow | `make seal` |
| Artifact validation | `make validate` |
| Unified attestation | `make attest RUN_ID=<id>` |

## Usage

### 1) Python CLI operations

Use `abx`/`python -m abx.cli` for operational commands:

```bash
python -m abx.cli doctor
python -m abx.cli smoke
python -m abx.cli acceptance
```

### 2) Oracle API path

Run API and call endpoints:

- `POST /api/lexicons/register`
- `POST /api/oracle/run`
- `GET /api/oracle/{artifact_id}`
- `WS /ws`

### 3) Webpanel path

Run `python -m webpanel.run`, then open panel routes served by `webpanel/app.py` registrations (index/operator/runs/compare/export/governance).

### 4) TypeScript full-stack path

Use `npm run dev` to launch the Express + Vite stack (`server/index.ts` + client app).

## Development

### Where to start reading

1. `aal_core/runes/executor.py` and `aal_core/schemas/rune_execution_artifact.v1.json`
2. `abx/cli.py`
3. `abraxas/runes/invoke.py`
4. `webpanel/app.py` and `webpanel/routes/`
5. `server/routes.ts` and `client/src/App.tsx`

### Quality surfaces visible in-repo

- Python tests under `tests/`, `webpanel/`, and `abx_familiar/tests/`
- CI canary workflow running governance gates + selected regression suites
- Deterministic artifact/gate scripts in `scripts/`

## Project Status

Current state appears to be **active, multi-surface development** with strong deterministic/governance intent and broad module coverage.

- There are many implemented execution surfaces and tests.
- There is also clear evidence of ongoing evolution (multiple READMEs, overlapping docs, mixed maturity across modules).
- Treat this repo as **powerful but complex**: great for contributors who can navigate layered systems; harder for first-time setup without a narrowed path.

## Highlights / Design Notes

- Determinism and contract surfaces are explicit (schema + envelope + registry).
- Governance/audit culture is deeply represented in scripts and CI checks.
- The repository embraces both operator UX and machine-auditable lineage outputs.

## Contributing

No root `CONTRIBUTING.md` was found. A practical contribution path is:

1. pick one subsystem (e.g., `webpanel`, `aal_core`, `server/client`),
2. run only that subsystem’s relevant tests,
3. preserve deterministic artifact contracts when touching execution paths,
4. keep patches incremental and scope-local.

## License

- Root `LICENSE` file is not present in this repository snapshot.
- `package.json` declares `MIT` for the TypeScript package.
- Confirm intended top-level licensing before external redistribution.
