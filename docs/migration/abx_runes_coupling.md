# ABX-Runes Coupling Migration Guide

**Version:** 2.0.0
**Last Updated:** 2026-01-04
**Status:** Active

## Overview

This guide explains how to migrate from direct `abx → abraxas` imports to ABX-Runes capability contracts.

**Why migrate?**
- ✅ **Determinism**: All inputs/outputs validated against JSON schemas
- ✅ **Provenance**: Every invocation tracked with SHA-256 hashes
- ✅ **Testability**: Subsystems can be tested independently
- ✅ **Deployability**: Enables multi-process architecture
- ✅ **Governance**: Policy enforcement at capability boundary

## Migration Checklist

### Step 1: Identify Direct Imports

Find all files with direct `abraxas.*` imports:

```bash
# Find violations in abx/ directory
grep -r "from abraxas\." abx/ --include="*.py" | \
  grep -v "abraxas.runes" | \
  grep -v "abraxas.core.provenance"
```

**Example output:**
```
abx/a2_phase.py:from abraxas.evolve.non_truncation import enforce_non_truncation
abx/a2_phase.py:from abraxas.evidence.lift import load_bundles_from_index
abx/a2_phase.py:from abraxas.memetic.metrics_reduce import reduce_provenance_means
```

### Step 2: Find or Create Capability Contract

Check if a capability already exists:

```python
from abraxas.runes.capabilities import load_capability_registry

registry = load_capability_registry()

# List all oracle capabilities
oracle_caps = registry.list_by_prefix("oracle.")
print([cap.capability_id for cap in oracle_caps])

# Check specific capability
cap = registry.find_capability("oracle.v2.run")
if cap:
    print(f"Found: {cap.rune_id} at {cap.operator_path}")
```

**If capability doesn't exist**, create it:

1. **Define JSON schemas** (`schemas/capabilities/`)
2. **Create rune adapter** (thin wrapper in subsystem)
3. **Register in registry.json**

See examples in:
- `abraxas/oracle/v2/rune_adapter.py`
- `schemas/capabilities/oracle_run_input.schema.json`
- `schemas/capabilities/oracle_run_output.schema.json`

### Step 3: Replace Import with Invocation

**Before (Direct Import):**
```python
# abx/mymodule.py
from abraxas.oracle.v2.pipeline import run_oracle

def process_observations(obs, config):
    result = run_oracle(
        run_id="RUN-001",
        observations=obs,
        config=config
    )
    return result["terms"]
```

**After (Capability Invocation):**
```python
# abx/mymodule.py
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext

def process_observations(obs, config):
    # Create invocation context
    ctx = RuneInvocationContext(
        run_id="RUN-001",
        caller="abx.mymodule",
        environment="production"
    )

    # Invoke via capability contract
    result = invoke_capability(
        capability="oracle.v2.run",
        inputs={
            "run_id": "RUN-001",
            "observations": obs,
            "config": config,
            "seed": 42  # Always provide seed for determinism
        },
        ctx=ctx,
        strict_execution=True
    )

    # Extract with provenance tracking
    oracle_output = result["oracle_output"]
    provenance = result["provenance"]

    # Log provenance for audit trail
    print(f"Invoked oracle.v2.run: {provenance['config_sha256'][:8]}...")

    return oracle_output["terms"]
```

### Step 4: Add Golden Test

Every migrated module should have a golden test proving determinism:

```python
# tests/test_mymodule_determinism.py
def test_process_observations_determinism():
    """Same inputs must produce identical outputs."""

    observations = [
        {"term": "test", "context": "example", "timestamp": "2026-01-01T00:00:00Z"},
    ]
    config = {"domain": "test", "max_terms": 10}

    # Run twice with same inputs
    result1 = process_observations(observations, config)
    result2 = process_observations(observations, config)

    # Outputs must be identical
    assert result1 == result2
```

### Step 5: Update Coupling Lint

Run the coupling lint test to verify violation count decreased:

```bash
pytest tests/test_coupling_lint.py -v
```

The test tracks total violations and ensures they decrease over time:

```python
# Target: 0 violations after all migrations
assert len(violations) <= 34, f"ABX→Abraxas coupling violations: {len(violations)} (target: 0)"
```

## Common Migration Patterns

### Pattern 1: Simple Function Call

**Before:**
```python
from abraxas.memetic.metrics_reduce import reduce_provenance_means

means = reduce_provenance_means(profiles)
```

**After:**
```python
from abraxas.runes.invoke import invoke_capability

result = invoke_capability(
    capability="memetic.metrics_reduce",
    inputs={"profiles": profiles},
    ctx=ctx
)
means = result["means"]
```

### Pattern 2: Multiple Calls

**Before:**
```python
from abraxas.evidence.lift import load_bundles_from_index, term_lift

bundles = load_bundles_from_index(index_path)
lifted = term_lift(bundles, term="example")
```

**After:**
```python
# Call 1: Load bundles
bundles_result = invoke_capability(
    capability="evidence.load_bundles",
    inputs={"index_path": index_path},
    ctx=ctx
)
bundles = bundles_result["bundles"]

# Call 2: Term lift
lift_result = invoke_capability(
    capability="evidence.term_lift",
    inputs={"bundles": bundles, "term": "example"},
    ctx=ctx
)
lifted = lift_result["lifted_terms"]
```

### Pattern 3: Error Handling

**Before:**
```python
try:
    result = run_oracle(observations, config)
except Exception as e:
    log.error(f"Oracle failed: {e}")
    return None
```

**After:**
```python
try:
    result = invoke_capability(
        capability="oracle.v2.run",
        inputs={"observations": observations, "config": config},
        ctx=ctx
    )

    # Check if computable
    if result.get("not_computable"):
        log.warning(f"Oracle not computable: {result['not_computable']['reason']}")
        return None

    oracle_output = result["oracle_output"]

except PermissionError as e:
    log.error(f"Oracle access denied: {e}")
    return None
```

## Available Capabilities (as of 2026-01-04)

| Capability ID | Status | Description |
|--------------|--------|-------------|
| `oracle.v2.run` | ✅ Live | Oracle V2 pipeline execution |
| `memetic.temporal_profiles` | 🚧 Planned | Temporal profile building |
| `memetic.metrics_reduce` | 🚧 Planned | Provenance mean reduction |
| `evidence.load_bundles` | 🚧 Planned | Evidence bundle loading |
| `forecast.term_classify` | 🚧 Planned | Term classification |

*(See `abraxas/runes/registry.json` for complete list)*

## Troubleshooting

### Error: "No rune registered for capability"

**Cause:** Capability not yet registered.

**Solution:** Create the capability contract (Steps 2-3 above) or check spelling.

### Error: "Payload validation failed"

**Cause:** Input doesn't match JSON schema.

**Solution:** Check schema requirements:
```python
import json
from pathlib import Path

schema_path = Path("schemas/capabilities/oracle_run_input.schema.json")
schema = json.loads(schema_path.read_text())
print(json.dumps(schema, indent=2))
```

### Error: "Shadow lane access denied"

**Cause:** Attempting to access shadow metrics without ϟ₇ SSO rune.

**Solution:** Shadow metrics are observe-only. Don't access directly. Use prediction lane capabilities instead.

## Best Practices

1. **Always provide `seed` parameter** for deterministic operations
2. **Log provenance hashes** for audit trail
3. **Handle `not_computable` gracefully** - it's not an error, it's expected
4. **Test determinism** with golden tests
5. **Use strict_execution=True** in production code

## Migration Progress Tracking

Track your progress:

```bash
# Count remaining violations
grep -r "from abraxas\." abx/ --include="*.py" | \
  grep -v "abraxas.runes" | \
  grep -v "abraxas.core.provenance" | \
  wc -l

# Goal: 0
```

## Questions?

- See `CLAUDE.md` for developer guidelines
- Check `abraxas/runes/README.md` for rune system documentation
- Review example migrations in recent commits (search for "capability" in git log)

---

**End of Migration Guide**
