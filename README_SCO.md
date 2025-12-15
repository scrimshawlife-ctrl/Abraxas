# Abraxas Symbolic Compression Stack (SCO/ECO)

Deterministic, modular, provenance-embedded linguistic compression detection system.

## Architecture

```
abraxas/
├── __init__.py
├── operators/
│   ├── __init__.py
│   └── symbolic_compression.py    # SCO/ECO operator
├── linguistic/
│   ├── __init__.py
│   ├── phonetics.py               # Soundex encoding
│   ├── similarity.py              # Edit distance, phonetic similarity, intent scores
│   ├── tokenize.py                # Token extraction, n-grams
│   ├── transparency.py            # Symbolic Transparency Index (STI)
│   └── rdv.py                     # Replacement Direction Vector (RDV)
├── pipelines/
│   ├── __init__.py
│   └── sco_pipeline.py            # End-to-end processing pipeline
├── storage/
│   ├── __init__.py
│   └── events.py                  # JSONL event persistence
└── cli/
    ├── __init__.py
    └── sco_run.py                 # CLI interface

tests/
├── __init__.py
├── test_phonetics.py
├── test_similarity.py
├── test_transparency.py
├── test_operator.py
├── test_pipeline.py
├── records.json                   # Sample input data
└── lexicon.json                   # Sample lexicon
```

## Key Concepts

### Symbolic Compression Event (SCE)
Detected instance where an opaque symbol is replaced by a semantically transparent substitute while preserving intent.

**Metrics:**
- **STI** (Symbolic Transparency Index): 0-1 scale of semantic legibility
- **CP** (Compression Pressure): How strongly the system favors replacement
- **IPS** (Intent Preservation Score): Context similarity before/after
- **SLC** (Symbolic Load Capacity): Inverse of transparency
- **RDV** (Replacement Direction Vector): Affective/tonal shift axes

**Tiers:**
- **ECO_T1** (Eggcorn): High phonetic similarity (≥0.85) + high transparency delta (≥0.18)
- **SCO_T2** (General symbolic compression): Passes thresholds but lower metrics

### Thresholds
- Phonetic similarity: ≥0.75
- Transparency delta: ≥0.12
- Intent preservation: ≥0.70

## Usage

### Command Line

```bash
python -m abraxas.cli.sco_run \
  --records tests/records.json \
  --lexicon tests/lexicon.json \
  --out sco_events.jsonl \
  --domain music
```

### Python API

```python
from abraxas.linguistic.transparency import TransparencyLexicon
from abraxas.pipelines.sco_pipeline import SCOPipeline

# Build transparency lexicon
lexicon = [
    {"canonical": "aphex twin", "variants": ["aphex twins", "apex twin"]}
]
tokens = ["aphex twin", "aphex twins", "apex twin"]
transparency = TransparencyLexicon.build(tokens)

# Run pipeline
records = [
    {"id": "1", "text": "I love Aphex Twins."},
    {"id": "2", "text": "Apex Twin is a legend."}
]
pipe = SCOPipeline(transparency)
events = pipe.run(records, lexicon, domain="music")

# Process events
for e in events:
    print(f"{e.tier}: {e.original_token} → {e.replacement_token}")
    print(f"  CP={e.compression_pressure}, STI={e.symbolic_transparency_index}")
```

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_operator.py

# Test CLI
python -m abraxas.cli.sco_run \
  --records tests/records.json \
  --lexicon tests/lexicon.json \
  --out /tmp/test_events.jsonl
```

## Event Format

Each event in the JSONL output contains:

```json
{
  "event_type": "SymbolicCompressionEvent",
  "tier": "ECO_T1",
  "original_token": "aphex twin",
  "replacement_token": "aphex twins",
  "domain": "music",
  "phonetic_similarity": 0.95,
  "semantic_transparency_delta": 0.22,
  "intent_preservation_score": 0.87,
  "compression_pressure": 1.42,
  "symbolic_transparency_index": 0.45,
  "symbolic_load_capacity": 0.55,
  "replacement_direction_vector": {
    "humor": 0.0,
    "aggression": 0.0,
    "authority": 0.0,
    "intimacy": 0.6,
    "nihilism": 0.0,
    "irony": 0.0
  },
  "observed_frequency": 12,
  "status": "emergent",
  "provenance_sha256": "a1b2c3..."
}
```

## Dependencies

- Python 3.11+
- No external dependencies required for core functionality
- pytest (optional, for testing)

## Integration with Abraxas Ecosystem

The SCO stack is designed to integrate with:
- **Weather Engine**: Symbolic drift as memetic weather pattern
- **Slang Model**: Compression events as linguistic evolution markers
- **AAlmanac**: Event logs for provenance tracking
- **Oracle**: Compression pressure as signal input

## Provenance

Every event includes a deterministic SHA-256 hash ensuring:
- Reproducibility across runs
- Auditability of detection logic
- Version tracking for transparency lexicons
