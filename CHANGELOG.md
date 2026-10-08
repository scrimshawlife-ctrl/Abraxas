# Changelog

All notable changes to the Abraxas project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [2.1.0] - 2026-10-08

> **Consolidated release.** Four separate `[Unreleased]` sections were merged into this one and
> released. Content is preserved; only the headings changed.
>
> **Version-line note.** This file also carries `[2.2.0] - 2026-01-04`, which is a HIGHER number
> with an EARLIER date than `[v2.0.0] - 2026-10-04` below it. It belongs to an abandoned numbering
> scheme, the same pattern as the `v4.0.0` and `v4.0.2` git tags, which were also older commits
> with higher numbers than `v2.0.0` and have since been **retired** (2026-10-08). The current line
> is canon-authoritative: `.abraxas/gates.json`
> holds `gates.CANON_VERSION`, and `pyproject.toml`, the README badge and `abraxas.__version__` all
> agree with it. The stray sections are documented rather than renumbered, because their true
> history is not something this file records.

### Security & Behavioural Audit of Webpanel + Dashboard


#### Fixed
- **Webpanel app could not be constructed at all** — all 61 routes unreachable. `Optional[Request]`
  dependency annotation.
- **`GET /runs/{id}` raised on every render** — undefined template variable; label now sourced from
  `PROFILE_LABELS` with raw-id fallback.
- **Ledger events were unhashable** — a float `pressure_score` reached canonical hashing, which forbids
  floats by design. Fixed at the producing site, not at the hash boundary.
- **Run plan hash was non-deterministic** — it covered a per-run id.
- **Policy-change detection could only ever return `MATCH`** — threshold was read once at import.
- **Dashboard bound `0.0.0.0` with no auth** — now defaults to `127.0.0.1` via `ABX_DASHBOARD_HOST`,
  with a bind guard refusing a non-loopback host without a token.
- **Token comparison leaked prefix length and failed open** — `secrets.compare_digest`, fail-closed.
- **`eval` on generated content** → `ast.literal_eval`.
- **13 undefined names (F821)** → `TYPE_CHECKING` imports; ruff clean.
- **`xml.etree` on third-party-fetched documents** → `defusedxml`.

#### Added
- **`webpanel/` is now covered by CI — for the first time.** 61 routes had never been executed by any
  pipeline, which is why the app could ship unbuildable. `starlette<1.0` pinned in the `[dev]` extra
  only, established by measurement (jinja2 held constant: 0.37.2 → 67 passed, 1.7.0 → 7 failed) after
  three other hypotheses were refuted and reverted.
- `webpanel/test_bind_safety.py`, `webpanel/test_token_comparison.py`.
- `defusedxml>=0.7.1`; `httpx>=0.27.0` and `jsonschema>=4.22.0` declared in `[dev]` (the harness had
  depended on them undeclared).

#### Verified
- CI green on `2b104b0c`: 4/4 workflows, `376 passed`, panel tests named in the run log.

### Changes (2)


#### Fixed
- **The evidence contract was defined twice and the copies were not the same object.** `EvidenceEnvelope`,
  `RelationStep`, `CandidateOutput`, `EvidenceType` and `Decision` are now single-homed on
  `abraxas/evidence/contract.py` (and `EvidenceProvider` on `abraxas/evidence/provider.py`), with the
  package re-exporting rather than redefining. Consequences that were silently present before: an
  `isinstance` check against the package copy rejected a real engine's output, and one `Decision` copy
  was missing `REJECT` — the value the coordination layer uses to fail closed.
- `abraxas/evidence/verifiers/latent.py` returned a bare `dict` where the interface declares an
  `EvidenceEnvelope`, and passed every guard: the conformance check asked whether a class inherits a base
  class, never what `produce_evidence` actually returns.
- `EvidenceSchemaMigrator` idempotence — `schema_version` was promoted onto the canonical envelope rather
  than deleted, because the migrator reads it to decide whether migration is needed and writes it so a
  second call is a no-op.

#### Added
- `abraxas/engines/execution_harness.py` — runs each `LIVE` engine twice on identical input and measures
  determinism, provenance, canonical artifacts, and replay. Replay persists an envelope, reloads it,
  reproduces the run, and compares against the reloaded artifact; it mirrors the existing
  `RuneReplayPacket` contract in `core/execution/replay_runner.py` rather than forcing that type.
- `scripts/survey_engine_settlements.py` — evaluates every engine against the doctrine's six
  technical-settlement criteria and refuses to certify a settlement resting on an unmeasured criterion.
  All six now measure as passing for all five live engines.
- `docs/DOCTRINE.md`, `docs/EXECUTION_HISTORY.md`, `execplans/` — doctrine, consolidated execution history,
  and the ExecPlan the contract work was delivered under.
- Guards: object-identity across every contract type (parametrized, one table row per type), a return-type
  check over every live engine, and failure-mode tests for the harness verdict.

#### Changed
- Every engine remains `unsettled`. The survey would now corroborate a technical settlement for all five
  live engines, but the criteria are measured under one defined input and a `Settlement` cannot carry that
  qualification, so the operator decision is to keep them unset and record the corroboration in
  `docs/ENGINE_TOPOLOGY.md`.
- 36 root-level status documents consolidated into `docs/EXECUTION_HISTORY.md` and removed; root `.md`
  count 57 → 18.

### Changes (3)


#### Added
- governance: add canon_state + drift_check v0.1
- governance: add inventory_report v0.1
- governance: add rune_registry_gate v0.1 (hard fail + scaffolds)
- governance: add rune_registry_gate v1.0 (hard fail + scaffolds)
- registry: sync catalog.v0.yaml and repair sdct.digit.v1 module target
- Kernel routing and deterministic handlers for `weather.generate`, `ser.run`, `daemon.ingest`, and `edge.deploy_orin`
- Oracle v2 factory wiring for lifecycle, tau, weather registry, integrity composites, and AAlmanac context
- Kernel and patch registry tests covering new rune routing and proposal-only patch receipts
- ASE (Anagram Sweep Engine) shadow-lane module with deterministic Tier-1/2 anagram mining, PFDI drift baseline, JSON schemas, CLI, and tests
- ASE hardening with strict JSONL validation, invariance gate test, CLI state carry-forward, and a shadow-lane adapter hook
- ASE lexicon automation with deterministic generator, provenance manifest, and CI check gate
- ASE candidate expansion loop with LPS scoring, lane promotion tooling, and lane-aware Tier-2 hits

#### Changed
- Kernel seed normalization to handle structured seed payloads deterministically
- Scenario runner uses caller-provided timestamp when available for deterministic outputs
- Shadow patch registry now records proposal-only receipts
- Policy allowlist expanded to include newly routable runes

#### Fixed
- Shadow detector status typing and DetectorOutput shape used by tests
- Strict-execution operators now return structured not-computable details when inputs are missing

#### Added - Shadow Detectors v0.1 (2025-12-29)
- **Shadow Detectors**: Three new observe-only pattern detectors that feed Shadow Structural Metrics as evidence without influencing system decisions
  - **Compliance vs Remix Detector** (`abraxas/detectors/shadow/compliance_remix.py`):
    - Detects balance between rote repetition and creative remix/mutation
    - Subscores: `remix_rate`, `rote_repetition_rate`, `template_phrase_density`, `anchor_stability`
    - Uses: slang drift metrics, lifecycle states, tau metrics, weather classification, CSP fields, fog types
  - **Meta-Awareness Detector** (`abraxas/detectors/shadow/meta_awareness.py`):
    - Detects meta-level discourse about manipulation, algorithms, and epistemic fatigue
    - Subscores: `manipulation_discourse_score`, `algorithm_awareness_score`, `fatigue_joke_rate`, `predictive_mockery_rate`
    - Uses: DMX metrics, RDV affect axes, EFTE fatigue metrics, keyword detection, narrative manipulation metrics
  - **Negative Space / Silence Detector** (`abraxas/detectors/shadow/negative_space.py`):
    - Detects topic dropout, visibility asymmetry, and abnormal silences
    - Subscores: `topic_dropout_score`, `visibility_asymmetry_score`, `mention_gap_halflife_score`
    - Requires: symbol pool history (minimum 3 entries) for baseline comparison
  - **Detector Infrastructure**:
    - `abraxas/detectors/shadow/types.py`: Base types (DetectorId, DetectorStatus, DetectorValue, DetectorProvenance)
    - `abraxas/detectors/shadow/registry.py`: Registry with `compute_all_detectors()` and serialization
    - `abraxas/detectors/shadow/__init__.py`: Package exports
  - **Integration Example**: `examples/shadow_detectors_integration.py` with complete usage patterns
- **Shadow Metrics Integration** (Incremental Patch Only):
  - Modified SCG, FVC, NOR, PTS, CLIP, SEI to accept optional detector evidence
  - Added `shadow_detectors` field extraction in all `extract_inputs()` functions
  - Added `shadow_detector_evidence` to metadata when present
  - **NO influence** on metric value computation (evidence only)
  - Total changes: +54 lines across 6 files (minimal diffs)
- **Comprehensive Test Suite** (22 tests, 100% passing):
  - `tests/test_shadow_detectors_determinism.py`: Verifies identical outputs for identical inputs (5 tests)
  - `tests/test_shadow_detectors_missing_inputs.py`: Verifies `not_computable` when required inputs absent (10 tests)
  - `tests/test_shadow_detectors_bounds.py`: Verifies all values clamped to [0.0, 1.0] (7 tests)
- **Documentation**:
  - `docs/detectors/shadow_detectors_v0_1.md`: Complete specification (430 lines)
  - Input requirements (required vs optional)
  - Output schemas with provenance tracking
  - Determinism guarantees and SEED compliance
  - Integration notes and usage examples
  - Governance policies and rent-payment gate stubs

#### Technical Details
- **SHADOW-ONLY Guarantee**: `no_influence_guarantee=True` - never affects forecasts, decisions, or state transitions
- **Deterministic**: Stable sorting, canonical JSON hashing, SHA-256 provenance
- **ABX-Runes ϟ₇ Access Control**: Invocation via SSO (Shadow Structural Observer) rune only, direct access forbidden
- **SEED Compliant**: Full provenance tracking with `inputs_hash`, `config_hash`, `computed_at_utc`
- **Bounds Enforced**: All values and subscores strictly clamped to [0.0, 1.0] via `clamp01()` utility
- **No Placeholders**: All inputs from real envelope fields discovered in codebase (slang_drift, lifecycle, weather, DMX, RDV, EFTE, CSP, fog types, symbol pool)
- **Incremental Patch Only**: Minimal diffs to existing shadow metrics preserving all existing logic

#### Governance
- **Status**: Emergent Candidate (subject to evolution)
- **Mode**: `shadow` (observe-only)
- **No Influence**: `no_influence=True` (guaranteed)
- **Governance**: `emergent_candidate` (subject to rent-payment gates)
- **Rent-Payment Gates**: Skeleton only (dormant) - correlation check, stability check, utility check

#### Files Created
- `abraxas/detectors/shadow/__init__.py`
- `abraxas/detectors/shadow/types.py` (94 lines)
- `abraxas/detectors/shadow/compliance_remix.py` (329 lines)
- `abraxas/detectors/shadow/meta_awareness.py` (378 lines)
- `abraxas/detectors/shadow/negative_space.py` (337 lines)
- `abraxas/detectors/shadow/registry.py` (184 lines)
- `tests/test_shadow_detectors_determinism.py` (171 lines)
- `tests/test_shadow_detectors_missing_inputs.py` (182 lines)
- `tests/test_shadow_detectors_bounds.py` (219 lines)
- `docs/detectors/shadow_detectors_v0_1.md` (430 lines)
- `examples/shadow_detectors_integration.py` (327 lines)

#### Files Modified
- `abraxas/shadow_metrics/scg.py` (+9 lines)
- `abraxas/shadow_metrics/fvc.py` (+9 lines)
- `abraxas/shadow_metrics/nor.py` (+9 lines)
- `abraxas/shadow_metrics/pts.py` (+9 lines)
- `abraxas/shadow_metrics/clip.py` (+9 lines)
- `abraxas/shadow_metrics/sei.py` (+9 lines)

**Total**: +2,757 insertions across 17 files

### Changes (4)


#### Planned
- Integration of runes into main Abraxas oracle pipelines
- TypeScript/JavaScript bindings for rune system
- Web UI for sigil visualization

## [v2.0.0] - 2026-10-04

### Canon Mutation
- CANON-SHADOW/ADVISORY_ONLY → PRODUCTION CANON
- All gates authorized: EXP-001, N5, PRODUCTION, CANON_MUTATION, RITUAL_SYSTEM

### Components Delivered
- Domain Compression Engines (DCEs)
- Oracle Pipeline v2 (Signal → Compression → Forecast → Narrative)
- Phase Detection Engine (alignment, synchronicity, early warning, drift-resonance coupling)
- Resonance Narratives (diff mode, constraints, evidence gating)
- Ritual System (7 protocols, effect tracking)
- CypherTempre Timechain (immutable records, PoW, file fallback)

### Tests
- 299 tests passing
- 5 Q1 qualifications: HYPERLEX, SEMION, NOESIS, TRUTINA, ABRAXAS
- Integrated pipeline: Phase Detection + Oracle v2 + Resonance Narratives + Ritual System

### Gates
- AC-EIC-G1 = ACCEPT (2026-10-04)
- EXP-001: ACTIVE
- N5: COMPLETE
- PRODUCTION: APPROVED
- CANON_MUTATION: AUTHORIZED

## Unreleased

### Added
- **Hyperlex Instrument V1 shadow evidence adapter** (`abraxas.evidence.hyperlex_instrument`):
  maps `hyperlex.instrument.v1` observations to advisory `SHADOW_SIGNAL` evidence.
  Feature flag `ABX_HYPERLEX_INSTRUMENT` defaults off. Subsystem
  `hyperlex_instrument_v1`. Docs: `docs/integration/hyperlex_instrument_v1.md`.
  Merged via PR #261.

## [2.2.0] - 2026-01-04

### Added
- **Seal Release Pack**: Complete release validation infrastructure
  - `VERSION` file (single-line version)
  - `abx_versions.json` (machine-readable component versions)
  - `scripts/seal_release.py` - Deterministic seal script that:
    - Runs seal tick into `./artifacts_seal`
    - Validates artifacts against schemas
    - Runs dozen-run gate into `./artifacts_gate`
    - Writes `SealReport.v0` JSON with provenance
  - `scripts/validate_artifacts.py` - Artifact validator CLI
  - `Makefile` with `seal` and `validate` targets
- **JSON Schemas** (`schemas/*.schema.json`):
  - `runindex.v0.schema.json`
  - `runheader.v0.schema.json`
  - `trendpack.v0.schema.json`
  - `resultspack.v0.schema.json`
  - `viewpack.v0.schema.json`
  - `policysnapshot.v0.schema.json`
  - `runstability.v0.schema.json`
  - `stabilityref.v0.schema.json`
  - `sealreport.v0.schema.json`
- **SealReport.v0**: New artifact schema for release validation results

### Changed
- Updated `docs/artifacts/SCHEMA_INDEX.md` with schemas directory and validation tooling

### Fixed
- None

---

## [1.4.0] - 2025-12-21

### Added
- **ABX-Runes v1.4**: Comprehensive rune-sigil generation pipeline + operator system
  - Added 3 new ABX-Runes to registry:
    - ϟ₄ SDS (State-Dependent Susceptibility) - Core layer
    - ϟ₅ IPL (Intermittent Phase-Lock) - Core layer
    - ϟ₆ ADD (Anchor Drift Detector) - Governance layer
  - **Retroactive Builder (`abx_runes_build.py`)**:
    - Comprehensive build system for sigils + operators + dispatch
    - Auto-generates operator stubs with typed signatures
    - Creates dynamic dispatch system for runtime resolution
    - Generates strict mapping for performance-critical paths
    - Future-proof: new rune defs auto-generate all infrastructure
  - **Operator Infrastructure**:
    - `operators/dispatch.py` - Dynamic rune ID → function resolution
    - `operators/map.py` - Strict mapping for direct calls
    - Individual operator modules for all 6 runes (rfa.py through add.py)
    - Typed function signatures derived from rune definitions
  - Deterministic SVG sigil generator using SHA-256 based PRNG
  - Generated deterministic sigils for all 6 runes (ϟ₁..ϟ₆)
  - Sigil manifest with SHA-256 hashes and provenance tracking
  - CLI scripts:
    - `scripts/abx_runes_build.py` - Comprehensive builder (recommended)
    - `scripts/gen_abx_sigils.py` - Legacy sigil generator
  - Comprehensive test suite for determinism and manifest integrity
  - Rune definitions with full metadata and provenance sources

### Technical Details
- Pure Python implementation (stdlib only)
- Deterministic sigil generation using `SigilPRNG` class
- Hash-based seed derivation: `rune_id + name + version + canonical_statement`
- Fixed precision SVG output (3 decimal places)
- Monochrome geometric design vocabulary
- 512x512 viewBox for all sigils

### Testing
- `tests/test_sigils_determinism.py`: Validates deterministic generation
- `tests/test_manifest_integrity.py`: Validates manifest and file hashes
- All tests ensure same inputs produce identical SVG bytes

### Files Created
- `abraxas/runes/` - New runes package
- `abraxas/runes/models.py` - Pydantic models for runes and manifests
- `abraxas/runes/sigil_generator.py` - Deterministic sigil generator
- `abraxas/runes/definitions/` - Individual rune definition files (JSON)
- `abraxas/runes/sigils/` - Generated SVG sigils
- `abraxas/runes/registry.json` - Runes registry with paths and metadata
- `scripts/gen_abx_sigils.py` - CLI tool for sigil generation

### Provenance
All new runes include provenance sources:
- Star Gauge / Xuanji Tu traversal logic
- Schumann resonance physics corpus
- EEG phase synchronization (pilot) framing
- Drift/entropy governance principles (AAL doctrine)

