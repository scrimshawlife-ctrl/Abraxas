# Abraxas AI OS Roadmap

**Roadmap status:** Active direction  
**Execution rule:** Reduce architectural ambiguity before expanding feature scope.

## Current Baseline

### Implemented or strong

- deterministic runtime and hash-based artifacts;
- ABX-Runes typed execution, receipts, replay, and rollback primitives;
- governance registries and subsystem metadata;
- validation, invariance, readiness, and promotion-policy surfaces;
- continuity-ledger and task-graph prototypes;
- operator projection and web surfaces;
- sandboxed adaptive experimentation.

### Partial

- task/process intermediate representation;
- continuity and stabilization runtime;
- capability abstraction;
- operator console consistency;
- artifact addressing and linkage;
- policy-to-projection wiring.

### Missing as canonical AI OS services

- workspace model;
- session lifecycle;
- unified process orchestrator;
- event bus and reconstructable state machine;
- real scheduler;
- model routing abstraction;
- principal-level permissions and secret brokerage;
- governed agent lifecycle;
- scoped persistent memory;
- canonical artifact filesystem;
- plugin installation and versioning.

## Phase 0 — Canonicalization and Inventory

**Objective:** Establish one authoritative AI OS boundary without changing runtime authority.

### Deliverables

- `docs/ai-os/AI_OS_CONTRACT.md` accepted as canonical direction.
- Machine-readable schema backlog for all canonical AI OS objects.
- Complete inventory of current executable surfaces:
  - runes;
  - scripts;
  - CLI commands;
  - adapters;
  - model calls;
  - connectors;
  - agents;
  - server endpoints;
  - workflows.
- Classification for each surface:
  - canonical kernel service;
  - capability adapter;
  - projection;
  - experimental;
  - compatibility shim;
  - archival candidate.
- Architecture decision record for package ownership and dependency direction.

### Exit criteria

- No major execution surface remains unclassified.
- Direct cross-subsystem calls are mapped.
- Canonical ingress and egress are explicitly named.
- Existing tests remain unchanged or stronger.

## Phase 1 — Contracts and Skeleton

**Objective:** Create the AI OS package and schema spine without broad migrations.

### Deliverables

- `abx_os/` package skeleton.
- Initial schemas:
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
- Schema registry entries and compatibility rules.
- Deterministic IDs, canonical JSON, and digest helpers reused from existing infrastructure.
- Dependency boundary tests preventing `abx_os` from bypassing governance and receipt layers.

### Exit criteria

- All schemas validate positive and negative fixtures.
- Package imports are acyclic.
- No production execution path has changed yet.

## Phase 2 — Canonical Vertical Slice

**Objective:** Prove one complete AI OS lifecycle.

### Required flow

```text
request
→ session
→ intent
→ task graph
→ policy
→ capability resolution
→ model call
→ repository read
→ checkpoint
→ artifact
→ validation
→ delivery
→ continuity commit
→ projection
```

### Deliverables

- `abx_os.kernel.run()` or equivalent single canonical entrypoint.
- One model capability adapter.
- One read-only GitHub/repository capability adapter.
- Process state machine and event emission.
- Append-only event ledger.
- Checkpoint/resume for the slice.
- Artifact registration with lineage.
- Delivery assembly.
- Operator projection endpoint/view.
- Deterministic replay test using stable fixtures and mocked external observations.

### Exit criteria

- Same canonical inputs yield the same internal digests.
- External observations are recorded and replayable.
- Resume does not duplicate completed side effects.
- Missing evidence resolves to `NOT_COMPUTABLE`.
- Existing proof and governance tests pass.

## Phase 3 — Capability Convergence

**Objective:** Make capabilities the only public execution abstraction.

### Deliverables

- Canonical capability registry.
- Wrappers for high-value existing runes, scripts, adapters, and connectors.
- Capability permissions, side-effect classes, retries, timeouts, and receipts.
- Compatibility shims for legacy CLI/script entrypoints.
- Direct-call lint or dependency test.
- Capability conformance test kit.

### Exit criteria

- New functionality cannot bypass the registry.
- Legacy entrypoints delegate to canonical capabilities or are explicitly shadow-only.
- Capability receipts link to process, session, workspace, and artifacts.

## Phase 4 — Workspace, Memory, and Identity

**Objective:** Support persistent governed work across sessions.

### Deliverables

- Persistent `WorkspaceState.v1` store.
- Principal, role, and capability-grant model.
- Opaque secret-reference broker.
- Memory namespaces and write arbitration.
- Supersession, retention, and deletion semantics.
- Workspace import/export bundle.
- Continuity cursor and recovery tests.

### Exit criteria

- A user can close and reopen a workspace without losing canonical state.
- Memory provenance is inspectable.
- Secrets never appear in task graphs, artifacts, or model-visible context by default.

## Phase 5 — Scheduler and Agent Runtime

**Objective:** Run long-lived and delegated work safely.

### Deliverables

- Dependency-aware scheduler.
- Bounded parallelism.
- Time, token, cost, and tool budgets.
- Retry, timeout, cancellation, and dead-letter semantics.
- Approval gates.
- `AgentManifest.v1` and `AgentInstance.v1`.
- Parent/child lineage, mailbox, checkpoint, and termination receipt.
- Multi-agent shared-state conflict policy.

### Exit criteria

- Agent work is resumable and bounded.
- No child agent can exceed parent grants.
- Concurrent updates are deterministic or explicitly conflict-marked.

## Phase 6 — Unified Operator Console

**Objective:** Present the AI OS as one coherent operating environment.

### Deliverables

- Workspace switcher.
- Intent/command surface.
- Process graph and queue.
- Capability and agent activity views.
- Approval inbox.
- Artifact explorer.
- Event and provenance timeline.
- Memory inspector.
- Replay, resume, cancel, and rollback controls.
- Resource accounting.

### Exit criteria

- Every visible state traces to canonical artifacts or events.
- No projection surface independently derives authority.
- Webpanel/server/client/shared contracts converge on one view model.

## Phase 7 — Plugin and Automation Ecosystem

**Objective:** Make Abraxas extensible without weakening the kernel.

### Deliverables

- Installable plugin manifest.
- Capability bundles with dependency and permission declarations.
- Version compatibility and migration hooks.
- Installation, upgrade, disable, and uninstall receipts.
- Scheduled and condition-based automation service.
- Plugin trust tiers and sandbox policy.

### Exit criteria

- Plugins cannot silently add permissions or bypass canonical execution.
- Install and uninstall are reversible and provenance-backed.

## Priority Queue

### P0

1. Accept AI OS contract and package ownership ADR.
2. Inventory executable surfaces and direct calls.
3. Define canonical schemas.
4. Build the vertical slice.
5. Add process/event/checkpoint tests.

### P1

1. Capability convergence.
2. Workspace persistence.
3. Memory namespaces.
4. Principal permissions and secret references.
5. Scheduler and agent lifecycle.

### P2

1. Unified operator console.
2. Plugin packaging.
3. Automation daemon.
4. Resource accounting and operational dashboards.

## Explicit Non-Goals Until Phase 2 Closes

- broad UI redesign;
- unrestricted autonomous execution;
- large-scale plugin marketplace;
- distributed multi-node scheduling;
- self-modifying kernel behavior;
- migration of every legacy script;
- new symbolic subsystems not required by the vertical slice.
