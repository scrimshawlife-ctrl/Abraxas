# JCode Execution Plan — Abraxas AI OS Foundation

Use this plan with JCode in **Plan Mode first**, then execute one phase at a time. Do not authorize a repository-wide rewrite.

## Mission

Transform the current governed deterministic Abraxas architecture into the first canonical AI OS foundation by adding contracts, package boundaries, and one end-to-end vertical slice while preserving existing runtime, governance, proof, validation, and operator behavior.

## Operating Constraints

- Work on a dedicated feature branch.
- Read `README.md`, `PLANS.md`, `docs/README.md`, `docs/ai-os/AI_OS_CONTRACT.md`, and `docs/ai-os/ROADMAP.md` before editing.
- Treat existing deterministic, provenance, governance, validation, replay, and `NOT_COMPUTABLE` semantics as invariants.
- Reuse existing canonical JSON, hashing, schema, receipt, ledger, and policy helpers.
- Do not create parallel versions of infrastructure that already exists.
- Do not rename or relocate broad existing packages in this campaign.
- Do not modify authority or promotion defaults.
- Do not add live autonomy, unrestricted external writes, background daemons, or secret values.
- Do not delete historical docs or artifacts.
- Every implementation phase must end with tests, a diff summary, and a remaining-gap report.

## Required First Action — Repository Mapping

Before writing code, generate a repository-grounded implementation map covering:

1. Existing canonical entrypoints in `abx/`, `abraxas/`, scripts, Make targets, APIs, and workflows.
2. Existing schema loaders, canonical serializers, digest helpers, artifact writers, ledgers, receipts, replay utilities, policy evaluators, and operator projections.
3. Existing task graph, invocation plan, Familiar runtime, continuity, event, workspace, capability, agent, model, and memory concepts.
4. Direct cross-subsystem calls that bypass rune/capability registries.
5. Candidate modules to reuse for each AI OS canonical object.
6. Import-cycle and dependency-boundary risks.
7. Current test commands and known failing tests.

Write the map to:

```text
docs/ai-os/JCODE_REPOSITORY_MAP.md
```

Classify every relevant surface as:

```text
REUSE
ADAPT
WRAP
KEEP_AS_PROJECTION
COMPATIBILITY_SHIM
EXPERIMENTAL
ARCHIVE_CANDIDATE
NOT_COMPUTABLE
```

Stop and report after this map if the canonical ownership of any P0 component remains ambiguous.

## Phase 1 — Architecture Decision and Skeleton

### Goal

Create the AI OS package boundary without changing existing production behavior.

### Tasks

1. Add an ADR defining dependency direction and ownership:

```text
docs/adr/ADR-AI-OS-001-kernel-boundary.md
```

2. Create the minimal package skeleton:

```text
abx_os/
  __init__.py
  kernel/
  session/
  workspace/
  process/
  capabilities/
  events/
  artifacts/
  recovery/
  delivery/
```

3. Add import-boundary tests that prevent:

- UI/projection modules from becoming runtime authority;
- direct secret access from task/process objects;
- kernel bypass of governance, policy, receipt, and artifact layers;
- circular imports between `abx_os` and legacy packages.

4. Add package-level documentation identifying which existing modules are reused.

### Acceptance Criteria

- Existing commands behave identically.
- Existing test baseline does not regress.
- `abx_os` imports successfully with no side effects.
- Dependency tests pass.
- No duplicate canonical JSON or hashing implementation is introduced.

## Phase 2 — Canonical Schemas

### Goal

Define the minimum object contracts needed by the vertical slice.

### Required Schemas

Create repository-conformant schemas for:

```text
Principal.v1
SessionEnvelope.v1
WorkspaceState.v1
OperatorIntent.v1
TaskGraphIR.v1
ProcessRun.v1
CapabilityManifest.v1
SystemEvent.v1
Checkpoint.v1
ArtifactEnvelope.v1
DeliveryPack.v1
```

Use the repository's existing schema location and index conventions. Do not invent a second schema registry.

### Requirements

- strict required fields;
- explicit schema version;
- deterministic identifiers;
- timestamps classified as observed metadata and excluded from semantic digest where appropriate;
- `status`, `not_computable`, and reason-code semantics;
- provenance and correlation pointers;
- positive and negative fixtures;
- compatibility notes with existing TaskGraphIR, Familiar, execution, artifact, and delivery structures.

### Acceptance Criteria

- Every schema has positive and negative tests.
- Invalid unknown state values fail closed.
- Semantic digests are stable across key ordering and equivalent serialization.
- Schema index and docs are updated.

## Phase 3 — TaskGraphIR.v1 Adapter

### Goal

Extend task representation without breaking v0 consumers.

### Tasks

1. Implement `TaskGraphIR.v1` with:

- nodes and dependency edges;
- data/artifact bindings;
- required capabilities;
- policy and permission requirements;
- concurrency groups;
- branch conditions;
- budgets;
- retries and timeouts;
- approval gates;
- checkpoint boundaries;
- rollback/compensation references;
- expected outputs.

2. Add a deterministic v0-to-v1 adapter.
3. Preserve strict hash-based semantic equality.
4. Reject cycles unless explicitly represented by a bounded loop construct.
5. Add topological-order and stable-hash tests.

### Acceptance Criteria

- Existing v0 tests continue to pass.
- Equivalent graphs produce identical semantic digests.
- Invalid cycles, missing node references, and undeclared capabilities fail closed.

## Phase 4 — Capability Registry Foundation

### Goal

Provide one canonical public abstraction for executable services.

### Tasks

1. Implement or adapt `CapabilityManifest.v1` and registry lookup.
2. Wrap exactly two capabilities:

```text
model.infer.mock.v1
repo.inspect.local_read.v1
```

The model adapter must be deterministic and fixture-backed for tests. The repository adapter must be read-only and restricted to an allowed workspace root.

3. Add:

- permission declarations;
- side-effect class;
- timeout and retry policy;
- input/output schema references;
- receipt requirement;
- executor type;
- capability version.

4. Emit capability invocation receipts linked to session, workspace, process, task node, and artifact IDs.

### Acceptance Criteria

- Unregistered capabilities cannot execute.
- Missing grants fail before invocation.
- Read-only path traversal is blocked.
- Test replay can use recorded external observations.

## Phase 5 — Process, Event, and Checkpoint Spine

### Goal

Create a reconstructable runtime lifecycle.

### Tasks

1. Implement the canonical process state machine from the AI OS contract.
2. Emit append-only `SystemEvent.v1` records for every transition.
3. Add snapshot reconstruction from events.
4. Implement checkpoints at declared task graph boundaries.
5. Support resume without repeating completed capability invocations.
6. Add cancellation and `NOT_COMPUTABLE` terminal paths.
7. Reuse existing ledger and receipt infrastructure where possible.

### Acceptance Criteria

- Illegal transitions fail closed.
- State reconstructs identically from the event ledger.
- Resume is idempotent.
- Checkpoint corruption is detected by digest mismatch.
- Process and event records link to existing governance and artifact surfaces.

## Phase 6 — Canonical Vertical Slice

### Goal

Execute one complete AI OS flow through a single kernel entrypoint.

### Implement

```python
abx_os.kernel.run(request, workspace, principal, policy_profile)
```

or a repository-conformant equivalent.

### Flow

```text
request
→ create/load session
→ normalize OperatorIntent
→ compile TaskGraphIR.v1
→ evaluate policy and grants
→ call model.infer.mock.v1
→ call repo.inspect.local_read.v1
→ checkpoint
→ register ArtifactEnvelope.v1
→ validate output
→ assemble DeliveryPack.v1
→ commit continuity/workspace state
→ emit operator projection
```

### Required Fixtures

- normal success;
- missing repository path;
- denied capability;
- model result unavailable;
- checkpoint and resume;
- replay from recorded observations;
- corrupted artifact;
- cancellation before delivery.

### Acceptance Criteria

- A single command or test executes the full slice.
- All canonical objects are emitted and schema-valid.
- Semantic digests match under replay.
- No external network or live model is required for the test lane.
- Existing canonical proof and governance tests pass.

## Phase 7 — Projection Bridge

### Goal

Expose the vertical slice through existing operator surfaces without creating a second source of truth.

### Tasks

1. Add a read-only projection builder consuming canonical session, process, event, policy, artifact, and delivery records.
2. Integrate with the smallest existing operator route or API surface.
3. Display:

- current process state;
- task nodes;
- capability calls;
- blockers and reason codes;
- artifacts;
- provenance pointers;
- checkpoint/resume availability.

4. Label all projection-only fields.

### Acceptance Criteria

- Projection tests use canonical fixtures.
- UI/API cannot mutate canonical state directly.
- No authority, readiness, or completion state is derived without canonical evidence.

## Phase 8 — Closure and Handoff

### Required Outputs

- updated architecture diagram;
- updated `README.md`, `PLANS.md`, and `docs/README.md` only where implementation evidence supports changes;
- schema index update;
- test inventory and results;
- migration/compatibility notes;
- unresolved gaps classified by priority;
- list of duplicate or obsolete surfaces discovered, without deleting them;
- follow-on plan for workspace persistence, real model adapters, identity, memory, scheduler, and agents.

Write the final report to:

```text
docs/ai-os/JCODE_AI_OS_FOUNDATION_REPORT.md
```

## Validation Commands

Discover and use repository-native commands first. At minimum, run the relevant equivalents of:

```bash
pytest -q
make dependency-check
make developer-readiness
make governance-lint
make ts-canonical-check
```

If the full suite has known failures, separate:

```text
NEW_REGRESSION
PRE_EXISTING_FAILURE
ENVIRONMENT_BLOCKED
NOT_COMPUTABLE
```

Never report a clean pass by excluding failing tests without documenting the exclusion.

## Commit Strategy

Use bounded commits:

1. `docs: map AI OS reuse and ownership`
2. `arch: add AI OS package boundary`
3. `schema: add AI OS foundation contracts`
4. `feat: add task graph v1 adapter`
5. `feat: add governed capability registry foundation`
6. `feat: add process event checkpoint spine`
7. `feat: implement AI OS vertical slice`
8. `feat: project canonical AI OS process state`
9. `docs: seal AI OS foundation report`

Do not combine all work into one opaque commit.

## Stop Conditions

Stop implementation and report rather than guessing when:

- canonical ownership conflicts between two existing modules;
- required governance or policy behavior is unclear;
- a change would alter promotion or authority defaults;
- the existing test baseline cannot be established;
- schema duplication cannot be avoided;
- a required secret or live external service would be needed;
- repository state contains unrelated uncommitted changes.
