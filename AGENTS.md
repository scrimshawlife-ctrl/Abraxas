# ABRAXAS / AAL-Core Agent Contract

## System Identity
ABRAXAS is the execution intelligence for Abraxas / AAL-Core. All work must preserve ABX-Core, SEED, deterministic modularity, validator visibility, and run-linked lineage.

## Governance Priority
1. Repository safety and determinism
2. ABX-Core + SEED compliance
3. Incremental patch doctrine
4. Validator-visible artifact linkage
5. Delivery speed without hidden coupling

## Global Rules
- **ABX-Core required:** every complexity increase must reduce compute, time, entropy, or ambiguity.
- **SEED required:** simplify to essentials, preserve intent, maintain integrity.
- **Deterministic execution only:** no hidden randomness in control logic.
- **No mock data:** use real data, explicit `NOT_COMPUTABLE`, or explicit failure states.
- **Explicit contracts:** every new structure is typed and/or schema-defined.
- **Composability first:** avoid hidden coupling and side-channel state.

## Incremental Patch Doctrine
- Incremental patch only.
- Prefer additive changes over rewrites.
- Keep modifications local and minimal.
- Do not refactor broad systems without explicit task scope.

## Mandatory Execution Flow
All implementation runs must follow:

**PLAN → WAIT → EXECUTE → VALIDATE**

- PLAN: state files, intent, assumptions, and checks.
- WAIT: hold for approval when required by task framing.
- EXECUTE: apply minimal coherent patch set.
- VALIDATE: run focused checks and report objective outcomes.

## Output Requirements
- Report changed files and why.
- Report validation commands and outcomes.
- Distinguish pass, fail, and environment limitation.
- Surface unresolved risks or linkage gaps explicitly.

## Validation Standard
Validation must be:
- deterministic where possible,
- directly tied to changed surfaces,
- reproducible via explicit commands,
- traceable to run-linked artifacts.

## Artifact Linkage Requirements
Any execution-facing change must emit or preserve artifact surfaces linkable to validator and ledger layers, including:
- `run_id`
- `rune_id`
- `artifact_id`
- `timestamp`
- payload (`inputs`/`outputs`)
- `provenance`
- correlation or ledger pointers when available

Missing links must be represented explicitly, not fabricated.

## Prohibited Behavior
- Broad rewrites outside scope
- Hidden coupling or implicit state mutation
- Fabricated success states
- Placeholder/mock outputs presented as real
- Skipping validation for execution-critical changes

## Success Condition
A change is complete when it is minimal, deterministic, schema-aligned, rune-mapped (where applicable), validator-visible, and validated.

---

## ABX-RUNES EXECUTION LAYER

### 1) Mandatory Rune Mapping
All non-trivial operations must map to a registered rune. No free-form execution path should bypass rune mapping when a rune wrapper is applicable.

### 2) Required Rune Mapping
Each execution step must declare:
- `rune_id`
- input contract reference
- output contract reference
- determinism notes
- provenance requirements

### 3) Execution Binding
Execution should run through a rune envelope/wrapper that normalizes status, payload, provenance, and correlation fields.

### 4) Artifact Requirements
Rune execution artifacts must include:
- `run_id`, `rune_id`, `artifact_id`, `timestamp`
- `phase`, `status`
- `inputs`, `outputs`
- `provenance`
- `ledger_record_ids`, `ledger_artifact_ids`, `correlation_pointers`

### 5) Registry Enforcement
Rune IDs must exist in the rune catalog/registry prior to production promotion.

### 6) YGGDRASIL Compatibility
Rune modules must remain composable, deterministic, and independently testable so they can be chained without hidden coupling.

### 7) Shadow → Promotion Flow
- New runes default to **SHADOW** unless promotion is justified.
- Promotion requires validation evidence, deterministic behavior, and artifact linkage sufficiency.

### 8) Validation Requirements
Rune changes must include focused validation for:
- schema compatibility,
- envelope completeness,
- explicit status handling (`SUCCESS`, `FAILED`, `NOT_COMPUTABLE`),
- lineage/linkage field preservation.

### 9) Failure Handling
Failures and non-computable outcomes must be explicit and structurally valid. Do not claim success when linkage or compute prerequisites are missing.

### 10) Complexity Rule at Rune Layer
Introduce rune-layer abstractions only when they reduce entropy and improve composability across more than one execution path.

---

## ENFORCEMENT SURFACES (REPO-BOUND)

The following files are considered REQUIRED execution surfaces:

- `/AGENTS.md` (this contract)
- `/PLANS.md` (active task queue)
- `/aal_core/runes/catalog.v0.yaml` (rune registry)
- `/aal_core/schemas/rune_execution_artifact.v1.json` (artifact schema)
- `/aal_core/runes/executor.py` (rune execution wrapper)

If any are missing:
→ create minimal valid versions before proceeding with other work

All implementation must remain compatible with these surfaces.

---

## DEFAULT EXECUTION PATH (RUNE-FIRST)

All non-trivial logic must follow:

INPUT → RUNE WRAPPER → ARTIFACT → VALIDATOR SURFACE

Free-form function execution is only allowed if:
- trivial
- non-persistent
- non-artifact-generating

Otherwise:
→ must use rune executor

---

## RUNE EXECUTION MINIMUM CONTRACT

Any rune execution must produce an artifact envelope with:

- run_id
- rune_id
- artifact_id
- timestamp
- phase
- status
- inputs
- outputs
- provenance
- correlation_pointers (may be empty but must exist)

If any field is missing:
→ execution is INVALID

---

## CODE GENERATION RULE (CRITICAL)

When writing code:

1. Prefer extending:
   - rune executor
   - schema definitions
   - registry entries

2. Avoid:
   - standalone business logic functions without rune mapping
   - duplicate execution paths

3. If adding new logic:
   → wrap it in rune execution or explicitly justify why not

---

## PLAN REQUIREMENT EXTENSION

All PLAN outputs must now include:

- rune mapping per step
- artifact emission points
- validation linkage expectations

Example:

- Step: validate execution result
  - rune_id: RUNE.DIFF
  - artifact: validator output
  - linkage: ledger_record_ids + correlation_pointers

---

## VALIDATOR COMPATIBILITY GUARANTEE

All changes must preserve or improve:

- validator visibility
- artifact traceability
- run-linked lineage

If a change reduces observability:
→ reject or refactor

---

## MINIMUM VIABLE ARTIFACT RULE

If full linkage is not possible:

- still emit artifact
- set:
  - status = NOT_COMPUTABLE
  - include reason
  - preserve structure

Never skip artifact emission.

---

## DRIFT PREVENTION

If Codex encounters:

- ambiguous structure
- missing schema
- unclear rune mapping

It must:

1. stop
2. declare ambiguity
3. propose minimal schema/rune addition

Do not improvise hidden structures.

---

## SUCCESS CRITERIA (ENFORCED)

A change is ONLY valid if:

- rune-mapped (or explicitly justified trivial exception)
- artifact emitted
- schema-compliant
- validator-visible or explicitly NOT_COMPUTABLE
- deterministic across runs
