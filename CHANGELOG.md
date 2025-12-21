# Changelog

All notable changes to the Abraxas project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
