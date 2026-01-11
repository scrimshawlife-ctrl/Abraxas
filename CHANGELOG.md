# Changelog

All notable changes to the Abraxas project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

## [Unreleased]

### Added - Shadow Detectors v0.1 (2025-12-29)
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

### Technical Details
- **SHADOW-ONLY Guarantee**: `no_influence_guarantee=True` - never affects forecasts, decisions, or state transitions
- **Deterministic**: Stable sorting, canonical JSON hashing, SHA-256 provenance
- **ABX-Runes ϟ₇ Access Control**: Invocation via SSO (Shadow Structural Observer) rune only, direct access forbidden
- **SEED Compliant**: Full provenance tracking with `inputs_hash`, `config_hash`, `computed_at_utc`
- **Bounds Enforced**: All values and subscores strictly clamped to [0.0, 1.0] via `clamp01()` utility
- **No Placeholders**: All inputs from real envelope fields discovered in codebase (slang_drift, lifecycle, weather, DMX, RDV, EFTE, CSP, fog types, symbol pool)
- **Incremental Patch Only**: Minimal diffs to existing shadow metrics preserving all existing logic

### Governance
- **Status**: Emergent Candidate (subject to evolution)
- **Mode**: `shadow` (observe-only)
- **No Influence**: `no_influence=True` (guaranteed)
- **Governance**: `emergent_candidate` (subject to rent-payment gates)
- **Rent-Payment Gates**: Skeleton only (dormant) - correlation check, stability check, utility check

### Files Created
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

### Files Modified
- `abraxas/shadow_metrics/scg.py` (+9 lines)
- `abraxas/shadow_metrics/fvc.py` (+9 lines)
- `abraxas/shadow_metrics/nor.py` (+9 lines)
- `abraxas/shadow_metrics/pts.py` (+9 lines)
- `abraxas/shadow_metrics/clip.py` (+9 lines)
- `abraxas/shadow_metrics/sei.py` (+9 lines)

**Total**: +2,757 insertions across 17 files

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

## [Unreleased]

### Planned
- Integration of runes into main Abraxas oracle pipelines
- TypeScript/JavaScript bindings for rune system
- Web UI for sigil visualization
