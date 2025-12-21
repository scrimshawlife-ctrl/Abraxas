# ABX-Runes: Deterministic Runic Symbolic System

**Version:** 1.4.0
**Status:** Canonical
**Framework:** SEED Compliant

## Overview

ABX-Runes is a deterministic symbolic system providing geometric sigils and semantic anchors for the Abraxas oracle framework. Each rune encodes a specific operational principle with provenance tracking and cryptographic verification.

## Runes Registry

### Core Layer

- **ϟ₁ RFA** (Resonant Field Anchor)
  *"Stabilize meaning by fixing the center, not the path."*
  Establishes stable semantic anchor points for drift-tolerant interpretation.

- **ϟ₂ TAM** (Traversal-as-Meaning)
  *"Meaning is the walk, not the map."*
  Treats meaning as emergent from path traversal rather than static transmission.

- **ϟ₄ SDS** (State-Dependent Susceptibility)
  *"The system only resonates when the receiver is phase-open."*
  Gates signal reception based on receiver state and phase alignment.

- **ϟ₅ IPL** (Intermittent Phase-Lock)
  *"Resonance appears in windows, not streams."*
  Enforces bounded temporal windows with mandatory refractory periods.

### Validation Layer

- **ϟ₃ WSSS** (Weak Signal · Strong Structure)
  *"Power does not persuade. Structure does."*
  Validates effects scale with structural coherence, not signal amplitude.

### Governance Layer

- **ϟ₆ ADD** (Anchor Drift Detector)
  *"When the center moves, meaning decays."*
  Monitors semantic anchor drift with immutable logging and conservative recentering.

## Architecture

### Directory Structure

```
abraxas/runes/
├── __init__.py              # Package initialization
├── models.py                # Pydantic models for runes and manifests
├── sigil_generator.py       # Deterministic SVG generation (legacy)
├── registry.json            # Runes registry with paths and metadata
├── README.md                # This file
├── definitions/             # Individual rune definition files (JSON)
│   ├── rune_01_rfa.json
│   ├── rune_02_tam.json
│   ├── rune_03_wsss.json
│   ├── rune_04_sds.json
│   ├── rune_05_ipl.json
│   └── rune_06_add.json
├── sigils/                  # Generated SVG sigils
│   ├── manifest.json        # SHA-256 hashes and provenance
│   ├── ϟ₁_RFA.svg
│   ├── ϟ₂_TAM.svg
│   ├── ϟ₃_WSSS.svg
│   ├── ϟ₄_SDS.svg
│   ├── ϟ₅_IPL.svg
│   └── ϟ₆_ADD.svg
└── operators/               # Rune operator implementations
    ├── __init__.py
    ├── dispatch.py          # Dynamic dispatcher
    ├── map.py               # Strict mapping (optional)
    ├── rfa.py               # RFA operator
    ├── tam.py               # TAM operator
    ├── wsss.py              # WSSS operator
    ├── sds.py               # SDS operator
    ├── ipl.py               # IPL operator
    └── add.py               # ADD operator
```

## Deterministic Sigil Generation

### SigilPRNG

The `SigilPRNG` class implements a deterministic pseudo-random number generator based on SHA-256 hash chaining:

```python
from abraxas.runes.sigil_generator import SigilPRNG

prng = SigilPRNG("seed_material")
value = prng.next_float()  # [0, 1)
angle = prng.next_angle()  # [0, 2π)
```

### Seed Material

Each rune's sigil is generated from deterministic seed material:

```
seed = f"{rune_id}:{short_name}:{version}:{canonical_statement}"
```

### SVG Properties

- **Dimensions:** 512x512 viewBox
- **Style:** Monochrome (black strokes, no fills)
- **Precision:** 3 decimal places for all numeric values
- **Format:** Sorted attributes, Unix newlines, stable ordering

## CLI Usage

### ABX-Runes Builder (Recommended)

The `abx_runes_build.py` script provides comprehensive build and verification:

```bash
# Build everything: sigils, operators, dispatch system
python scripts/abx_runes_build.py --write --strict-map

# Verify build integrity
python scripts/abx_runes_build.py --check
```

**What it does:**
- Generates deterministic SVG sigils for all runes
- Creates operator stubs for missing runes
- Generates dynamic dispatch system
- Creates strict mapping (`operators/map.py`) when `--strict-map` is used
- Validates manifest integrity

### Legacy Sigil Generator

The original sigil generator is still available:

```bash
# Generate all sigils
python scripts/gen_abx_sigils.py --all --write-manifest

# Generate single sigil
python scripts/gen_abx_sigils.py --id ϟ₄

# Verify manifest
python scripts/gen_abx_sigils.py --check
```

## Testing

### Run Determinism Tests

```bash
pytest tests/test_sigils_determinism.py -v
```

### Run Manifest Integrity Tests

```bash
pytest tests/test_manifest_integrity.py -v
```

### Test Coverage

- **Determinism:** Same seed → identical SVG bytes
- **Hash Verification:** Manifest hashes match file contents
- **Registry References:** All runes have valid definitions
- **Regeneration:** Sigils can be regenerated deterministically

## Provenance

All runes include provenance sources:

- Star Gauge / Xuanji Tu traversal logic
- Schumann resonance physics corpus
- EEG phase synchronization (pilot) framing
- Drift/entropy governance principles (AAL doctrine)

## Operator System

### Dynamic Dispatch

ABX-Runes provides automatic operator resolution via the dynamic dispatcher:

```python
from abraxas.runes.operators import dispatch

# Dispatch rune by ID
result = dispatch("ϟ₁", semantic_field=data, context_vector=ctx, anchor_candidates=candidates)

# Result contains operator outputs
print(result["anchored_field"])
print(result["resonance_strength"])
```

**How it works:**
1. Loads rune definition from `definitions/*.json`
2. Resolves short_name to operator module
3. Calls `apply_<short_name>(**kwargs)`
4. Returns output dictionary

### Strict Mapping

For performance-critical paths, use the strict mapping:

```python
from abraxas.runes.operators.map import RUNE_FUNCTIONS

# Direct function call (faster)
apply_rfa = RUNE_FUNCTIONS["ϟ₁"]
result = apply_rfa(semantic_field=data, context_vector=ctx, anchor_candidates=candidates)
```

### Operator Stubs

All operators are generated as stubs with:
- Typed function signatures derived from rune inputs
- Output dictionaries matching rune outputs
- `strict_execution` parameter for enforcement

**Example stub (SDS operator):**

```python
def apply_sds(
    receiver_state: Any,
    phase_alignment: Any,
    incoming_signal: Any,
    susceptibility_threshold: Any,
    *,
    strict_execution: bool = False
) -> Dict[str, Any]:
    if strict_execution:
        raise NotImplementedError("Operator not implemented yet...")

    return {
        "gated_signal": None,
        "reception_status": None,
        "state_classification": None,
    }
```

To implement an operator, replace the stub with real logic while preserving the signature.

## API Reference

### Models

#### `RuneDefinition`

Complete definition of an ABX-Rune with metadata, constraints, and provenance.

**Key Fields:**
- `id`: Rune identifier (e.g., "ϟ₁")
- `short_name`: Acronym (e.g., "RFA")
- `canonical_statement`: Defining principle
- `introduced_version`: Version when introduced

#### `SigilManifest`

Manifest tracking all generated sigils with SHA-256 hashes.

**Key Fields:**
- `generated_at_utc`: Generation timestamp
- `generator_version`: Generator version
- `entries`: List of `SigilManifestEntry` objects

### Functions

#### `generate_sigil(rune_id: str, seed_material: str) -> str`

Generate deterministic SVG sigil for a specific rune.

**Parameters:**
- `rune_id`: Rune identifier (e.g., "ϟ₁")
- `seed_material`: Deterministic seed string

**Returns:**
- SVG string with fixed formatting

**Example:**
```python
from abraxas.runes.sigil_generator import generate_sigil

svg = generate_sigil("ϟ₁", "ϟ₁:RFA:1.0.0:Stabilize meaning by fixing the center, not the path.")
```

## SEED Framework Compliance

✅ **Deterministic Execution:** All sigil generation is deterministic
✅ **Provenance Chain:** Full provenance tracking for all runes
✅ **Entropy Bounded:** PRNG entropy derived from SHA-256
✅ **Capability Isolation:** No network access, filesystem-only
✅ **Integrity Verification:** SHA-256 hashes in manifest

## Version History

- **1.4.0** (2025-12-21): Added ϟ₄ SDS, ϟ₅ IPL, ϟ₆ ADD + sigil pipeline
- **1.0.0** (2024-Q4): Initial release with ϟ₁ RFA, ϟ₂ TAM, ϟ₃ WSSS

## License

Part of the Abraxas project. See main repository for license details.
