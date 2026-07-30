# Abraxas AI OS Contract

**Status:** Proposed canonical direction  
**Authority:** Architecture and implementation contract; non-promotive until schemas, subsystem manifests, tests, and operator approval are complete.

## 1. Purpose

Abraxas is evolving from a governed deterministic execution framework into a governed AI operating system built from the repository's existing runtime, rune, artifact, ledger, validation, governance, and operator infrastructure.

The AI OS does not replace the existing architecture. It unifies it behind one canonical lifecycle:

```text
operator intent
→ session and workspace context
→ deterministic task graph
→ policy and permission evaluation
→ capability resolution
→ governed execution
→ checkpoints and artifacts
→ validation and provenance
→ delivery
→ memory and continuity commit
```

## 2. Non-Negotiable Invariants

1. **Determinism where computable.** Canonical transforms, identifiers, hashes, ordering, and state transitions must be reproducible.
2. **Explicit uncertainty.** Missing or insufficient evidence resolves to `NOT_COMPUTABLE`, not fabricated completion.
3. **Provenance by default.** Every process, capability invocation, artifact, memory write, and delivery must carry source and lineage information.
4. **Governed side effects.** External calls, mutations, writes, deployments, and credential use require explicit capability grants and policy evaluation.
5. **Canonical versus projection separation.** User interfaces and summaries may project canonical state but may not redefine it.
6. **Recoverability.** Long-running work must support checkpoints, replay, cancellation, bounded retry, and compensating rollback where possible.
7. **No hidden execution surfaces.** Every executable surface must be registered as a capability or classified as private implementation.
8. **No autonomous authority escalation.** Agents and adaptive systems may propose actions but may not expand their own permissions.

## 3. Canonical Objects

| Domain | Canonical object | Responsibility |
|---|---|---|
| Identity | `Principal.v1` | Human, agent, or service identity |
| Session | `SessionEnvelope.v1` | Interactive execution boundary |
| Workspace | `WorkspaceState.v1` | Persistent project and operational state |
| Intent | `OperatorIntent.v1` | Normalized requested outcome and constraints |
| Planning | `TaskGraphIR.v1` | Deterministic process graph |
| Process | `ProcessRun.v1` | Runtime lifecycle and state |
| Capability | `CapabilityManifest.v1` | Governed executable service contract |
| Agent | `AgentManifest.v1` / `AgentInstance.v1` | Bounded delegated worker |
| Event | `SystemEvent.v1` | Append-only state transition record |
| Memory | `MemoryRecord.v1` | Scoped, sourced persistent context |
| Artifact | `ArtifactEnvelope.v1` | Addressable output with lineage |
| Permission | `CapabilityGrant.v1` | Principal-to-capability authorization |
| Recovery | `Checkpoint.v1` | Resumable process snapshot |
| Delivery | `DeliveryPack.v1` | Validated user-facing result bundle |
| Audit | Existing receipts and ledgers | Evidence, replay, and governance closure |

## 4. Kernel Boundary

The canonical AI OS kernel owns:

- session creation and closure;
- workspace state loading and commit;
- intent normalization;
- task graph compilation;
- process scheduling;
- policy and permission evaluation;
- capability lookup and invocation;
- agent lifecycle control;
- event emission;
- checkpoint and recovery;
- artifact registration;
- memory write arbitration;
- final delivery assembly.

Recommended canonical package:

```text
abx_os/
  kernel/
  session/
  workspace/
  process/
  scheduler/
  capabilities/
  agents/
  events/
  memory/
  permissions/
  artifacts/
  recovery/
  delivery/
```

Existing packages remain authoritative within their bounded roles:

- `abx/`: current canonical CLI and proof orchestration;
- `abraxas/`: domain runtime, rune, oracle, detector, and execution modules;
- `abx_familiar/`: task, continuity, and delegated-runtime prototypes to be promoted or adapted;
- `.abraxas/`: governance, registry, subsystem, and policy metadata;
- `schemas/`: machine-readable contracts;
- `webpanel/`, `server/`, `client/`, `shared/`: derivative operator projections.

## 5. Capability Law

Every callable tool, rune, script, adapter, model endpoint, connector, workflow, or delegated agent operation must resolve through `CapabilityManifest.v1`.

Minimum manifest fields:

```yaml
capability_id: repo.github.inspect
version: 1.0.0
provider: github
executor: connector
input_schema: GitHubRepoInspectionInput.v1
output_schema: GitHubRepoInspectionResult.v1
authority: read_only
side_effect_class: none
determinism_class: externally_observed
permissions:
  - github.repo.read
receipt_required: true
retry_policy: bounded
```

Direct cross-subsystem execution is transitional and must be inventoried, wrapped, redirected, or explicitly exempted.

## 6. Process State Machine

Canonical process states:

```text
CREATED
→ CONTEXT_READY
→ PLANNED
→ POLICY_READY
→ QUEUED
→ RUNNING
→ CHECKPOINTED | WAITING_APPROVAL | BLOCKED
→ VALIDATING
→ DELIVERING
→ COMPLETED
```

Terminal failure states:

```text
FAILED
CANCELLED
NOT_COMPUTABLE
ROLLED_BACK
```

Every transition emits `SystemEvent.v1` and must be reconstructable from the event ledger plus the latest valid snapshot.

## 7. TaskGraphIR.v1 Requirements

`TaskGraphIR.v1` extends the existing deterministic v0 representation with:

- explicit nodes and dependency edges;
- data dependencies and artifact bindings;
- capability requirements;
- policy and permission requirements;
- concurrency groups;
- branch conditions;
- time, token, cost, and tool budgets;
- retry and timeout policy;
- approval gates;
- checkpoint boundaries;
- compensation or rollback actions;
- expected outputs and delivery targets.

Inference may propose a graph, but canonical compilation must produce an explicit, validated, hashable representation.

## 8. Workspace and Memory

A workspace is the persistent AI OS boundary containing:

- principal and role bindings;
- projects, repositories, and documents;
- active and historical sessions;
- task graphs and process runs;
- artifacts and lineage;
- installed capabilities;
- memory namespaces;
- scheduled work;
- pending approvals;
- policy profile and secret references;
- continuity cursor.

Memory namespaces must remain separated:

- working;
- episodic;
- semantic;
- procedural;
- project;
- user;
- governance;
- provenance.

Every memory write requires source, scope, evidence class, retention policy, supersession semantics, and a canonical digest.

## 9. Agent Boundary

Agents are governed child processes, not free-standing authorities.

Each `AgentInstance.v1` requires:

- parent process and task linkage;
- explicit mission and completion condition;
- capability grants;
- workspace and memory scope;
- model profile;
- time, token, cost, and tool budgets;
- checkpoint policy;
- output contract;
- termination receipt.

## 10. Operator Surface

The Operator Console is a projection of canonical process, event, artifact, policy, and memory state. It should expose:

- workspace navigation;
- intent input;
- task graph and process state;
- active agents and capability calls;
- approvals and blockers;
- artifact explorer;
- event and provenance timeline;
- memory inspector;
- replay, resume, cancel, and rollback controls;
- model and resource accounting.

The UI may not invent completion, authority, or readiness states absent canonical evidence.

## 11. Initial Vertical Slice

The first production-oriented slice must implement exactly one bounded path:

```text
operator request
→ SessionEnvelope.v1
→ OperatorIntent.v1
→ TaskGraphIR.v1
→ capability resolution
→ one model inference
→ one repository read capability
→ checkpoint
→ artifact registration
→ validation
→ DeliveryPack.v1
→ continuity and memory commit
→ operator projection
```

This slice is the architectural proof. Broad migration begins only after it is deterministic, replayable, tested, and documented.

## 12. Definition of AI OS Foundation Complete

The foundation is complete when:

- the canonical schemas exist and validate;
- `abx_os.kernel` owns the vertical-slice lifecycle;
- the capability registry wraps at least one model and one external tool;
- process events reconstruct runtime state;
- checkpoints resume without semantic duplication;
- workspace state persists across sessions;
- memory writes are scoped and provenance-backed;
- the operator projection reads canonical artifacts only;
- replay produces equivalent canonical digests;
- governance tests prevent direct authority or capability bypass.
