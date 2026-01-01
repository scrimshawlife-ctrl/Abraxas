# Abraxas v1.4 Implementation Plan
# Temporal & Adversarial Expansion

## OVERVIEW
Surgical addition of τ operator + D/M layer + SOD modules to existing Abraxas pipeline.
No broad refactoring. Preserve existing oracle, lexicon, slang infrastructure.

## EXISTING ENTRYPOINTS (PRESERVE)
- abraxas/cli/sco_run.py — SCO analysis
- abraxas/cli/oasis_cli.py — OASIS operations
- abraxas/oracle/runner.py — DeterministicOracleRunner (v1)
- abraxas/lexicon/engine.py — LexiconEngine
- abraxas/slang/engine.py — SlangEngine

## NEW MODULES TO ADD

### 1. Core: Temporal Operator τ
**File**: abraxas/core/temporal_tau.py
- TauHalfLife (τₕ): symbolic persistence under declining reinforcement
- TauVelocity (τᵥ): emergence/decay slope from time-series
- TauPhaseProximity (τₚ): distance to lifecycle boundaries
- Deterministic confidence bands (LOW/MED/HIGH)
- Provenance embedding via abraxas.core.provenance.Provenance

### 2. Slang: Lifecycle State Machine
**File**: abraxas/slang/lifecycle.py
- Enum: LifecycleState (Proto → Front → Saturated → Dormant → Archived)
- Deterministic transition rules using τ + recurrence thresholds
- Mutation detection (edit distance for revival)

### 3. Slang: AAlmanac Store
**File**: abraxas/slang/a_almanac_store.py
- Write-once, annotate-only ledger per term
- Storage: data/a_almanac/terms.jsonl (JSONL format)
- Functions:
  - load_entries()
  - append_annotation(term_id, annotation)
  - create_entry_if_missing(term, class_id, created_at, provenance)
  - compute_current_state(term) → LifecycleState + TauSnapshot

### 4. Weather: Registry + Affinity
**Files**:
- abraxas/weather/registry.py — MW-01..MW-05 canonical types
- abraxas/weather/affinity.py — affinity(term_entry, weather_type) → [0,1]
- Deterministic scoring based on archetype class, tone flags, τ signatures

### 5. Integrity: D/M Metrics
**Files**:
- abraxas/integrity/dm_metrics.py — Artifact integrity metrics (PPS, PCS, MMS, SLS, EIS)
- abraxas/integrity/composites.py — Narrative manipulation (FLS, EIL, OCS, RRS, MPS, CIS) + composites (IRI, MRI)
- abraxas/integrity/payload_taxonomy.py — 5 canonical payload types
- abraxas/integrity/propaganda_archetypes.py — 12 propaganda families with trigger signatures

All metrics return confidence bands: LOW/MED/HIGH based on evidence completeness.
No external API calls. Risk/likelihood estimators, NOT truth adjudication.

### 6. SOD: Second-Order Symbolic Dynamics
**Files**:
- abraxas/sod/__init__.py
- abraxas/sod/models.py — Typed inputs/outputs, scenario envelopes
- abraxas/sod/ncp.py — Narrative Cascade Predictor
- abraxas/sod/cnf.py — Counter-Narrative Forecaster
- abraxas/sod/efte.py — Epistemic Fatigue Threshold Engine
- abraxas/sod/spm.py — Susceptibility Profile Mapper
- abraxas/sod/rrm.py — Recovery & Re-Stabilization Model

Each module:
- Consumes τ snapshots + AAlmanac + Weather + D/M metrics
- Emits scenario envelopes (top-N paths with triggers + probabilities)
- Probabilities are deterministic heuristic scores normalized to [0,1]
- Includes "falsifiers" field for counterfactual checks
- No simulation engine yet — deterministic scaffold only

### 7. Artifacts: Non-Commodity Outputs
**Files**:
- abraxas/artifacts/cascade_sheet.py
- abraxas/artifacts/manipulation_surface_map.py
- abraxas/artifacts/contamination_advisory.py
- abraxas/artifacts/trust_drift_graph_data.py
- abraxas/artifacts/oracle_delta_ledger.py

Each artifact:
- Outputs JSON (machine) and Markdown (human)
- Embeds provenance: run_id, timestamp, git_commit, input_hash
- Supports delta-only mode:
  - Compare to data/runs/last_snapshot.json
  - Only emit changed fields unless "full" requested

### 8. CLI Integration
**File**: abraxas/cli/abx_run_v1_4.py
- New CLI command or flags: --v1_4, --delta_only, --format, --artifacts
- Workflow:
  1. Ingest observations (existing)
  2. Update AAlmanac (append annotations, compute τ)
  3. Compute Weather + affinities
  4. Compute D/M metrics when inputs available (optional)
  5. Run SOD modules (emit envelopes)
  6. Generate artifacts (delta-only default)
  7. Persist snapshot for next run
- Do NOT break existing CLI

## DATA DIRECTORIES TO CREATE
- data/a_almanac/ — AAlmanac JSONL storage
- data/runs/ — Snapshot storage for delta-only mode

## TESTS TO ADD
**Files**:
- tests/test_temporal_tau.py
- tests/test_lifecycle.py
- tests/test_dm_metrics.py
- tests/test_sod_outputs.py
- tests/test_artifact_delta_only.py

**Golden outputs**:
- tests/golden/v1_4/*.json

**Requirements**:
- No randomness
- Fixed timestamps in fixtures
- Stable JSON ordering
- Deterministic test fixtures only

## DOCUMENTATION TO ADD/UPDATE
- docs/canon/ABRAXAS_CANON_LEDGER.txt — v1.4 entry (append only)
- docs/specs/v1_4_temporal_adversarial.md — τ operator + D/M overview
- docs/specs/sod_second_order_dynamics.md — SOD modules specification
- README.md — Add v1.4 section with usage examples

## INTEGRATION POINTS
- Existing abraxas.core.provenance.Provenance — reuse for all new modules
- Existing abraxas.core.canonical.canonical_json, sha256_hex — reuse for deterministic hashing
- Existing abraxas.slang.models.SlangCluster — extend with lifecycle state
- Existing abraxas.oracle.runner.DeterministicOracleRunner — integrate with SOD modules

## DESIGN PRINCIPLES
1. Deterministic: no random, no external API calls in core logic
2. Provenance-first: every output includes run_id, git_sha, inputs_hash
3. Silence-as-signal: missing observations affect τ decay/velocity
4. Write-once, annotate-only: AAlmanac ledger immutability
5. Delta-only default: minimize output noise
6. Confidence bands: LOW/MED/HIGH based on evidence completeness
7. No truth adjudication: D/M metrics are risk estimators only

## FILES TO MODIFY (MINIMAL)
- README.md — Add v1.4 section
- abraxas/slang/models.py — Add lifecycle_state field to SlangCluster (optional annotation)

## FILES NOT TO MODIFY
- abraxas/oracle/runner.py — preserve v1 oracle
- abraxas/lexicon/engine.py — preserve existing lexicon
- abraxas/cli/sco_run.py — preserve existing CLI
- All other existing modules

## IMPLEMENTATION ORDER
1. Core infrastructure (temporal_tau.py, lifecycle.py)
2. Data structures (almanac store, weather registry)
3. Metrics (D/M layer)
4. SOD modules (scaffold only, no simulation)
5. Artifact generators
6. CLI integration
7. Tests (golden fixtures)
8. Documentation

## SUCCESS CRITERIA
- All new tests pass with deterministic golden outputs
- Existing tests still pass (no regression)
- CLI --v1_4 flag produces artifacts with valid provenance
- Delta-only mode correctly emits only changed fields
- All modules embed git_sha and inputs_hash
- No external API calls in core logic
- No randomness in any computation
