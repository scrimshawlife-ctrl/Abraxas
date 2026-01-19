# Neon-Genie ABX-Runes Adapter Integration Guide

**Version:** 0.1.0
**Status:** Runtime Bridge Ready (awaiting external overlay integration)
**Capability ID:** `aal.neon_genie.generate.v0`

---

## Overview

The Neon-Genie adapter enables Abraxas to invoke Neon-Genie as an external symbolic generation overlay through ABX-Runes capability contracts. This integration follows strict governance principles to ensure Neon-Genie operates as an observation/generation layer without influencing forecasts.

### Key Principles

1. **Dual-Lane Principle**: Neon-Genie runs in OBSERVATION/GENERATION lane only
2. **No Influence Guarantee**: Outputs never fed into forecast weights
3. **Incremental Patch Only**: No cross-repo imports or codebase merging
4. **Provenance Tracking**: All outputs include SHA-256 tracked provenance
5. **Artifact Storage**: Results stored as deterministic artifacts
6. **Module/Overlay Separation**: Core modules (e.g., AALmanac) never import overlays directly

---

## Architecture

### Component Structure

```
abraxas/aal/                           # AAL (Abraxas Almanac Layer)
├── __init__.py                         # Package exports
├── neon_genie_adapter.py               # Rune adapter (thin wrapper)
└── artifact_handler.py                 # Artifact storage handler

schemas/capabilities/                   # JSON schemas for validation
├── neon_genie_input.schema.json       # Input validation schema
└── neon_genie_output.schema.json      # Output validation schema

abraxas/runes/registry.json             # Capability registry (updated)

tests/test_neon_genie_adapter.py        # Comprehensive test suite
```

### Data Flow

```
┌─────────────────────────────────────────────────────────┐
│                   Abraxas Core System                    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  ABX-Runes Invocation Layer                    │    │
│  │  invoke_capability("aal.neon_genie.generate.v0")│    │
│  └──────────────────┬─────────────────────────────┘    │
│                     │                                    │
│  ┌──────────────────▼─────────────────────────────┐    │
│  │  Neon-Genie Rune Adapter                       │    │
│  │  (abraxas/aal/neon_genie_adapter.py)           │    │
│  │  • Validates inputs                            │    │
│  │  • Calls _invoke_neon_genie_overlay() bridge  │    │
│  │  • Wraps result in canonical envelope          │    │
│  │  • Tags with no_influence=True                 │    │
│  └──────────────────┬─────────────────────────────┘    │
│                     │                                    │
│  ┌──────────────────▼─────────────────────────────┐    │
│  │  Artifact Storage Handler                      │    │
│  │  (abraxas/aal/artifact_handler.py)             │    │
│  │  • Stores generation results                   │    │
│  │  • Enforces no_influence=True                  │    │
│  │  • Tracks SHA-256 provenance                   │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘

                            │
                            │ (External invocation)
                            ▼

┌─────────────────────────────────────────────────────────┐
│               Neon-Genie Overlay (External)              │
│                     (Not Yet Integrated)                 │
│  • Receives prompt + context via overlay runtime        │
│  • Generates symbolic output                            │
│  • Returns result through overlay interface             │
└─────────────────────────────────────────────────────────┘
```

---

## Separation Boundaries

Core modules (e.g., AALmanac) must remain isolated from overlay integrations. Overlays are invoked via the overlay runtime and never imported directly into core modules. See `docs/overlay_contract.md` for the universal separation gates and initialization workflow used across all overlays.

---

## Usage

### Basic Invocation

```python
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext

# Create invocation context
ctx = RuneInvocationContext(
    run_id="RUN-001",
    subsystem_id="abx.mymodule",
    git_hash="unknown"
)

# Invoke Neon-Genie capability
result = invoke_capability(
    capability="aal.neon_genie.generate.v0",
    inputs={
        "prompt": "Generate a symbolic representation of emergent patterns",
        "context": {
            "term": "emergence",
            "motif": "cascade",
            "mode": "symbolic"
        },
        "seed": 42  # For determinism
    },
    ctx=ctx,
    strict_execution=False  # Allow external overlay to be missing
)

# Extract results
generated_output = result["generated_output"]
provenance = result["provenance"]
metadata = result["metadata"]

# Verify no-influence guarantee
assert metadata["no_influence"] is True
assert metadata["lane"] in ["OBSERVATION", "GENERATION"]
```

### Storing Results as Artifacts

```python
from abraxas.aal.artifact_handler import store_neon_genie_result

# Store generation result
artifact_record = store_neon_genie_result(
    run_id="RUN-001",
    tick=1,
    generation_result=result,
    prompt="Generate a symbolic representation of emergent patterns"
)

# Artifact record includes:
# - artifact_path: Path to stored JSON file
# - sha256: SHA-256 hash of artifact
# - bytes: File size
# - no_influence: True (enforced)
```

### Direct Adapter Usage

```python
from abraxas.aal.neon_genie_adapter import generate_symbolic_v0

# Generate symbolic output
result = generate_symbolic_v0(
    prompt="Generate a symbolic representation of truth",
    context={
        "term": "truth",
        "motif": "cascade",
        "constraints": {"style": "glyph", "format": "svg"}
    },
    config={"max_length": 1000},
    seed=42
)

# Handle not_computable case (overlay not available)
if result["not_computable"] is not None:
    print(f"Generation failed: {result['not_computable']['reason']}")
else:
    print(f"Generated: {result['generated_output']}")
```

---

## Integration Checklist

### Current Status (v0.1.0 - Runtime Bridge Ready)

- ✅ Rune adapter created with provenance wrapping
- ✅ Capability registered in `abraxas/runes/registry.json`
- ✅ Input/output JSON schemas defined
- ✅ Artifact storage handler with no-influence validation
- ✅ Comprehensive test suite (11 tests, all passing)
- ✅ Determinism verification tests
- ✅ Overlay runtime bridge implemented (`check_overlay_available`, `invoke_overlay`)
- ⚠️ **EXTERNAL OVERLAY MISSING**: `_invoke_neon_genie_overlay()` returns `None` until Neon-Genie is available

### Next Steps for Full Integration

1. **External Overlay Setup** (Priority: P0)
   - Follow the overlay initialization workflow in `docs/overlay_contract.md` (Section F).  
   - Install the external Neon-Genie overlay package (extras group).  
   - Register the overlay module path in `abraxas/overlays/dispatcher.py`.  
   - Ensure `check_overlay_available("neon_genie")` returns `True`.  
   - Test end-to-end invocation with a real Neon-Genie instance.

2. **Golden Tests** (Priority: P2)
   - Add golden test with known prompt → known output
   - Verify deterministic generation with fixed seed
   - Test provenance hash stability

3. **Documentation** (Priority: P2)
   - Add Neon-Genie integration example to `examples/`
   - Update CLAUDE.md with Neon-Genie adapter section
   - Document overlay registration workflow

---

## Implementation: Overlay Bridge

`_invoke_neon_genie_overlay()` now routes through the overlay runtime bridge. Complete the external overlay setup (P0) to make the invocation live:

```python
def _invoke_neon_genie_overlay(
    prompt: str,
    context: dict,
    config: dict,
    seed: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Invoke Neon-Genie overlay through overlay runtime interface.

    Implementation Steps:
    1. Check overlay availability
    2. Prepare overlay request payload
    3. Invoke overlay through runtime interface
    4. Extract and return generated output
    """
    try:
        from abraxas.overlay.run import check_overlay_available, invoke_overlay

        # Check availability
        if not check_overlay_available("neon_genie", version="v0"):
            return None

        # Prepare payload
        overlay_payload = {
            "prompt": prompt,
            "context": context,
            "seed": seed,
            **config
        }

        # Invoke overlay
        response = invoke_overlay(
            overlay_name="neon_genie",
            version="v0",
            phase="ASCEND",  # Generation happens in ASCEND phase
            payload=overlay_payload
        )

        # Extract result
        if response.get("ok"):
            return response.get("output", {}).get("result")
        else:
            # Overlay returned error
            return None

    except Exception:
        # Overlay invocation failed
        return None
```

---

## Testing

### Run Tests

```bash
# Run all Neon-Genie adapter tests
pytest tests/test_neon_genie_adapter.py -v

# Run with coverage
pytest tests/test_neon_genie_adapter.py --cov=abraxas.aal --cov-report=term-missing

# Run specific test
pytest tests/test_neon_genie_adapter.py::test_generate_symbolic_v0_successful_generation -v
```

### Test Coverage

Current test suite covers:
- ✅ Missing prompt validation
- ✅ Overlay not available (external overlay missing)
- ✅ Overlay invocation errors
- ✅ Successful generation with provenance
- ✅ Deterministic hash verification
- ✅ Context mode variations
- ✅ Artifact storage and retrieval
- ✅ No-influence flag enforcement
- ✅ Artifact listing by run_id

---

## Schema Validation

### Input Schema

Location: `schemas/capabilities/neon_genie_input.schema.json`

Required fields:
- `prompt` (string, min length 1): Generation prompt text

Optional fields:
- `context` (object): Generation context with term, motif, constraints, mode
- `config` (object): Configuration options (max_length, temperature, overlay_version)
- `seed` (integer): Deterministic seed

### Output Schema

Location: `schemas/capabilities/neon_genie_output.schema.json`

Success response:
- `generated_output` (object/string): Generated symbolic output
- `provenance` (object): SHA-256 tracked provenance
- `metadata` (object): Must include `no_influence=true` and `lane="OBSERVATION|GENERATION"`

Error response:
- `not_computable` (object): Error reason and missing inputs
- `metadata` (object): Still includes `no_influence=true`

---

## Governance Compliance

### Dual-Lane Enforcement

All Neon-Genie outputs are tagged with:
```json
{
  "metadata": {
    "no_influence": true,
    "lane": "OBSERVATION",
    "artifact_only": true
  }
}
```

This ensures:
- ❌ Outputs never used in forecast scoring
- ❌ Outputs never fed into prediction weights
- ✅ Outputs stored as artifacts only
- ✅ Outputs tracked with SHA-256 provenance

### Artifact Storage Validation

The artifact handler enforces `no_influence=True`:

```python
# This will raise ValueError
handler.store_generation_result(
    run_id="RUN-001",
    tick=1,
    prompt="Test",
    generated_output={"text": "Output"},
    provenance=provenance,
    metadata={"no_influence": False}  # ❌ VIOLATION
)
```

---

## Troubleshooting

### Common Issues

**Issue**: `Neon-Genie overlay not yet integrated (stub mode)`

**Solution**: The runtime bridge is in place, but the external Neon-Genie overlay is not installed or not discoverable by the overlay runtime. Complete the external setup to resolve this.

---

**Issue**: `TypeError: ArtifactWriter.__init__() got an unexpected keyword argument 'base_dir'`

**Solution**: Use `artifacts_dir` parameter instead of `base_dir`:
```python
writer = ArtifactWriter(artifacts_dir=str(path))
```

---

**Issue**: Neon-Genie outputs affecting forecasts

**Solution**: This should be impossible. The artifact handler enforces `no_influence=True` at storage time. If this occurs, file a critical bug report - this is a governance violation.

---

## References

- **ABX-Runes Coupling Guide**: `docs/migration/abx_runes_coupling.md`
- **Capability Contracts**: `abraxas/runes/registry.json`
- **Artifact Storage**: `abraxas/runtime/artifacts.py`
- **Overlay Runtime**: `abraxas/overlay/run.py`
- **Test Suite**: `tests/test_neon_genie_adapter.py`

---

## Changelog

### v0.1.0 (2026-01-18)

**Initial Release - Runtime Bridge Ready**

- ✅ Created rune adapter with provenance wrapping
- ✅ Registered `aal.neon_genie.generate.v0` capability
- ✅ Added input/output JSON schemas
- ✅ Created artifact storage handler with no-influence enforcement
- ✅ Added comprehensive test suite (11 tests)
- ✅ Verified determinism and governance compliance
- ✅ Overlay runtime bridge implemented (`check_overlay_available`, `invoke_overlay`)
- ⚠️ **EXTERNAL OVERLAY MISSING**: `_invoke_neon_genie_overlay()` returns `None` (awaiting external overlay)

**Next Release**: Complete external overlay setup and add golden tests.

---

**End of Integration Guide**
