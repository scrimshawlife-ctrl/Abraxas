# Abraxas Active Plan Surface

This file is the canonical append-first execution queue for the Abraxas AI OS unification program.

Detailed architecture and sequencing:

- [`docs/ai-os/AI_OS_CONTRACT.md`](docs/ai-os/AI_OS_CONTRACT.md)
- [`docs/ai-os/ROADMAP.md`](docs/ai-os/ROADMAP.md)
- [`docs/ai-os/JCODE_EXECUTION_PLAN.md`](docs/ai-os/JCODE_EXECUTION_PLAN.md)

## Operating Contract

- Preserve existing deterministic runtime, governance, proof, validation, replay, and `NOT_COMPUTABLE` semantics.
- Reuse existing infrastructure before creating new modules.
- Reduce ambiguity before increasing feature scope.
- Keep canonical state separate from derivative projections.
- Treat external calls and side effects as governed capabilities.
- Complete one vertical slice before broad migration.
- Record completed work with evidence links, tests, and remaining gaps.
- Never infer promotion, readiness, or closure from documentation alone.

## Strategic Objective

Unify the existing Abraxas architecture into a governed AI operating system with one canonical lifecycle:

```text
operator intent
→ session and workspace context
→ deterministic task graph
→ policy and permission evaluation
→ capability resolution
→ governed execution
→ events and checkpoints
→ artifacts and validation
→ delivery
→ memory and continuity commit
→ operator projection
```

## Active Queue

### P0 — AI OS Repository Mapping and Ownership

- **Status:** READY
- **Intent:** identify all existing implementation surfaces that should be reused, adapted, wrapped, projected, retained for compatibility, or archived.
- **Required output:** `docs/ai-os/JCODE_REPOSITORY_MAP.md`.
- **Definition of done:**
  - canonical entrypoints inventoried;
  - runes, scripts, adapters, connectors, model calls, agents, APIs, and workflows classified;
  - direct cross-subsystem calls mapped;
  - schema, hashing, artifact, ledger, receipt, policy, task graph, continuity, and projection helpers mapped;
  - ownership ambiguity explicitly resolved or marked `NOT_COMPUTABLE`.

### P0 — Kernel Boundary ADR

- **Status:** QUEUED
- **Intent:** define package ownership and dependency direction for `abx_os` without changing existing runtime authority.
- **Required output:** `docs/adr/ADR-AI-OS-001-kernel-boundary.md`.
- **Definition of done:**
  - `abx_os` responsibilities fixed;
  - existing `abx`, `abraxas`, `abx_familiar`, `.abraxas`, schemas, and projection roles documented;
  - import and authority boundaries testable;
  - no broad package relocation required.

### P0 — AI OS Foundation Schemas

- **Status:** QUEUED
- **Intent:** add machine-readable contracts for the minimum canonical AI OS objects.
- **Scope:**
  - `Principal.v1`;
  - `SessionEnvelope.v1`;
  - `WorkspaceState.v1`;
  - `OperatorIntent.v1`;
  - `TaskGraphIR.v1`;
  - `ProcessRun.v1`;
  - `CapabilityManifest.v1`;
  - `SystemEvent.v1`;
  - `Checkpoint.v1`;
  - `ArtifactEnvelope.v1`;
  - `DeliveryPack.v1`.
- **Definition of done:** positive and negative fixtures, schema-index registration, stable semantic digests, explicit reason-code and `NOT_COMPUTABLE` semantics.

### P0 — TaskGraphIR.v1 Compatibility Layer

- **Status:** QUEUED
- **Intent:** extend the current deterministic task representation into an executable process graph without breaking v0 consumers.
- **Definition of done:**
  - deterministic nodes and edges;
  - capability, data, policy, budget, approval, checkpoint, retry, timeout, and rollback references;
  - v0-to-v1 adapter;
  - cycle and missing-reference rejection;
  - stable topological ordering and semantic hash tests.

### P0 — Capability Registry Foundation

- **Status:** QUEUED
- **Intent:** establish one public execution abstraction for runes, tools, scripts, adapters, models, connectors, and delegated operations.
- **Initial adapters:**
  - `model.infer.mock.v1`;
  - `repo.inspect.local_read.v1`.
- **Definition of done:**
  - unregistered capability execution blocked;
  - grants checked before invocation;
  - side-effect class, timeout, retry, schemas, and receipts enforced;
  - invocation receipts linked to session, workspace, process, task, and artifact IDs.

### P0 — Process, Event, and Checkpoint Spine

- **Status:** QUEUED
- **Intent:** make runtime state reconstructable and resumable.
- **Definition of done:**
  - canonical process state machine;
  - append-only system events;
  - state reconstruction from events;
  - idempotent checkpoint resume;
  - cancellation and `NOT_COMPUTABLE` terminal paths;
  - digest mismatch detection.

### P0 — Canonical AI OS Vertical Slice

- **Status:** BLOCKED_BY_PREVIOUS_P0
- **Intent:** prove one complete lifecycle through a single kernel entrypoint.
- **Required flow:**

```text
request
→ session
→ intent
→ TaskGraphIR.v1
→ policy and grants
→ mock model capability
→ read-only repository capability
→ checkpoint
→ artifact registration
→ validation
→ DeliveryPack.v1
→ workspace/continuity commit
→ operator projection
```

- **Definition of done:**
  - one command or test executes the full path;
  - all artifacts schema-valid;
  - replay produces equivalent semantic digests;
  - resume does not duplicate completed capability calls;
  - no live model or external network required by the deterministic test lane;
  - existing proof and governance tests do not regress.

### P1 — Capability Convergence

- **Status:** FUTURE
- **Intent:** wrap high-value existing execution surfaces and redirect legacy entrypoints through the canonical capability layer.
- **Definition of done:** new public functionality cannot bypass capability registration; compatibility shims are explicit; direct-call lint is enforced.

### P1 — Persistent Workspace and Memory

- **Status:** FUTURE
- **Intent:** preserve governed operational context across sessions.
- **Definition of done:** persistent workspace store, separated memory namespaces, provenance-backed writes, retention and supersession semantics, continuity cursor, import/export bundle.

### P1 — Identity, Permissions, and Secret References

- **Status:** FUTURE
- **Intent:** move governance from subsystem-only boundaries to runtime principal and capability authorization.
- **Definition of done:** principal roles, capability grants, delegated authority limits, opaque secret references, and approval records.

### P1 — Scheduler and Agent Runtime

- **Status:** FUTURE
- **Intent:** support bounded long-running and delegated work.
- **Definition of done:** dependency scheduling, concurrency limits, retries, timeouts, cancellation, budgets, approval gates, agent parent/child lineage, checkpoints, and termination receipts.

### P2 — Unified Operator Console

- **Status:** CONDITIONAL
- **Intent:** converge `webpanel`, `server`, `client`, and `shared` onto canonical AI OS projections after the vertical slice is complete.
- **Definition of done:** workspace, process, task graph, capability, agent, approval, artifact, event, memory, provenance, and recovery views all trace to canonical records.

### P2 — Plugin and Automation Ecosystem

- **Status:** FUTURE
- **Intent:** make the AI OS extensible without weakening governance.
- **Definition of done:** installable capability bundles, dependency and permission declarations, migration hooks, reversible installation, scheduled/conditional automation, and plugin trust tiers.

## Existing Runtime Closure Work — Carryover

The following work remains valid and should be integrated where it supports the AI OS vertical slice:

### Validator Artifact Linkage Closure

- Complete rune execution linkage into validator and ledger surfaces.
- Preserve explicit unresolved reasons when linkage is incomplete.

### Proof-Run Correlation Pointer Completion

- Propagate correlation-pointer set semantics across execution artifacts.
- Preserve `present`, `empty`, and `unresolved` states.

### Rune-Aware Validator Surfacing

- Surface rune identifiers and phase-aware outcomes in validator and operator summaries.

### Execution Artifact Generation Integration

- Route execution-producing paths through shared schema-aligned artifact envelopes.

### Snapshot Lookup and Synthesis Readiness

- Resolve blocker precedence for bound exact-match cases.
- Broaden deterministic real-case validation.
- Align derivable metrics with binding-health semantics.

These items are supporting infrastructure, not a substitute for the canonical AI OS session, process, capability, event, workspace, and delivery lifecycle.

## Phase Gates

### Phase 0 Gate

- repository map complete;
- ownership ADR accepted;
- no unresolved P0 ownership collision.

### Phase 1 Gate

- foundation schemas validated;
- package skeleton import-safe;
- dependency boundaries enforced.

### Phase 2 Gate

- vertical slice complete;
- deterministic replay passes;
- checkpoint resume passes;
- capability and policy bypass tests pass;
- operator projection reads canonical records only.

### Expansion Gate

Workspace persistence, real models, scheduler, agents, memory, and UI expansion may proceed only after the Phase 2 gate is satisfied.

## Required Validation

Use repository-native commands and record exact results:

```bash
pytest -q
make dependency-check
make developer-readiness
make governance-lint
make ts-canonical-check
```

Classify failures as:

```text
NEW_REGRESSION
PRE_EXISTING_FAILURE
ENVIRONMENT_BLOCKED
NOT_COMPUTABLE
```

## Explicit Non-Goals Before Vertical-Slice Closure

- unrestricted autonomous execution;
- broad UI redesign;
- distributed scheduling;
- plugin marketplace;
- self-modifying kernel behavior;
- migration of every legacy script;
- new symbolic subsystems not required by the first vertical slice.

## Completed

- 2026-07-30 — Defined canonical AI OS contract, phased roadmap, JCode implementation plan, README posture, documentation routing, and active execution queue on `agent/ai-os-unification-docs`.
- Historical completed runtime, governance, validator, proof, correlation, large-run, Notion-sync, Oracle Signal Layer, and operator-surface work remains preserved in git history and repository artifacts.
