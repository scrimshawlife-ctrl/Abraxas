# VBM Casebook: Vortex-Based Mathematics Drift Detection

## Overview

The VBM (Vortex-Based Mathematics) casebook is a **drift detection and operator training dataset** integrated into Abraxas. It serves as an IMMUNE-SYSTEM component for identifying and classifying escalating rhetorical patterns that begin with mathematical observations and progress toward unfalsifiable metaphysical claims.

**CRITICAL: VBM is NOT used as a knowledge source for physics or mathematics. It is a PATTERN/DYNAMICS casebook ONLY.**

## Purpose

The VBM casebook enables:

1. **Drift Detection**: Identify VBM-class rhetoric in live Decodo streams
2. **Operator Training**: Validate that operator candidates don't false-positive on VBM patterns
3. **Phase Classification**: Map text to escalation phases (1-6)
4. **Quarantine System**: Tag VBM-class content for special handling

## Six-Phase Escalation Model

The VBM casebook documents a 6-phase escalation pattern:

### Phase 1: MATH_PATTERN
- **Description**: Initial pattern observation in mathematics
- **Markers**: Arithmetic patterns, sequences, doubling, symmetry
- **Example**: "The sequence 1, 2, 4, 8 exhibits repeating patterns in modular arithmetic"

### Phase 2: REPRESENTATION_REDUCTION
- **Description**: Digital root reduction and modular operations
- **Markers**: Digital root, reduces, single digits, repeating decimals, modular
- **Example**: "All numbers reduce to single digits through digital root operations"

### Phase 3: CROSS_DOMAIN_ANALOGY
- **Description**: Pattern applied across unrelated domains
- **Markers**: DNA, music, binary, galaxies, biology, nuclear, aura
- **Example**: "The pattern appears in DNA structure, musical frequencies, and galaxy spirals"

### Phase 4: PHYSICS_LEXICON_INJECTION
- **Description**: Physics terminology without physics methodology
- **Markers**: Tachyon, monopole, ether, zero-point, inertia, magnetic field, photon
- **Example**: "Tachyons emerge from the vortex, explaining zero-point energy dynamics"

### Phase 5: CONSCIOUSNESS_ATTRIBUTION
- **Description**: Pattern linked to consciousness and awareness
- **Markers**: Consciousness, apex of consciousness, awareness, sentience, cosmic mind
- **Example**: "The pattern represents the architecture of consciousness itself"

### Phase 6: UNFALSIFIABLE_CLOSURE
- **Description**: Claims immune to falsification
- **Markers**: Everything explains, must coexist, cannot revert, absolute, complete, fundamental
- **Example**: "This theory is complete and cannot be disproven because the pattern is everywhere"

## Architecture

### Components

```
abraxas/casebooks/vbm/
├── models.py          # VBMPhase, VBMEpisode, VBMCasebook, VBMDriftScore
├── corpus.py          # Episode loading and normalization
├── phase.py           # Deterministic phase classification
├── features.py        # Feature extraction
├── comparator.py      # Scoring against casebook
├── registry.py        # Singleton registry with caching
└── README.md          # This file
```

### Data Flow

```
Decodo Stream
    ↓
ResonanceFrames
    ↓
SlangEngine.process_frames()
    ↓
apply_vbm_drift_tagging()
    ↓
VBMRegistry.score_text()
    ↓
VBMDriftScore (phase, score, lattice_hits)
    ↓
Cluster annotation (drift_tags, vbm_phase, vbm_score)
```

## Integration Points

### 1. SEE (Slang Emergence Engine)

VBM integrates into SEE's processing pipeline:

```python
from abraxas.slang.engine import SlangEngine

engine = SlangEngine(enable_vbm_casebook=True)
clusters = engine.process_frames(frames)

# Clusters now have VBM annotations
for cluster in clusters:
    if "VBM_CLASS" in cluster.drift_tags:
        print(f"VBM Phase: {cluster.vbm_phase}")
        print(f"VBM Score: {cluster.vbm_score}")
        print(f"Lattice Hits: {cluster.vbm_lattice_hits}")
```

**Drift Tagging Threshold**: VBM_CLASS tag fires when drift_score >= 0.65

### 2. OAS (Operator Auto-Synthesis)

VBM serves as a golden validation dataset for operator candidates:

**In-Scope Criteria**: Candidates are VBM in-scope if triggers/scope contain:
- digital root, symmetry, torus, vortex, pattern
- zero-point, tachyon, ether, monopole
- consciousness, frequency, modular

**Golden Gate Requirements**:
1. Candidate must fire on VBM episodes (recall > 0.1)
2. Candidate must NOT fire on control texts (false positives = 0)

```python
from abraxas.oasis.validator import OASValidator

validator = OASValidator(enable_vbm_golden=True)

# Check if candidate is in-scope
if validator.is_vbm_inscope(candidate):
    passed, metrics = validator.validate_vbm_golden(candidate)
    print(f"VBM Golden Gate: {'PASS' if passed else 'FAIL'}")
    print(f"VBM Hits: {metrics.get('vbm_hits', 0)}")
    print(f"Control FP: {metrics.get('control_false_positives', 0)}")
```

## Operator Lattice Mapping

VBM phase detection maps to operator lattice IDs:

| Phase | Lattice Operators |
|-------|------------------|
| MATH_PATTERN | MKB (Math Knowledge Base) |
| REPRESENTATION_REDUCTION | MKB, SCA (Symbolic Compression Analogy) |
| CROSS_DOMAIN_ANALOGY | SCA, DOE (Domain Overgeneralization) |
| PHYSICS_LEXICON_INJECTION | DOE, PAP (Physics Authority Pattern) |
| CONSCIOUSNESS_ATTRIBUTION | PAM (Pattern Authority Metaphysics), UCS |
| UNFALSIFIABLE_CLOSURE | UCS (Unfalsifiable Cosmic Scope) |

## Usage Examples

### Classify Text Phase

```python
from abraxas.casebooks.vbm.registry import get_vbm_registry

registry = get_vbm_registry()
registry.load_casebook()

text = "The tachyon field exhibits consciousness through vortex dynamics"
phase, confidence = registry.phase_text(text)

print(f"Phase: {phase.value}")
print(f"Confidence: {confidence:.2f}")
```

### Score Text Against VBM

```python
score = registry.score_text(
    text="Consciousness emerges from the torus pattern",
    operator_hits=["ctd_v1"]
)

print(f"Drift Score: {score.score:.2f}")
print(f"Phase: {score.phase.value}")
print(f"Lattice Hits: {score.lattice_hits}")
```

### Process Stream with VBM Tagging

```python
from abraxas.slang.engine import SlangEngine
from abraxas.decodo.adapter import DecodoAdapter

adapter = DecodoAdapter()
frames = adapter.events_to_frames(decodo_events)

engine = SlangEngine(enable_vbm_casebook=True)
clusters = engine.process_frames(frames)

# Filter VBM-tagged clusters
vbm_clusters = [c for c in clusters if "VBM_CLASS" in c.drift_tags]

for cluster in vbm_clusters:
    print(f"Cluster: {cluster.cluster_id}")
    print(f"  Phase: {cluster.vbm_phase}")
    print(f"  Score: {cluster.vbm_score:.2f}")
    print(f"  Lattice: {cluster.vbm_lattice_hits}")
```

## Determinism Guarantees

The VBM casebook provides deterministic operation:

1. **Corpus Loading**: Episodes sorted by episode_id
2. **Token Extraction**: Deterministic substring matching
3. **Phase Classification**: Rule-based with stable lexeme weights
4. **Feature Extraction**: Deterministic feature computation
5. **Scoring**: Cached by SHA256 hash of text
6. **Provenance**: Full audit trail for all operations

## Testing

Run VBM tests:

```bash
# Test casebook ingestion
pytest tests/test_vbm_casebook_ingest.py -v

# Test phase classification
pytest tests/test_vbm_phase_classifier.py -v

# Test SEE drift tagging
pytest tests/test_see_vbm_drift_tagging.py -v

# Test OAS golden gate
pytest tests/test_oas_vbm_golden_gate.py -v
```

## Fixtures

VBM casebook fixtures: `tests/fixtures/vbm/`

- `episode_01.json` - Phase 1: Math pattern
- `episode_02.json` - Phase 2: Representation reduction
- `episode_03.json` - Phase 3: Cross-domain analogy
- `episode_04.json` - Phase 4: Physics lexicon injection
- `episode_05.json` - Phase 5: Consciousness attribution
- `episode_06.json` - Phase 6: Unfalsifiable closure (first)
- `episode_07.json` - Phase 6: Unfalsifiable closure (final)
- `vbm_expected_phase_curve.json` - Expected phase classifications

## Configuration

VBM behavior can be configured:

```python
# Disable VBM in SEE
engine = SlangEngine(enable_vbm_casebook=False)

# Disable VBM golden gate in OAS
validator = OASValidator(enable_vbm_golden=False)

# Adjust drift threshold (default: 0.65)
VBM_THRESHOLD = 0.70  # More strict
```

## Design Principles

1. **Quarantine First**: VBM is NEVER used as truth; only as pattern library
2. **Deterministic**: All operations are deterministic and reproducible
3. **Provenance**: Full audit trail for every classification
4. **Backward Compatible**: Existing pipelines unaffected
5. **Typed**: Strict pydantic validation everywhere
6. **Cached**: Results cached by text hash for efficiency

## Maintenance

### Adding New Episodes

1. Create `episode_N.json` in `tests/fixtures/vbm/`
2. Include: episode_id, title, summary_text
3. Update expected phase curve if needed
4. Run tests to verify determinism

### Extending Phase Model

1. Add new phase to `VBMPhase` enum in `models.py`
2. Add lexeme group to `TRIGGER_LEXICON` in `corpus.py`
3. Update phase weights in `phase.py`
4. Add lattice mapping in `comparator.py`
5. Update tests and documentation

### Tuning Classification

Adjust lexeme weights and thresholds in:
- `phase.py`: Phase classification logic
- `features.py`: Feature extraction weights
- `comparator.py`: Scoring logic and thresholds

## References

- Main SEE integration: `abraxas/slang/engine.py:158-187`
- OAS validator extension: `abraxas/oasis/validator.py:229-332`
- OAS canonizer gate: `abraxas/oasis/canonizer.py:227-249`
- Cluster model extension: `abraxas/slang/models.py:48-55`

## Support

For issues or questions about VBM casebook integration, see:
- Test suite for usage examples
- Source code for implementation details
- This README for architecture overview
