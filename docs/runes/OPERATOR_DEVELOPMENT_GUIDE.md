# Rune Operator Development Guide

This guide describes how to convert auto-generated rune stubs into deterministic, provenance-bearing implementations.

## Principles (ABX-Core / SEED)

- **Determinism**: identical inputs must yield identical outputs.
- **Provenance**: emit structured provenance data for every run.
- **Entropy reduction**: prefer bounded, explicit logic over probabilistic behavior.
- **No hidden coupling**: use capability contracts for cross-module dependencies.

## Anatomy of a Rune Operator

A typical operator lives under `abraxas/runes/operators/` and exposes a function like:

```python
from typing import Any, Dict

def apply_example(input_a: Any, input_b: Any, *, strict_execution: bool = False) -> Dict[str, Any]:
    ...
```

### Required Behaviors

1. **Accept `strict_execution`** but do not raise `NotImplementedError` once implemented.
2. **Validate inputs** with safe defaults for missing or malformed data.
3. **Return explicit outputs** matching the rune’s contract (keys and types).
4. **Avoid side effects** (no filesystem/network) unless explicitly required by the rune spec.

## Conversion Workflow

1. **Read the stub header**
   - Identify inputs, outputs, constraints, and canonical statement.
   - Example: `abraxas/runes/operators/wsss.py` declares `signal_amplitude`, `structural_coherence`, `pattern_matrix`.

2. **Define deterministic transformations**
   - Convert inputs into normalized scalars (`0.0 → 1.0`).
   - Use explicit scoring rules (weighted averages, clamps, hashes).

3. **Emit structured outputs**
   - Include both raw metrics and a classification label when appropriate.
   - Ensure all keys are populated (no `None`) unless the contract permits.

4. **Add golden tests**
   - Create deterministic fixtures in `tests/` or update existing golden files.
   - Use stable inputs and compare entire output dicts.

## Provenance Patterns

When a rune must surface provenance in outputs:

- Use canonical hashes for input serialization.
- Include:
  - `operation_id`
  - `inputs_hash`
  - `timestamp` (ISO8601)
  - optional `seed`

See `abraxas/core/provenance.py` for `canonical_envelope` and hashing helpers.

## Example: Converting a Stub

```python
from __future__ import annotations
from typing import Any, Dict
import hashlib


def apply_tam(traversal_path: Any, node_sequence: Any, context_history: Any, *, strict_execution: bool = False) -> Dict[str, Any]:
    _ = strict_execution
    nodes = [str(v) for v in (node_sequence or [])]
    path_signature = hashlib.sha256("|".join(nodes).encode("utf-8")).hexdigest()
    return {
        "emergent_meaning": nodes[-1] if nodes else "origin",
        "path_signature": path_signature,
        "semantic_trace": [{"step": i, "node": n} for i, n in enumerate(nodes)],
    }
```

## Checklist

- [ ] Stub removed (`NotImplementedError` no longer raised)
- [ ] Inputs normalized + deterministic
- [ ] Outputs match contract keys
- [ ] Golden test added or updated
- [ ] Provenance included when required

