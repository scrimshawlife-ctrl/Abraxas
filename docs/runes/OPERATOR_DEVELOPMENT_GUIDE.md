# Rune Operator Development Guide

**Version:** 1.0.0  
**Last Updated:** 2026-01-11  
**Purpose:** Complete guide to converting auto-generated rune operator stubs into production implementations

---

## Table of Contents

1. [Overview](#overview)
2. [Rune Operator Lifecycle](#rune-operator-lifecycle)
3. [Understanding Auto-Generated Stubs](#understanding-auto-generated-stubs)
4. [Implementation Steps](#implementation-steps)
5. [Testing Requirements](#testing-requirements)
6. [Provenance & Determinism](#provenance--determinism)
7. [Example: WSSS Implementation](#example-wsss-implementation)
8. [Capability Contract Integration](#capability-contract-integration)
9. [Common Patterns](#common-patterns)
10. [Troubleshooting](#troubleshooting)

---

## Overview

Abraxas uses **ABX-Runes** for cross-subsystem communication via capability contracts. Runes are symbolic operators that process signals while maintaining strict determinism and provenance tracking.

### What is a Rune Operator?

A **rune operator** is a deterministic function that:
- Takes structured inputs (state, context, signals)
- Applies domain-specific transformations
- Returns structured outputs with provenance metadata
- Never mutates external state
- Always produces identical outputs for identical inputs

### Operator Lifecycle

```
AUTO-GENERATED STUB
        ↓
    IMPLEMENTATION (this guide)
        ↓
    TESTING (golden tests + determinism)
        ↓
    CAPABILITY REGISTRATION
        ↓
    PRODUCTION USE
```

---

## Rune Operator Lifecycle

### Phase 1: Stub Generation (Done)

Auto-generated stubs are created from canonical rune definitions with:
- Docstring with rune metadata (name, layer, motto, provenance)
- Function signature with type hints
- Stub implementation that raises `NotImplementedError` in strict mode
- Placeholder return values (all `None`)

**Example stub:**
```python
def apply_wsss(signal_amplitude, structural_coherence, pattern_matrix, *, strict_execution=False):
    """Apply WSSS rune operator."""
    if strict_execution:
        raise NotImplementedError("Operator WSSS not implemented yet.")
    
    # Stub implementation - returns empty outputs
    return {
        "structure_score": None,
        "signal_quality": None,
        "validation_result": None,
    }
```

---

### Phase 2: Implementation (Your Task)

Replace stub logic with real implementation:
1. **Understand the rune's purpose** from docstring
2. **Implement core logic** based on canonical statement
3. **Add input validation** with clear error messages
4. **Compute outputs deterministically** (no randomness, no timestamps)
5. **Include provenance metadata** (SHA-256 hashes)
6. **Handle edge cases** (missing inputs, invalid ranges)

---

### Phase 3: Testing (Required)

Every rune operator MUST have:
1. **Unit tests** - Test each output with various inputs
2. **Golden tests** - Verify deterministic output stability
3. **Determinism tests** - Run twice, compare hashes
4. **Strict execution tests** - Verify no `NotImplementedError`
5. **Edge case tests** - Test boundary conditions

---

### Phase 4: Integration (Capability Contract)

Register the operator in the capability registry:
1. Add capability entry to `abraxas/runes/registry.json`
2. Create rune adapter if needed
3. Update migration docs with new capability
4. Run coupling lint to verify no direct imports

---

## Understanding Auto-Generated Stubs

### Stub Anatomy

Every auto-generated stub has:

```python
"""ABX-Rune Operator: ϟ₃ WSSS

AUTO-GENERATED OPERATOR STUB
Rune: ϟ₃ WSSS — Weak Signal · Strong Structure  ← Rune name
Layer: Validation  ← Processing layer
Motto: Power does not persuade. Structure does.  ← Core principle

Canonical statement:  ← What the rune does
  Effects must scale with structure, not amplitude.

Function:  ← Detailed description
  Validates that effects scale with structural coherence...

Inputs: signal_amplitude, structural_coherence, pattern_matrix  ← Required inputs
Outputs: structure_score, signal_quality, validation_result  ← Expected outputs

Constraints:  ← Rules that must be enforced
  - effects_scale_with_structure
  - amplitude_not_sufficient
  - structure_must_be_measurable

Provenance:  ← Where the rune concept comes from
  - Signal processing theory
  - Structural validation frameworks
  - AAL anti-persuasion doctrine
"""
```

### Key Metadata

| Field | Purpose | How to Use |
|-------|---------|------------|
| **Rune Name** | Identifier (e.g., ϟ₃ WSSS) | Use in logging, docs |
| **Layer** | Processing stage | Determines when rune runs |
| **Motto** | Core principle | Guides implementation |
| **Canonical Statement** | What it does | Primary requirement |
| **Inputs** | Required parameters | Function args |
| **Outputs** | Return value keys | Dict keys in return |
| **Constraints** | Rules to enforce | Implementation logic |
| **Provenance** | Conceptual origins | Cite in docs, tests |

---

## Implementation Steps

### Step 1: Read and Understand

1. **Read the full docstring** - Understand the rune's purpose
2. **Identify the canonical statement** - This is your primary requirement
3. **List constraints** - These are hard rules that must be enforced
4. **Note provenance** - Understand the conceptual foundation

**Example (WSSS):**
- **Canonical statement:** "Effects must scale with structure, not amplitude"
- **Key constraint:** "amplitude_not_sufficient"
- **Meaning:** High amplitude signals with low structure should be rejected

---

### Step 2: Design the Algorithm

Based on the canonical statement and constraints, design your algorithm:

1. **Input validation** - Check for required inputs
2. **Normalization** - Convert inputs to standard ranges
3. **Core computation** - Apply the rune's logic
4. **Constraint checking** - Verify all constraints are satisfied
5. **Output generation** - Package results with provenance

**Example (WSSS pseudocode):**
```
1. Validate inputs exist (signal_amplitude, structural_coherence, pattern_matrix)
2. Normalize amplitude to [0, 1]
3. Compute structural_coherence from pattern_matrix
4. Check: structure_score must dominate amplitude (constraint: amplitude_not_sufficient)
5. Compute signal_quality = structural_coherence / (1 + signal_amplitude)
6. Return: structure_score, signal_quality, validation_result
```

---

### Step 3: Implement with Provenance

Replace the stub with real implementation:

```python
from abraxas.core.provenance import hash_canonical_json
import json

def apply_wsss(
    signal_amplitude: float,
    structural_coherence: float,
    pattern_matrix: list[list[float]],
    *,
    strict_execution: bool = False
) -> dict[str, Any]:
    """Apply WSSS rune operator - Weak Signal · Strong Structure.
    
    Validates that effects scale with structure, not amplitude.
    
    Args:
        signal_amplitude: Signal amplitude in [0, inf)
        structural_coherence: Structural coherence in [0, 1]
        pattern_matrix: NxN matrix of pattern correlations
        strict_execution: If True, raises errors for invalid inputs (unused after impl)
    
    Returns:
        Dict with keys:
            - structure_score: float in [0, 1]
            - signal_quality: float in [0, 1]
            - validation_result: "PASS" | "FAIL" | "NOT_COMPUTABLE"
            - provenance_hash: SHA-256 of inputs
    """
    # Step 1: Input validation
    if signal_amplitude < 0:
        return {
            "structure_score": 0.0,
            "signal_quality": 0.0,
            "validation_result": "NOT_COMPUTABLE",
            "error": "signal_amplitude must be >= 0",
            "provenance_hash": None,
        }
    
    if not (0 <= structural_coherence <= 1):
        return {
            "structure_score": 0.0,
            "signal_quality": 0.0,
            "validation_result": "NOT_COMPUTABLE",
            "error": "structural_coherence must be in [0, 1]",
            "provenance_hash": None,
        }
    
    if not pattern_matrix:
        return {
            "structure_score": 0.0,
            "signal_quality": 0.0,
            "validation_result": "NOT_COMPUTABLE",
            "error": "pattern_matrix cannot be empty",
            "provenance_hash": None,
        }
    
    # Step 2: Normalize amplitude to [0, 1] using log scaling
    normalized_amplitude = 1.0 / (1.0 + 1.0 / (1.0 + signal_amplitude))
    
    # Step 3: Compute structure score from pattern matrix
    # Structure = average correlation strength across pattern matrix
    total_correlation = sum(sum(row) for row in pattern_matrix)
    num_elements = len(pattern_matrix) * len(pattern_matrix[0])
    structure_score = total_correlation / num_elements if num_elements > 0 else 0.0
    structure_score = max(0.0, min(1.0, structure_score))  # Clamp to [0, 1]
    
    # Step 4: Compute signal quality (structure-to-amplitude ratio)
    # High structure + low amplitude = high quality (WSSS principle)
    signal_quality = structural_coherence / (1.0 + normalized_amplitude)
    signal_quality = max(0.0, min(1.0, signal_quality))  # Clamp to [0, 1]
    
    # Step 5: Validation result based on constraint "effects_scale_with_structure"
    # PASS if structure_score > normalized_amplitude (structure dominates)
    # FAIL if amplitude dominates structure
    if structure_score > normalized_amplitude:
        validation_result = "PASS"
    else:
        validation_result = "FAIL"
    
    # Step 6: Compute provenance hash
    inputs_canonical = {
        "signal_amplitude": signal_amplitude,
        "structural_coherence": structural_coherence,
        "pattern_matrix": pattern_matrix,
    }
    provenance_hash = hash_canonical_json(inputs_canonical)
    
    # Step 7: Return outputs
    return {
        "structure_score": structure_score,
        "signal_quality": signal_quality,
        "validation_result": validation_result,
        "provenance_hash": provenance_hash,
    }
```

**Key Implementation Principles:**
1. ✅ **Deterministic** - Same inputs always produce same outputs
2. ✅ **Input validation** - Graceful handling of invalid inputs
3. ✅ **Provenance tracking** - SHA-256 hash of inputs
4. ✅ **Constraint enforcement** - "effects_scale_with_structure" verified
5. ✅ **Type hints** - Clear types for all parameters and return values
6. ✅ **Docstring updated** - Describes actual behavior, not stub

---

### Step 4: Remove Strict Execution Guard

After implementing, the `strict_execution` parameter becomes unused:

**Before (stub):**
```python
if strict_execution:
    raise NotImplementedError("Operator WSSS not implemented yet.")
```

**After (implemented):**
```python
# strict_execution parameter kept for API compatibility but unused
# Implementation is now complete
```

---

## Testing Requirements

### Test File Structure

Create test file: `tests/test_rune_operators_wsss.py`

```python
"""Tests for WSSS rune operator (ϟ₃)."""

import pytest
from abraxas.runes.operators.wsss import apply_wsss


class TestWSSS:
    """Test suite for WSSS operator."""
    
    def test_basic_functionality(self):
        """Test basic WSSS computation."""
        result = apply_wsss(
            signal_amplitude=1.0,
            structural_coherence=0.8,
            pattern_matrix=[[0.9, 0.8], [0.8, 0.9]]
        )
        
        assert "structure_score" in result
        assert "signal_quality" in result
        assert "validation_result" in result
        assert "provenance_hash" in result
        
        assert 0 <= result["structure_score"] <= 1
        assert 0 <= result["signal_quality"] <= 1
        assert result["validation_result"] in ["PASS", "FAIL", "NOT_COMPUTABLE"]
    
    def test_high_structure_low_amplitude_passes(self):
        """Test that high structure + low amplitude passes validation (WSSS principle)."""
        result = apply_wsss(
            signal_amplitude=0.1,  # Low amplitude
            structural_coherence=0.9,  # High coherence
            pattern_matrix=[[1.0, 0.9], [0.9, 1.0]]  # High structure
        )
        
        assert result["validation_result"] == "PASS"
        assert result["structure_score"] > 0.8
    
    def test_high_amplitude_low_structure_fails(self):
        """Test that high amplitude + low structure fails validation."""
        result = apply_wsss(
            signal_amplitude=10.0,  # High amplitude
            structural_coherence=0.2,  # Low coherence
            pattern_matrix=[[0.1, 0.0], [0.0, 0.1]]  # Low structure
        )
        
        assert result["validation_result"] == "FAIL"
    
    def test_determinism(self):
        """Test that identical inputs produce identical outputs."""
        inputs = {
            "signal_amplitude": 2.5,
            "structural_coherence": 0.6,
            "pattern_matrix": [[0.5, 0.4], [0.4, 0.5]]
        }
        
        result1 = apply_wsss(**inputs)
        result2 = apply_wsss(**inputs)
        
        # All outputs should be identical
        assert result1["structure_score"] == result2["structure_score"]
        assert result1["signal_quality"] == result2["signal_quality"]
        assert result1["validation_result"] == result2["validation_result"]
        assert result1["provenance_hash"] == result2["provenance_hash"]
    
    def test_invalid_inputs(self):
        """Test handling of invalid inputs."""
        # Negative amplitude
        result = apply_wsss(
            signal_amplitude=-1.0,
            structural_coherence=0.5,
            pattern_matrix=[[0.5]]
        )
        assert result["validation_result"] == "NOT_COMPUTABLE"
        assert "error" in result
        
        # Coherence out of range
        result = apply_wsss(
            signal_amplitude=1.0,
            structural_coherence=1.5,
            pattern_matrix=[[0.5]]
        )
        assert result["validation_result"] == "NOT_COMPUTABLE"
        
        # Empty pattern matrix
        result = apply_wsss(
            signal_amplitude=1.0,
            structural_coherence=0.5,
            pattern_matrix=[]
        )
        assert result["validation_result"] == "NOT_COMPUTABLE"
    
    def test_no_strict_execution_error(self):
        """Test that strict_execution no longer raises NotImplementedError."""
        # After implementation, strict_execution should not raise
        result = apply_wsss(
            signal_amplitude=1.0,
            structural_coherence=0.5,
            pattern_matrix=[[0.5]],
            strict_execution=True  # Should NOT raise
        )
        
        assert result is not None
        assert "structure_score" in result
```

---

### Golden Tests

Golden tests verify output stability over time:

```python
import json
from pathlib import Path

def test_wsss_golden_output():
    """Test WSSS output matches golden reference."""
    inputs = {
        "signal_amplitude": 2.0,
        "structural_coherence": 0.75,
        "pattern_matrix": [[0.8, 0.7], [0.7, 0.8]]
    }
    
    result = apply_wsss(**inputs)
    
    # Load golden reference
    golden_path = Path("tests/golden/wsss_golden.json")
    if not golden_path.exists():
        # First run: save golden output
        golden_path.parent.mkdir(parents=True, exist_ok=True)
        with open(golden_path, "w") as f:
            json.dump(result, f, indent=2, sort_keys=True)
        pytest.skip("Golden file created - run test again to verify")
    
    with open(golden_path) as f:
        golden = json.load(f)
    
    # Verify all outputs match
    assert result["structure_score"] == golden["structure_score"]
    assert result["signal_quality"] == golden["signal_quality"]
    assert result["validation_result"] == golden["validation_result"]
    assert result["provenance_hash"] == golden["provenance_hash"]
```

---

### Provenance Hash Tests

```python
def test_wsss_provenance_hash_stability():
    """Test that provenance hashes are stable and deterministic."""
    inputs = {
        "signal_amplitude": 3.0,
        "structural_coherence": 0.65,
        "pattern_matrix": [[0.9, 0.8, 0.7], [0.8, 0.9, 0.8], [0.7, 0.8, 0.9]]
    }
    
    # Run 10 times
    hashes = [apply_wsss(**inputs)["provenance_hash"] for _ in range(10)]
    
    # All hashes should be identical
    assert len(set(hashes)) == 1, "Provenance hashes must be deterministic"
    
    # Hash should be valid SHA-256 (64 hex chars)
    assert len(hashes[0]) == 64
    assert all(c in "0123456789abcdef" for c in hashes[0])
```

---

## Provenance & Determinism

### Provenance Requirements

Every rune operator MUST include:

1. **Inputs hash** - SHA-256 of canonical JSON inputs
2. **Deterministic outputs** - No timestamps, no random values
3. **Stable ordering** - Arrays sorted by explicit keys
4. **Canonical JSON** - Use `hash_canonical_json()` from `abraxas.core.provenance`

### Computing Provenance Hashes

```python
from abraxas.core.provenance import hash_canonical_json

# Create canonical input dict (sorted keys, deterministic)
inputs_canonical = {
    "signal_amplitude": signal_amplitude,
    "structural_coherence": structural_coherence,
    "pattern_matrix": pattern_matrix,  # Lists are OK
}

# Compute SHA-256 hash
provenance_hash = hash_canonical_json(inputs_canonical)
# Returns: "abc123def456..." (64 hex chars)
```

### Determinism Checklist

- [ ] No `datetime.now()` calls
- [ ] No `random.random()` without fixed seed
- [ ] No dict iteration without sorted keys
- [ ] All floats rounded to consistent precision (e.g., 6 decimal places)
- [ ] Arrays sorted by explicit keys (not insertion order)
- [ ] Provenance hash computed from canonical JSON
- [ ] Same inputs produce same outputs (verified in tests)

---

## Example: WSSS Implementation

See [Step 3: Implement with Provenance](#step-3-implement-with-provenance) above for complete WSSS implementation.

**Key Decisions:**
1. **Structure dominates amplitude** - Validation passes when structure_score > normalized_amplitude
2. **Log scaling for amplitude** - Prevents large amplitudes from dominating
3. **Pattern matrix averaging** - Simple, deterministic structure computation
4. **Graceful error handling** - Returns NOT_COMPUTABLE instead of raising exceptions

---

## Capability Contract Integration

### Step 1: Register in Registry

Add entry to `abraxas/runes/registry.json`:

```json
{
  "capabilities": [
    {
      "id": "rune.wsss.apply",
      "name": "WSSS Rune Operator",
      "version": "1.0.0",
      "module": "abraxas.runes.operators.wsss",
      "function": "apply_wsss",
      "inputs_schema": "schemas/capabilities/rune_wsss_inputs.schema.json",
      "outputs_schema": "schemas/capabilities/rune_wsss_outputs.schema.json"
    }
  ]
}
```

---

### Step 2: Create Input/Output Schemas

**schemas/capabilities/rune_wsss_inputs.schema.json:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["signal_amplitude", "structural_coherence", "pattern_matrix"],
  "properties": {
    "signal_amplitude": {"type": "number", "minimum": 0},
    "structural_coherence": {"type": "number", "minimum": 0, "maximum": 1},
    "pattern_matrix": {
      "type": "array",
      "items": {
        "type": "array",
        "items": {"type": "number"}
      }
    },
    "strict_execution": {"type": "boolean", "default": false}
  }
}
```

---

### Step 3: Invoke via Capability Contract

```python
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext

# Create invocation context
ctx = RuneInvocationContext(
    run_id="RUN-001",
    caller="abx.mymodule",
    environment="production"
)

# Invoke WSSS via capability
result = invoke_capability(
    capability="rune.wsss.apply",
    inputs={
        "signal_amplitude": 2.0,
        "structural_coherence": 0.75,
        "pattern_matrix": [[0.8, 0.7], [0.7, 0.8]]
    },
    ctx=ctx,
    strict_execution=True
)

# Extract outputs
structure_score = result["structure_score"]
validation_result = result["validation_result"]
provenance_hash = result["provenance_hash"]
```

---

## Common Patterns

### Pattern 1: Bounded Outputs

Always clamp outputs to known ranges:

```python
structure_score = max(0.0, min(1.0, raw_score))  # Clamp to [0, 1]
```

---

### Pattern 2: Weighted Combinations

Use explicit weights for interpretability:

```python
weights = {"openness": 0.3, "receptivity": 0.3, "coherence": 0.2}
score = sum(state.get(k, 0.5) * w for k, w in weights.items())
```

---

### Pattern 3: NOT_COMPUTABLE Status

Return structured error info instead of raising exceptions:

```python
if missing_required_input:
    return {
        "validation_result": "NOT_COMPUTABLE",
        "error": "Missing required input: receiver_state",
        "provenance_hash": None,
    }
```

---

### Pattern 4: Default Values

Provide sensible defaults for optional inputs:

```python
default_threshold = kwargs.get("threshold", 0.25)
default_mode = kwargs.get("mode", "standard")
```

---

## Troubleshooting

### Problem: Tests fail with "NotImplementedError"

**Cause:** Stub not replaced with implementation

**Solution:** 
1. Remove `if strict_execution: raise NotImplementedError(...)`
2. Add real implementation logic
3. Return dict with all expected output keys

---

### Problem: Provenance hashes change between runs

**Cause:** Non-deterministic inputs (timestamps, randomness, dict ordering)

**Solution:**
1. Check for `datetime.now()` calls → use fixed timestamp from inputs
2. Check for `random.random()` → use deterministic seed or remove
3. Check for dict iteration → use `sorted(dict.items())`
4. Use `hash_canonical_json()` for all provenance hashes

---

### Problem: Golden tests fail after code change

**Expected:** Golden tests should fail when implementation changes

**Solution:**
1. Review the output diff carefully
2. If change is intentional:
   - Delete old golden file: `rm tests/golden/wsss_golden.json`
   - Re-run test to generate new golden
   - Commit new golden file
3. If change is unintentional:
   - Fix implementation to match original behavior

---

### Problem: Capability not found

**Cause:** Capability not registered in `abraxas/runes/registry.json`

**Solution:**
1. Add capability entry to registry.json
2. Create input/output schemas in `schemas/capabilities/`
3. Reload registry: Restart Python process or reload module

---

## Checklist: Implementation Complete

Before marking an operator as complete:

- [ ] Stub logic removed (`NotImplementedError` guard deleted)
- [ ] Real implementation logic added
- [ ] All outputs computed (no `None` values)
- [ ] Provenance hash included in outputs
- [ ] Input validation with graceful errors
- [ ] Constraints from docstring enforced
- [ ] Deterministic (same inputs → same outputs)
- [ ] Unit tests added (basic functionality)
- [ ] Determinism tests added (run twice, compare hashes)
- [ ] Golden tests added (output stability)
- [ ] Edge case tests added (invalid inputs, boundary conditions)
- [ ] Capability registered in `abraxas/runes/registry.json`
- [ ] Input/output schemas created
- [ ] Documentation updated (if needed)
- [ ] No direct imports in `abx/` (capability contracts only)

---

## See Also

- **ABX-Runes Coupling Guide:** `docs/migration/abx_runes_coupling.md`
- **Rune Operators Directory:** `abraxas/runes/operators/`
- **Capability Registry:** `abraxas/runes/registry.json`
- **Provenance Utilities:** `abraxas/core/provenance.py`
- **Example Implementation:** `abraxas/runes/operators/sds.py` (complete)
- **Example Stub:** `abraxas/runes/operators/wsss.py` (to be implemented)

---

**End of Rune Operator Development Guide**
