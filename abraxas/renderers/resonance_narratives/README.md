# Resonance Narratives Renderer v1

**Status**: Production-ready
**Schema Version**: v1
**Created**: 2025-12-30

## Purpose

Converts Oracle v2 envelopes into human-readable narrative bundles with full pointer-based auditability. Think: "compress signal," not "invent story."

## Core Principles

1. **No Invention**: Every statement maps to an envelope field via JSON Pointer
2. **Evidence Gating**: No claims without evidence - if data is missing, narrative acknowledges it
3. **Deterministic**: Same envelope → same narrative bytes (canonical JSON sort)
4. **Diff-Friendly**: Structured output, not prose soup

## Contract

```python
render(envelope_v2) -> narrative_bundle_v1
```

## Usage

### Basic Rendering

```python
from abraxas.renderers.resonance_narratives import render_narrative_bundle

# Render Oracle v2 envelope to narrative bundle
bundle = render_narrative_bundle(envelope)

# Bundle contains:
# - headline (1-line summary)
# - signal_summary (key signals with pointers)
# - motifs (recurring patterns with strength scores)
# - provenance_footer (input_hash, created_at, source_count)
# - constraints_report (missing_inputs, not_computable, evidence_present)
```

### Diff Mode

```python
from abraxas.renderers.resonance_narratives import render_narrative_bundle_with_diff

# Compare current vs previous envelope
bundle = render_narrative_bundle_with_diff(
    envelope=current_envelope,
    previous_envelope=previous_envelope
)

# Bundle includes what_changed[] with:
# - pointer (to changed field)
# - change_description (human-readable)
# - before/after values
```

## Output Schema

### Narrative Bundle Structure

```json
{
  "schema_version": "v1",
  "artifact_id": "NARR-abc12345",
  "headline": "SNAPSHOT Oracle (GREEN): 3 vital, 2 risk signals [day]",
  "signal_summary": [
    {
      "label": "Time Window",
      "value": "2025-12-29T00:00:00Z to 2025-12-30T00:00:00Z (day)",
      "pointer": "/oracle_signal/window"
    },
    {
      "label": "Compliance Status",
      "value": "GREEN",
      "pointer": "/oracle_signal/v2/compliance/status"
    }
  ],
  "motifs": [
    {
      "motif": "ghostmode",
      "strength": 0.8556,
      "pointer": "/oracle_signal/scores_v1/slang/top_vital/0"
    }
  ],
  "overlay_notes": [],
  "provenance_footer": {
    "input_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "created_at": "2025-12-30T12:00:00Z",
    "source_count": 42,
    "commit": "abc123def456"
  },
  "constraints_report": {
    "missing_inputs": [],
    "not_computable": ["v2_scores (not present in envelope)"],
    "evidence_present": false,
    "warnings": []
  }
}
```

## Rendering Rules

### Whitelisted Pointers

Only pre-approved JSON pointers are referenced. See `rules.py` for the full whitelist.

**Allowed pointer prefixes**:
- `/oracle_signal/window/*`
- `/oracle_signal/scores_v1/slang/*`
- `/oracle_signal/scores_v1/aalmanac/*`
- `/oracle_signal/v2/mode`
- `/oracle_signal/v2/compliance/*`
- `/oracle_signal/v2/scores_v2/*`
- `/oracle_signal/evidence/*`
- `/oracle_signal/meta/*`

### Forbidden Phrases (Without Evidence)

Causal language is prohibited unless evidence pointers exist:
- "because"
- "caused by"
- "this means"
- "therefore"
- "as a result"
- "consequently"
- "due to"

## Testing

Comprehensive test suite covers:

1. **Determinism**: Same input → same output
2. **Schema Validation**: Output validates against JSON schema
3. **Pointer Integrity**: All pointers resolve in envelope
4. **Evidence Gating**: Missing data removes dependent narrative lines
5. **Missing Input Discipline**: No synthesis of missing values

Run tests:
```bash
pytest tests/test_resonance_narratives_*.py -v
```

**Test Coverage**: 41 tests, all passing

## Files

```
abraxas/renderers/resonance_narratives/
├── __init__.py              # Public API exports
├── renderer.py              # Core rendering logic
├── rules.py                 # Whitelists & constraints
└── README.md                # This file

schemas/renderers/resonance_narratives/v1/
└── narrative_bundle.schema.json  # JSON schema v1

tests/
├── test_resonance_narratives_determinism.py
├── test_resonance_narratives_schema.py
├── test_resonance_narratives_pointer_integrity.py
├── test_resonance_narratives_evidence_gating.py
├── test_resonance_narratives_missing_input.py
└── test_resonance_narratives_diff_mode.py

tests/fixtures/resonance_narratives/
├── envelopes/
│   ├── baseline.json
│   ├── baseline_updated.json
│   ├── with_evidence.json
│   └── missing_inputs.json
└── expected/               # (Future golden outputs)
```

## Anti-Patterns Avoided

✗ **Freeform prose paragraphs** as primary output (hard to diff, hard to audit)
✗ **Causal claims** without explicit evidence fields
✗ **Live web data** pulled inside renderer (renderer is offline-pure)
✗ **Pointer invention** - all pointers must resolve in envelope
✗ **Value synthesis** - missing data acknowledged, never fabricated

## Integration Example

```python
from abraxas.oracle.v2 import run_oracle_v2
from abraxas.renderers.resonance_narratives import render_narrative_bundle

# Run Oracle v2
envelope = run_oracle_v2(observations)

# Render to narrative
narrative = render_narrative_bundle(envelope)

# Use narrative for human consumption
print(narrative["headline"])
for signal in narrative["signal_summary"]:
    print(f"  {signal['label']}: {signal['value']}")
    print(f"    → {signal['pointer']}")
```

## Future Enhancements (v2 Candidates)

- [ ] Motif clustering (group related patterns)
- [ ] Temporal trajectory annotations (how signals evolved)
- [ ] Evidence chain visualization (link narrative to source data)
- [ ] Multi-language headline generation
- [ ] Adaptive detail level (summary vs full narrative)

## Provenance

**Author**: Claude (via Abraxas AI development)
**Spec Source**: OPEN → ALIGN → ASCEND → CLEAR → SEAL framework
**First Deploy**: 2025-12-30
**Schema Stability**: v1 locked, future changes require v2 schema
