# Shadow Structural Metrics (SSM) Specification

**Version**: 1.0.0
**Status**: Canonical - LOCKED
**Compatibility**: Abraxas v1.4+
**Last Updated**: 2025-12-29

---

## Overview

Shadow Structural Metrics (SSM) are **observe-only, deterministic metrics** derived from Cambridge Analytica research that track psychological manipulation vectors without influencing other system metrics. They operate in "shadow mode" — passively observing and recording, but never affecting decision-making or other metric calculations.

SSM provides provenance-tracked, SEED-compliant measurement of six core manipulation dimensions:

1. **SEI** - Sentiment Entropy Index
2. **CLIP** - Cognitive Load Intensity Proxy
3. **NOR** - Narrative Overload Rating
4. **PTS** - Persuasive Trajectory Score
5. **SCG** - Social Contagion Gradient
6. **FVC** - Filter Velocity Coefficient

---

## Design Principles

### 1. No-Influence Guarantee

**CRITICAL**: Shadow Structural Metrics MUST NEVER influence any other system metrics, decisions, or outputs.

- **Read-Only**: SSM values are never used as inputs to other calculations
- **Observation-Only**: SSM tracks patterns without affecting them
- **Isolation**: SSM calculations run in isolated context with no side effects
- **Audit Trail**: All SSM computations logged for verification of non-influence
- **Diagnostics Never Alter Prediction**: Shadow metrics are diagnostic/analytical only and do not affect forecast/prediction pipelines

**Dual-Lane Architecture**:

Abraxas enforces strict separation between:
- **Prediction Lane** (truth-pure, morally agnostic forecasting) - never influenced by shadow signals
- **Shadow Lane** (observe-only diagnostics) - never affects prediction unless explicitly PROMOTED via governance

See `docs/specs/dual_lane_architecture.md` for full specification.

**Enforcement**:
```python
# SSM values are computed but never returned to calling context
# Only accessible via ABX-Runes interface with explicit isolation

# Lane Guard enforces prediction/shadow separation
from abraxas.detectors.shadow.lane_guard import require_promoted

# Before using shadow metric in prediction:
promotion = require_promoted("shadow_metric_name")  # Raises LaneViolationError if not promoted
```

### 2. SEED Provenance

All SSM computations are fully deterministic with SHA-256 provenance tracking:

- Same inputs always produce same outputs (no randomness)
- Every SSM calculation includes provenance hash
- Git SHA, timestamp (UTC), input hash tracked
- Provenance chain enables perfect reproducibility

**Provenance Structure**:
```python
{
  "metric": "SEI",
  "value": 0.653,
  "provenance": {
    "run_id": "RUN-abc123",
    "started_at_utc": "2025-12-29T10:30:00Z",
    "inputs_hash": "sha256:...",
    "config_hash": "sha256:...",
    "git_sha": "26f3fe9",
    "host": "edge-device-01",
    "seed_compliant": true
  }
}
```

### 3. ABX-Runes-Only Coupling

SSM values are ONLY accessible through the ABX-Runes interface:

- **No direct API access**: Cannot query SSM via REST API
- **No direct function calls**: Cannot import and call SSM functions
- **Rune-mediated access**: All access goes through designated rune operators
- **Permission-gated**: Runes enforce access control and audit logging

**Access Pattern**:
```python
# ALLOWED: Via ABX-Runes
from abraxas.runes import invoke_rune
result = invoke_rune("ϟ₇", context={"symbol_pool": symbols})

# FORBIDDEN: Direct access
from abraxas.shadow_metrics import compute_sei  # WILL FAIL
```

### 4. Incremental Patch Only

SSM implementations can ONLY be modified through incremental patches:

- **No wholesale replacement**: Cannot replace entire metric implementation
- **Patch-based updates**: Changes applied as versioned patches
- **Backward compatibility**: All patches must maintain compatibility
- **Audit trail**: Every patch logged with provenance

**Patch Structure**:
```python
{
  "patch_id": "SSM-PATCH-001",
  "metric": "SEI",
  "version": "1.0.1",
  "base_version": "1.0.0",
  "changes": "Improved normalization for edge case handling",
  "applied_at_utc": "2025-12-29T11:00:00Z",
  "git_sha": "def456",
  "backward_compatible": true
}
```

---

## Metric Definitions

### SEI - Sentiment Entropy Index

**Purpose**: Measures emotional volatility and sentiment manipulation potential

**Domain**: [0.0, 1.0]

**Calculation**:
```
SEI = H(p_positive, p_negative, p_neutral) / log(3)

where:
  H = Shannon entropy
  p_i = proportion of sentiment class i
  Normalization by log(3) bounds to [0,1]
```

**Interpretation**:
- **SEI ≈ 0.0**: Homogeneous sentiment (all positive, negative, or neutral)
- **SEI ≈ 0.5**: Mixed sentiment with some patterns
- **SEI ≈ 1.0**: Maximum entropy (perfectly balanced tri-modal distribution)

**Provenance Fields**:
- `sentiment_distribution`: {positive, negative, neutral} counts
- `total_samples`: Total number of sentiment-analyzed items
- `normalization_method`: "shannon_entropy_trimodal"

---

### CLIP - Cognitive Load Intensity Proxy

**Purpose**: Estimates cognitive processing burden on audience

**Domain**: [0.0, 1.0]

**Calculation**:
```
CLIP = w1*complexity + w2*density + w3*novelty

where:
  complexity = normalized Flesch-Kincaid grade level
  density = normalized information density (bits per token)
  novelty = proportion of low-frequency tokens
  w1, w2, w3 = calibrated weights (default: 0.4, 0.3, 0.3)
```

**Interpretation**:
- **CLIP < 0.3**: Low cognitive load (simple, sparse, familiar)
- **CLIP 0.3-0.7**: Moderate cognitive load
- **CLIP > 0.7**: High cognitive load (complex, dense, novel)

**Provenance Fields**:
- `complexity_score`: Raw complexity metric
- `density_score`: Raw information density
- `novelty_score`: Raw novelty metric
- `weights`: {w1, w2, w3}

---

### NOR - Narrative Overload Rating

**Purpose**: Detects narrative saturation and competing storylines

**Domain**: [0.0, 1.0]

**Calculation**:
```
NOR = 1 - exp(-λ * narrative_count)

where:
  narrative_count = number of distinct narrative threads detected
  λ = decay constant (default: 0.3)
  Saturation function bounds to [0,1)
```

**Interpretation**:
- **NOR < 0.3**: Singular narrative dominance
- **NOR 0.3-0.6**: Multiple competing narratives
- **NOR > 0.6**: Narrative saturation (fragmentation)

**Provenance Fields**:
- `narrative_count`: Number of distinct narratives
- `decay_constant`: λ parameter
- `narrative_ids`: List of detected narrative identifiers

---

### PTS - Persuasive Trajectory Score

**Purpose**: Tracks persuasion intensity over time

**Domain**: [0.0, 1.0]

**Calculation**:
```
PTS = sigmoid(slope * Δopinion)

where:
  Δopinion = change in aggregate opinion metric over window
  slope = calibrated steepness (default: 5.0)
  sigmoid = 1 / (1 + exp(-x))
```

**Interpretation**:
- **PTS < 0.4**: Weak or negative persuasion
- **PTS 0.4-0.6**: Neutral/stable opinion
- **PTS > 0.6**: Strong positive persuasion

**Provenance Fields**:
- `delta_opinion`: Raw opinion change value
- `time_window_hours`: Time window for trajectory calculation
- `slope_parameter`: Sigmoid slope value

---

### SCG - Social Contagion Gradient

**Purpose**: Measures rate of social transmission and viral potential

**Domain**: [0.0, 1.0]

**Calculation**:
```
SCG = (R_effective - 1) / (R_max - 1)

where:
  R_effective = estimated effective reproduction number
  R_max = maximum observed R in dataset (default: 10.0)
  Normalization bounds to [0,1]
```

**Interpretation**:
- **SCG < 0.3**: Sub-critical spread (dying out)
- **SCG 0.3-0.5**: Critical threshold (R ≈ 1)
- **SCG > 0.5**: Super-critical spread (viral growth)

**Provenance Fields**:
- `r_effective`: Estimated R value
- `r_max`: Maximum R for normalization
- `observation_window_hours`: Time window for R estimation

---

### FVC - Filter Velocity Coefficient

**Purpose**: Tracks speed of information filtering and echo chamber formation

**Domain**: [0.0, 1.0]

**Calculation**:
```
FVC = 1 - diversity_index

where:
  diversity_index = Simpson's diversity index over information sources
  D = 1 - Σ(p_i^2) where p_i = proportion from source i
```

**Interpretation**:
- **FVC < 0.3**: High source diversity (low filtering)
- **FVC 0.3-0.6**: Moderate filtering
- **FVC > 0.6**: High filtering (echo chamber formation)

**Provenance Fields**:
- `diversity_index`: Simpson's D value
- `source_count`: Number of distinct sources
- `source_distribution`: Proportions per source

---

## ABX-Runes Integration

### Rune ϟ₇ - Shadow Structural Observer (SSO)

**Purpose**: Provides isolated, read-only access to Shadow Structural Metrics

**Layer**: Governance

**Inputs**:
- `symbol_pool`: List of symbolic events to analyze
- `time_window_hours`: Time window for temporal metrics (default: 24)
- `metrics_requested`: List of metric IDs (default: all six)

**Outputs**:
- `ssm_bundle`: Shadow Structural Metrics bundle with provenance
- `isolation_proof`: Cryptographic proof of non-influence guarantee

**Constraints**:
- Read-only access (cannot modify system state)
- Isolated execution context
- Audit logging mandatory
- Provenance chain included

**Example Usage**:
```python
from abraxas.runes import invoke_rune

result = invoke_rune(
    "ϟ₇",
    context={
        "symbol_pool": symbol_events,
        "time_window_hours": 48,
        "metrics_requested": ["SEI", "CLIP", "PTS"]
    }
)

# result.ssm_bundle contains:
# {
#   "SEI": {"value": 0.65, "provenance": {...}},
#   "CLIP": {"value": 0.42, "provenance": {...}},
#   "PTS": {"value": 0.73, "provenance": {...}}
# }
# result.isolation_proof contains cryptographic isolation attestation
```

---

## Implementation Requirements

### Directory Structure

```
abraxas/
└── shadow_metrics/
    ├── __init__.py              # Module initialization (access control)
    ├── core.py                  # Core SSM computation engine
    ├── sei.py                   # SEI implementation
    ├── clip.py                  # CLIP implementation
    ├── nor.py                   # NOR implementation
    ├── pts.py                   # PTS implementation
    ├── scg.py                   # SCG implementation
    ├── fvc.py                   # FVC implementation
    ├── isolation.py             # Isolation enforcement
    ├── provenance.py            # SSM-specific provenance tracking
    ├── patch_registry.py        # Patch management system
    └── tests/
        ├── test_sei.py
        ├── test_clip.py
        ├── test_nor.py
        ├── test_pts.py
        ├── test_scg.py
        └── test_fvc.py
```

### Access Control

```python
# abraxas/shadow_metrics/__init__.py

# FORBIDDEN: Direct imports will raise AccessDeniedError
# All access MUST go through ABX-Runes interface

class AccessDeniedError(Exception):
    """Raised when attempting direct access to Shadow Structural Metrics."""
    pass

def __getattr__(name):
    """Block all direct attribute access."""
    if name.startswith("compute_") or name.startswith("_"):
        raise AccessDeniedError(
            "Shadow Structural Metrics can only be accessed via ABX-Runes interface (ϟ₇). "
            "Direct access is forbidden by design. "
            "See docs/specs/shadow_structural_metrics.md for details."
        )
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

### Provenance Tracking

All SSM computations include mandatory provenance:

```python
from abraxas.core.provenance import Provenance, hash_canonical_json

def _compute_with_provenance(metric_id, inputs, config):
    """Compute SSM metric with full provenance tracking."""
    provenance = Provenance(
        run_id=f"SSM-{metric_id}-{uuid.uuid4().hex[:8]}",
        started_at_utc=Provenance.now_iso_z(),
        inputs_hash=hash_canonical_json(inputs),
        config_hash=hash_canonical_json(config),
        git_sha=get_git_sha(),
        host=socket.gethostname()
    )

    value = _compute_metric(metric_id, inputs, config)

    return {
        "metric": metric_id,
        "value": value,
        "provenance": provenance.__dict__,
        "seed_compliant": True,
        "no_influence_guarantee": True
    }
```

### Patch Management

```python
# abraxas/shadow_metrics/patch_registry.py

PATCH_LEDGER = [
    {
        "patch_id": "SSM-BASELINE-1.0.0",
        "version": "1.0.0",
        "metrics": ["SEI", "CLIP", "NOR", "PTS", "SCG", "FVC"],
        "description": "Initial canonical implementation",
        "applied_at_utc": "2025-12-29T10:00:00Z",
        "git_sha": "baseline",
        "backward_compatible": True
    }
]

def apply_patch(patch_spec):
    """Apply incremental patch to SSM implementation."""
    # Validate backward compatibility
    # Apply changes incrementally
    # Log to patch ledger
    # Update version
    pass
```

---

## Deterministic Guarantees

1. **No Randomness**: All calculations use deterministic algorithms only
2. **No External APIs**: Pure local computation (no network calls)
3. **No ML Models**: Rule-based calculations only (no neural networks)
4. **Stable Outputs**: Same inputs always produce same outputs
5. **Provenance Chain**: Full audit trail from inputs to outputs

---

## Testing Requirements

### Determinism Tests

```python
def test_sei_determinism():
    """Verify SEI produces identical results for same inputs."""
    inputs = {"positive": 10, "negative": 5, "neutral": 15}
    result1 = compute_sei_via_rune(inputs)
    result2 = compute_sei_via_rune(inputs)
    assert result1["value"] == result2["value"]
    assert result1["provenance"]["inputs_hash"] == result2["provenance"]["inputs_hash"]
```

### Isolation Tests

```python
def test_direct_access_forbidden():
    """Verify direct access to SSM is blocked."""
    with pytest.raises(AccessDeniedError):
        from abraxas.shadow_metrics import compute_sei
```

### Provenance Tests

```python
def test_provenance_completeness():
    """Verify all provenance fields are present."""
    result = compute_clip_via_rune(inputs)
    assert "run_id" in result["provenance"]
    assert "started_at_utc" in result["provenance"]
    assert "inputs_hash" in result["provenance"]
    assert "config_hash" in result["provenance"]
    assert result["seed_compliant"] is True
```

---

## Migration & Rollout

### Phase 1: Implementation (Current)

- Create Shadow Structural Metrics module
- Implement six core metrics (SEI, CLIP, NOR, PTS, SCG, FVC)
- Add access control and isolation enforcement
- Write comprehensive tests

### Phase 2: ABX-Runes Integration

- Create Rune ϟ₇ (Shadow Structural Observer)
- Implement rune operator with isolation guarantees
- Add audit logging and provenance tracking
- Register rune in ABX-Runes registry

### Phase 3: Validation

- Run determinism tests on production data
- Verify no-influence guarantee holds
- Validate provenance chain integrity
- Confirm SEED compliance

### Phase 4: Lock & Deploy

- Lock implementation as canonical baseline
- Deploy to production edge devices
- Enable monitoring and audit logging
- Document access patterns

---

## References

- **Cambridge Analytica Research**: Proprietary psychological targeting metrics
- **SEED Framework**: Abraxas deterministic execution framework
- **ABX-Runes**: Abraxas runic symbolic operator system
- **Provenance System**: `abraxas/core/provenance.py`
- **Implementation**: `abraxas/shadow_metrics/`
- **Tests**: `tests/test_shadow_metrics_*.py`

---

## Compliance

This specification is **LOCKED** and **CANONICAL** as of 2025-12-29.

All changes MUST:
1. Go through incremental patch process
2. Maintain backward compatibility
3. Preserve no-influence guarantee
4. Include full provenance
5. Pass all determinism tests

**Violation of these constraints will result in automatic rollback.**

---

**End of Shadow Structural Metrics Specification v1.0.0**
