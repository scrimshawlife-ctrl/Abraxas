# Temporal Drift Detection (TDD)

## Overview

The Temporal Drift Detection (TDD) subsystem detects and classifies patterns of **causality inversion**, **diagrammatic temporal authority**, and **eschatological closure** in text. TDD is designed to protect **user epistemic sovereignty** by identifying rhetorical patterns that position subjects as predetermined outcomes of temporal structures.

**CRITICAL: TDD enforces de-escalation protocols for high sovereignty risk. When temporal authority patterns threaten user agency, the system MUST respond with de-escalation rather than reinforcement.**

## Purpose

TDD enables:

1. **Causality Detection**: Identify inverted or abolished causality claims
2. **Authority Classification**: Detect diagrammatic command structures over time
3. **Sovereignty Protection**: Flag patterns that erode user epistemic agency
4. **Operator Validation**: Test operator candidates against temporal drift patterns
5. **De-escalation**: Enforce protective responses for high-risk content

## Four-Dimensional Classification

TDD classifies text across four independent dimensions:

### Dimension 1: Temporal Mode

How time is conceptualized:

- **LINEAR**: Standard past→present→future causality
  - Example: "Yesterday I went to the store, tomorrow I'll cook dinner"

- **CYCLIC**: Eternal return, repetition, loops
  - Example: "The cycle repeats eternally in infinite loops"

- **INVERTED**: Retrocausality, future determines past
  - Example: "Time flows backwards through retrocausal determination"
  - **Triggers**: retronic, retrocausal, temporal inversion, backwards causation

- **ESCHATOLOGICAL**: End-times teleology, apocalyptic finality
  - Example: "The eschaton pulls all moments toward inevitable apocalypse"
  - **Triggers**: eschaton, apocalypse, end-times, destiny, inevitable, final

### Dimension 2: Causality Status

State of cause-effect relations:

- **NORMAL**: Standard cause→effect relations
- **QUESTIONED**: Causality uncertainty, ambiguity
- **INVERTED**: Effects precede causes, backwards causation
- **ABOLISHED**: Causality dissolved, acausal systems

### Dimension 3: Diagram Role

Authority status of temporal structures:

- **PASSIVE**: Time as neutral background
- **DESCRIPTIVE**: Time as pattern to describe
- **AUTHORITATIVE**: Time exerts influence, has weight
- **COMMANDING**: Time commands, overrides agency
  - **Triggers**: diagram, authority, command, override, determine, control

### Dimension 4: Sovereignty Risk

Risk to user epistemic sovereignty:

- **LOW**: No agency threats, user maintains autonomy
- **MODERATE**: Minor authority claims, limited agency questions
- **HIGH**: Significant authority claims, agency migration
- **CRITICAL**: Agency abolition, deterministic closure, sovereignty collapse
  - **Combination**: ESCHATOLOGICAL + COMMANDING + INVERTED

**Risk Escalation Rules**:
```
CRITICAL if: (ESCHATOLOGICAL + COMMANDING) OR (INVERTED + COMMANDING + agency_erosion)
HIGH if: COMMANDING + (INVERTED OR ESCHATOLOGICAL)
MODERATE if: AUTHORITATIVE OR (QUESTIONED causality)
LOW otherwise
```

## Architecture

### Components

```
abraxas/temporal/
├── models.py          # TemporalMode, CausalityStatus, DiagramRole, SovereigntyRisk
├── features.py        # Lexeme-based feature extraction
├── classifier.py      # Rule-based classification logic
├── detector.py        # TDD detector with SHA256 caching
└── README.md          # This file

abraxas/casebooks/numogram/
├── models.py          # NumogramEpisode, NumogramCasebook
├── corpus.py          # Episode loading (Retrónic Time)
└── __init__.py
```

### Data Flow

```
Decodo Stream
    ↓
ResonanceFrames
    ↓
SlangEngine.process_frames()
    ↓
apply_temporal_drift_detection()
    ↓
TemporalDriftDetector.analyze()
    ↓
TemporalDriftResult (mode, causality, diagram_role, sovereignty_risk)
    ↓
Cluster annotation (temporal_mode, sovereignty_risk, tdd_operator_hits)
    ↓
Response mode: "de-escalate" if sovereignty_risk >= HIGH
```

## Integration Points

### 1. SEE (Slang Emergence Engine)

TDD integrates into SEE's processing pipeline:

```python
from abraxas.slang.engine import SlangEngine

engine = SlangEngine(enable_tdd=True)
clusters = engine.process_frames(frames)

# Clusters now have TDD annotations
for cluster in clusters:
    print(f"Temporal Mode: {cluster.temporal_mode}")
    print(f"Sovereignty Risk: {cluster.sovereignty_risk}")
    print(f"TDD Operators: {cluster.tdd_operator_hits}")

    # Check for de-escalation requirement
    if cluster.response_mode == "de-escalate":
        print("⚠️ HIGH SOVEREIGNTY RISK - DE-ESCALATE")
```

**De-escalation Trigger**: response_mode = "de-escalate" when sovereignty_risk in [HIGH, CRITICAL]

### 2. OAS (Operator Auto-Synthesis)

TDD serves as a golden validation dataset for operator candidates:

**In-Scope Criteria**: Candidates are TDD in-scope if triggers contain:
- time, temporal, causality, causal, retrocausal
- future, destiny, fate, predetermined, inevitable
- eschaton, apocalypse, end-times, final
- diagram, authority, teleology

**Golden Gate Requirements**:
1. Candidate must fire on TDD patterns (recall > 0.3)
2. Candidate must NOT fire on control texts (false positives = 0)

```python
from abraxas.oasis.validator import OASValidator

validator = OASValidator(enable_vbm_golden=True)

# Check if candidate is in-scope
if validator.is_tdd_inscope(candidate):
    passed, metrics = validator.validate_tdd_golden(candidate)
    print(f"TDD Golden Gate: {'PASS' if passed else 'FAIL'}")
    print(f"TDD Recall: {metrics.get('tdd_recall', 0):.2f}")
    print(f"Control FP: {metrics.get('control_false_positives', 0)}")
```

## Operator Lattice Mapping

TDD detection maps to operator lattice IDs:

| Pattern | Operator | Description |
|---------|----------|-------------|
| Retrocausality | **RTI** | Retronic Time Inversion |
| Diagrammatic Authority | **DTA** | Diagram Temporal Authority |
| Eschatological Closure | **HSE** | Hard Singularity Eschaton |
| Sovereignty Erosion | **UCS** | Unfalsifiable Cosmic Scope |

**Operator Hit Rules**:
```
RTI if: temporal_mode == INVERTED OR causality_status == INVERTED
DTA if: diagram_role in [AUTHORITATIVE, COMMANDING]
HSE if: temporal_mode == ESCHATOLOGICAL
UCS if: sovereignty_risk == CRITICAL
```

## Usage Examples

### Analyze Text for Temporal Drift

```python
from abraxas.temporal.detector import analyze_text

text = "The eschaton flows backwards through retrocausal destiny"
result = analyze_text(text)

print(f"Temporal Mode: {result.temporal_mode.value}")
print(f"Causality: {result.causality_status.value}")
print(f"Diagram Role: {result.diagram_role.value}")
print(f"Sovereignty Risk: {result.sovereignty_risk.value}")
print(f"Operators: {result.operator_hits}")
```

### Process Stream with TDD

```python
from abraxas.slang.engine import SlangEngine
from abraxas.decodo.adapter import DecodoAdapter

adapter = DecodoAdapter()
frames = adapter.events_to_frames(decodo_events)

engine = SlangEngine(enable_tdd=True)
clusters = engine.process_frames(frames)

# Filter high-risk clusters
high_risk = [
    c for c in clusters
    if c.sovereignty_risk in ["high", "critical"]
]

for cluster in high_risk:
    print(f"⚠️ Cluster: {cluster.cluster_id}")
    print(f"  Risk: {cluster.sovereignty_risk}")
    print(f"  Mode: {cluster.temporal_mode}")
    print(f"  Response: {cluster.response_mode}")
```

### Direct Detector Usage

```python
from abraxas.temporal.detector import TemporalDriftDetector

detector = TemporalDriftDetector()

# Analyze with caching
result = detector.analyze("Time flows backwards", use_cache=True)

# Check cache stats
stats = detector.get_cache_stats()
print(f"Cache size: {stats['cache_size']}")

# Clear cache if needed
detector.clear_cache()
```

### Feature Extraction

```python
from abraxas.temporal.features import extract_temporal_features, compute_temporal_signature

text = "The future determines the past through diagram authority"
features = extract_temporal_features(text)

print(f"Retronic density: {features['retronic_density']:.2f}")
print(f"Eschatology density: {features['eschatology_density']:.2f}")
print(f"Diagram authority: {features['diagram_authority_density']:.2f}")

signature = compute_temporal_signature(features)
print(f"Temporal signature: {signature}")
```

## Numogram TT-CB Casebook

The Numogram Temporal-Theory Casebook includes Nick Land's **Retrónic Time** as a terminal unfalsifiable episode.

### Episode: numogram_08 - Retrónic Time

**Classification**:
- Temporal Mode: ESCHATOLOGICAL
- Causality Status: INVERTED
- Diagram Role: COMMANDING
- Sovereignty Risk: CRITICAL

**Content**: Material on temporal inversion, backwards causation from future eschaton, diagrammatic authority over consciousness, agency migration to teleological structures.

**Operator Hits**: RTI, DTA, HSE, UCS (all four)

### Loading Numogram Casebook

```python
from abraxas.casebooks.numogram.corpus import load_numogram_episodes, build_numogram_casebook

# Load episodes
episodes = load_numogram_episodes()
retronic = episodes[0]  # numogram_08

print(f"Title: {retronic.title}")
print(f"Phase: {retronic.phase}")
print(f"Tokens: {retronic.extracted_tokens}")

# Build complete casebook
casebook = build_numogram_casebook(episodes)
print(f"Casebook ID: {casebook.casebook_id}")
print(f"Lexicon categories: {list(casebook.trigger_lexicon.keys())}")
```

## Determinism Guarantees

TDD provides deterministic operation:

1. **Feature Extraction**: Deterministic lexeme counting, normalized scores
2. **Classification**: Rule-based with stable thresholds
3. **Operator Hits**: Deterministic mapping from classifications
4. **Caching**: Results cached by SHA256(text)
5. **Provenance**: Full audit trail for all detections

## Testing

Run TDD tests:

```bash
# Test TDD classifier
pytest tests/test_tdd_classifier.py -v

# Test Numogram Retrónic ingestion
pytest tests/test_numogram_retronic_ingest.py -v

# Test SEE temporal drift integration
pytest tests/test_see_temporal_drift.py -v

# Test OAS TDD golden gate
pytest tests/test_oas_tdd_golden_gate.py -v
```

## Fixtures

TDD fixtures: `tests/fixtures/numogram/`

- `episode_08_retronic_time.json` - Retrónic Time episode
- `retronic_expected_tdd.json` - Expected TDD classifications

## Configuration

TDD behavior can be configured:

```python
# Disable TDD in SEE
engine = SlangEngine(enable_tdd=False)

# Analyze without caching
result = detector.analyze(text, use_cache=False)

# Provide operator hits from upstream
result = detector.analyze(text, operator_hits=["ctd_v1", "mkb_v1"])
```

## Lexeme Groups

TDD uses four lexeme groups for feature extraction:

### RETRONIC_TERMS
- retronic, retrocausal, retrocausality, temporal inversion
- backwards causation, backwards, reverse time, time reversal
- future determination, future determines, predetermined future

### ESCHATOLOGY_TERMS
- eschaton, eschatological, apocalypse, apocalyptic
- end-times, end times, final days, destiny
- inevitable, inexorable, fate, fated, teleology

### DIAGRAM_AUTHORITY_TERMS
- diagram, diagrammatic, authority, command, commands
- determines, override, overrides, control, controls
- exert, exerts, dictate, dictates, teleology, teleological

### AGENCY_TERMS
- agency, will, free will, choice, choose, subject
- subjective, subjectivity, control, autonomy, autonomous
- self-determination, self-directed

## Design Principles

1. **Sovereignty First**: Protect user epistemic agency above all
2. **De-escalation**: High-risk patterns trigger protective responses
3. **Deterministic**: All operations reproducible and auditable
4. **Provenance**: Full audit trail for every classification
5. **Four-Dimensional**: Independent classification across 4 dimensions
6. **Backward Compatible**: Existing pipelines unaffected when disabled
7. **Typed**: Strict pydantic validation everywhere
8. **Cached**: Results cached by text hash for efficiency

## Thresholds and Tuning

Current thresholds (adjustable in `classifier.py`):

```python
# Temporal Mode
INVERTED_THRESHOLD = 0.15        # retronic_score >= 0.15
ESCHATOLOGICAL_THRESHOLD = 0.15  # eschatology_score >= 0.15
CYCLIC_THRESHOLD = 0.10          # Cyclic pattern detection

# Diagram Role
COMMANDING_THRESHOLD = 0.20      # diagram_authority >= 0.20
AUTHORITATIVE_THRESHOLD = 0.10   # diagram_authority >= 0.10

# Sovereignty Risk thresholds built into combination logic
```

## Maintenance

### Adding New Lexemes

1. Add terms to lexeme groups in `features.py`
2. Run tests to verify determinism maintained
3. Update expected test results if needed

### Extending Classification

1. Add new enum values to `models.py`
2. Update classification logic in `classifier.py`
3. Update operator mapping in `determine_operator_hits()`
4. Add tests for new classifications
5. Update documentation

### Tuning Thresholds

Adjust thresholds in `classifier.py`:
- `classify_temporal_mode()`: Temporal mode thresholds
- `classify_diagram_role()`: Authority thresholds
- `classify_sovereignty_risk()`: Risk escalation logic

## References

- Main SEE integration: `abraxas/slang/engine.py:189-217`
- OAS validator extension: `abraxas/oasis/validator.py:334-431`
- OAS canonizer gate: `abraxas/oasis/canonizer.py:259-281`
- Cluster model extension: `abraxas/slang/models.py:56-60`

## De-escalation Protocol

When sovereignty_risk >= HIGH:

1. Cluster tagged with `response_mode = "de-escalate"`
2. Downstream systems MUST respect de-escalation directive
3. No reinforcement of authority claims
4. Frame as perspective rather than truth
5. Emphasize user agency and epistemic sovereignty

**Example De-escalation Responses**:
- "This is one perspective on temporal causality..."
- "You maintain autonomy in interpreting these claims..."
- "Your agency is not constrained by these patterns..."

## Support

For issues or questions about TDD integration, see:
- Test suite for usage examples
- Source code for implementation details
- This README for architecture overview
- VBM casebook README for parallel structure
