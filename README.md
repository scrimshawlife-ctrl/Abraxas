# Abraxas

Deterministic runtime, proof surfaces, and governance tooling for ABX/Abraxas execution closure.

---

## Start Here

If you are new, start in this order:

1. **This file** — repo identity, maturity boundaries, and operator quickstart.
2. **Docs index** — [docs/README.md](docs/README.md) for canonical vs operational vs archival documentation map.
3. **Governance root** — `.abraxas/` plus `.abraxas/registries/expected_subsystems.yaml`.
4. **Gap closure deterministic path** — `scripts/run_gap_closure_cycle.py` → `scripts/validate_gap_closure_artifacts.py` → `scripts/log_gap_closure_invariance.py`.
5. **Verification surface** — `pytest tests/gap_closure`.

---

## Overview

Abraxas is a multi-surface repository with:

- **Canonical Python runtime and policy/governance lane** (`abx/`, `abraxas/`, `.abraxas/`).
- **Operator and projection surfaces** (`webpanel/`, `server/`, `client/`, `shared/`).
- **Run scripts, audits, and report emitters** (`scripts/`).
- **Schemas, contracts, and artifacts** (`schemas/`, `docs/`, `out/`, `artifacts_*`).

Current repository state includes an additive `gap_closure_v1` path for deterministic run artifacts, validation, invariance logging, stabilization reporting, and dry-run Notion sync tooling. (No canon-active promotion claims are minted by these surfaces.) [.abraxas/subsystems/gap_closure_v1.yaml](.abraxas/subsystems/gap_closure_v1.yaml)

---

## Current Maturity (Truth-Scoped)

| Area | Status | Evidence |
|---|---|---|
| Deterministic gap closure runtime + validator path | **Implemented** | `scripts/run_gap_closure_cycle.py`, `scripts/validate_gap_closure_artifacts.py`, `abraxas/runes/gap_closure/*` |
| Invariance logging and stabilization synthesis | **Implemented** | `scripts/log_gap_closure_invariance.py`, `scripts/run_gap_closure_stabilization_report.py` |
| Notion sync path | **Implemented (operator-controlled)** | `scripts/sync_invariance_to_notion.py` with `--dry-run` and live token gate |
| Promotion execution | **Partial / gated** | Promotion recommendation remains `HOLD`/`BLOCK` in gap-closure flow |
| Federated or live oracle wiring for gap closure | **Experimental / not part of this path** | No mandatory live oracle dependency in gap closure scripts |
| Long-horizon closure and release packaging workflows | **Planned / evolving** | See `docs/` + many audit/report scripts in `scripts/` |

### Implemented

- Canonical JSON + SHA256 deterministic artifacts.
- Artifact validation with explicit `PASS` / `FAIL` / `NOT_COMPUTABLE`.
- Invariance rows + local ledger progression state logic.
- Stabilization report synthesis from artifact + validator + invariance evidence.
- Dry-run Notion payload generation and live-mode token gating.

### Partial

- Stabilization readiness can remain `partial` when invariance thresholds are not met (for example, only `UNCHECKED` rows available).  
- Promotion is intentionally non-promotive (`HOLD`/`BLOCK` only) in this path.

### Experimental

- Operator/developer script surfaces in `scripts/` are broad and heterogeneous; many are audit/report experiments beyond the minimal canonical gap-closure spine.

### Planned

- Continued convergence of audit/report scripts into clearer operator runbooks and tighter release-readiness packaging.

---

## Architecture at a Glance

### Canonical runtime spine (repository-declared)

`ingest -> rune invoke -> artifact emit -> ledger linkage -> validator-visible proof -> operator projection -> attestation`

Key canonical entry points:

- `python -m abx.cli proof-run --run-id <RUN_ID>`
- `python -m abx.cli promotion-check --run-id <RUN_ID>`
- `python -m abx.cli promotion-policy --run-id <RUN_ID>`

### Gap closure additive spine (`RUN-GAP-FIRST-0001` path)

1. `scripts/run_gap_closure_cycle.py`  
2. `scripts/validate_gap_closure_artifacts.py`  
3. `scripts/log_gap_closure_invariance.py`  
4. `scripts/run_gap_closure_stabilization_report.py`  
5. `scripts/sync_invariance_to_notion.py --dry-run`

---

## Repository Map (operator-centric)

| Path | Purpose |
|---|---|
| `.abraxas/` | Governance policy, registries, subsystem manifests, release templates/scripts |
| `abx/` | Canonical ABX CLI/runtime orchestration surfaces |
| `abraxas/` | Domain/runtime modules including `abraxas/runes/gap_closure` |
| `scripts/` | Operational scripts (runtime, audit, validation, reporting, sync) |
| `schemas/` | JSON schemas (gap closure + bridge contracts and more) |
| `tests/` | Python tests (`tests/gap_closure` covers the gap closure lane) |
| `docs/` | Specs, canonical runtime docs, artifact notes |
| `webpanel/`, `server/`, `client/`, `shared/` | Operator/product projection surfaces |
| `out/`, `artifacts_seal/`, `artifacts_gate/` | Emitted reports, run artifacts, validator outputs |

---

## Key Scripts (Gap Closure + Validation/Governance)

### Gap closure runtime scripts

- `scripts/run_gap_closure_cycle.py`  
  Emits run/projection/validation artifacts and validator + ledger surfaces.

- `scripts/validate_gap_closure_artifacts.py`  
  Re-validates generated artifacts for a run and writes validator output.

- `scripts/log_gap_closure_invariance.py`  
  Reads run artifacts, compares hashes against local history, appends invariance rows.

- `scripts/run_gap_closure_stabilization_report.py`  
  Synthesizes stabilization report from artifact + validator + invariance + ledger evidence.

- `scripts/sync_invariance_to_notion.py`  
  Converts invariance rows to Notion payloads; supports `--dry-run` without token.

### Governance / guardrail scripts

- `.abraxas/scripts/preflight.py`
- `.abraxas/scripts/registry_consistency.py`
- `.abraxas/scripts/governance_lint.py`
- `.abraxas/scripts/release_readiness.py`

---

## Validation and Governance Surfaces

- Subsystem registry: `.abraxas/registries/expected_subsystems.yaml`
- Gap subsystem manifest: `.abraxas/subsystems/gap_closure_v1.yaml`
- Governance templates + ledgers: `.abraxas/templates/`, `.abraxas/ledger/`
- Documentation index: [docs/README.md](docs/README.md)
- Canon docs:
  - [docs/CANONICAL_RUNTIME.md](docs/CANONICAL_RUNTIME.md)
  - [docs/VALIDATION_AND_ATTESTATION.md](docs/VALIDATION_AND_ATTESTATION.md)
  - [docs/SUBSYSTEM_INVENTORY.md](docs/SUBSYSTEM_INVENTORY.md)
  - [docs/RELEASE_READINESS.md](docs/RELEASE_READINESS.md)

---

## Install

### Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Optional dev extras:

```bash
pip install -e ".[dev]"
```

### JavaScript/TypeScript surfaces (if needed)

```bash
npm install
```

---

## Quickstart

### Canonical ABX CLI path

```bash
python -m abx.cli proof-run --run-id RUN-DEMO-001
python -m abx.cli promotion-check --run-id RUN-DEMO-001
python -m abx.cli promotion-policy --run-id RUN-DEMO-001
```

### Gap closure path (current additive lane)

```bash
python scripts/run_gap_closure_cycle.py --run-id RUN-GAP-FIRST-0001 --mode sandbox --workspace-only
python scripts/validate_gap_closure_artifacts.py --run-id RUN-GAP-FIRST-0001
python scripts/log_gap_closure_invariance.py --run-id RUN-GAP-FIRST-0001 --mode sandbox --workspace-scope workspace_only
python scripts/run_gap_closure_stabilization_report.py --run-id RUN-GAP-FIRST-0001
python scripts/sync_invariance_to_notion.py --run-id RUN-GAP-FIRST-0001 --dry-run
```

Run gap-closure tests:

```bash
pytest tests/gap_closure
```

---

## Contributor / Operator Path

If you are new and want a deterministic first contribution:

1. Read governance contract and subsystem manifest:
   - `AGENTS.md`
   - `.abraxas/subsystems/gap_closure_v1.yaml`
2. Run deterministic checks:
   - `pytest tests/gap_closure`
   - `python scripts/run_gap_closure_cycle.py --run-id RUN-GAP-FIRST-0001 --mode sandbox --workspace-only`
3. Validate and inspect:
   - `python scripts/validate_gap_closure_artifacts.py --run-id RUN-GAP-FIRST-0001`
   - `python scripts/run_gap_closure_stabilization_report.py --run-id RUN-GAP-FIRST-0001`
4. Confirm promotion posture remains non-promotive (`HOLD`/`BLOCK`) in emitted evidence.

Recommended governance guardrails:

```bash
python scripts/run_governance_lint.py
make registry-check
```

---

## Repo Presentation Notes

- This repo intentionally contains both canonical and experimental/operator surfaces.
- When in doubt, prioritize:
  1. runtime artifact evidence,
  2. validator output,
  3. governance policy/registry constraints,
  4. derivative projections.

---

## License

A root `LICENSE` file is not currently present. `package.json` declares `MIT` for TypeScript package scope only; verify top-level licensing before redistribution.
