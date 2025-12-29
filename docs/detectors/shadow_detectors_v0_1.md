# Shadow Detectors v0.1 Documentation

**Version:** 0.1.0
**Status:** Emergent Candidate
**Governance:** ABX-Runes ϟ₇ (SSO) Only
**Last Updated:** 2025-12-29

---

## Overview

Shadow Detectors are three observe-only pattern detectors that feed Shadow Structural Metrics (SCG, FVC, NOR, PTS, CLIP, SEI) as evidence only. They **NEVER** influence system decisions, forecasts, or state transitions.

### The Three Detectors

1. **Compliance vs Remix Detector** (`compliance_remix`)
   - Detects balance between rote compliance/repetition and creative remix/mutation
   - Outputs: `remix_rate`, `rote_repetition_rate`, `template_phrase_density`, `anchor_stability`

2. **Meta-Awareness Detector** (`meta_awareness`)
   - Detects meta-level discourse about manipulation, algorithms, and epistemic fatigue
   - Outputs: `manipulation_discourse_score`, `algorithm_awareness_score`, `fatigue_joke_rate`, `predictive_mockery_rate`

3. **Negative Space / Silence Detector** (`negative_space`)
   - Detects topic dropout, visibility asymmetry, and abnormal silences
   - Outputs: `topic_dropout_score`, `visibility_asymmetry_score`, `mention_gap_halflife_score`

---

## Critical Invariants

### SHADOW-ONLY Guarantee

All detectors are **strictly observe-only**:

- ✅ **DO**: Feed shadow metrics as evidence
- ✅ **DO**: Include in metadata/provenance
- ❌ **NEVER**: Influence forecast weights
- ❌ **NEVER**: Affect state transitions
- ❌ **NEVER**: Modify system decisions

### Determinism & SEED Compliance

All detectors are **fully deterministic**:

- Same inputs → identical outputs
- Stable key ordering (sorted dicts/lists)
- SHA-256 provenance for all computations
- No timestamps in computation (only in provenance)

### Access Control

- **ABX-Runes ϟ₇ (SSO) ONLY**: Direct access forbidden
- Must be invoked via Shadow Structural Observer rune
- Isolation proof included in all outputs

---

## Input Requirements

### Compliance vs Remix Detector

**Required:**
- `drift_score` (float): Drift score from slang_drift analysis [0,1]
- `lifecycle_state` (str): Lifecycle state (Proto, Front, Saturated, Dormant, Archived)
- `tau_velocity` (float): Temporal velocity (τᵥ)

**Optional:**
- `appearances` (int): Number of term appearances
- `similarity_early_late` (float): Early/late similarity score [0,1]
- `new_to_window` (bool): Whether term is new to observation window
- `csp_ff` (float): Formulaic Flag from CSP [0,1]
- `csp_mio` (float): Manufactured Indicator Overlap [0,1]
- `fog_type_counts` (dict): Fog type counts from MWR
- `weather_types` (list): Weather classification (MW-01 through MW-05)
- `tau_half_life` (float): Temporal half-life (τₕ) in hours
- `observation_count` (int): Number of observations

### Meta-Awareness Detector

**Required:**
- `text` (str): Text content for keyword detection (non-empty)

**Optional:**
- `dmx_overall` (float): Overall manipulation risk [0,1]
- `dmx_bucket` (str): DMX bucket (LOW, MED, HIGH)
- `rdv_irony` (float): Irony axis from RDV [0,1]
- `rdv_humor` (float): Humor axis from RDV [0,1]
- `rdv_nihilism` (float): Nihilism axis from RDV [0,1]
- `fatigue_threshold` (float): EFTE fatigue threshold [0,1]
- `saturation_risk` (str): EFTE saturation risk (LOW, MED, HIGH)
- `rrs` (float): Repetition/Redundancy Score [0,1]
- `cis` (float): Coordination Indicator Score [0,1]
- `mri` (float): Manipulation Risk Index [0,100]
- `iri` (float): Integrity Risk Index [0,100]

### Negative Space / Silence Detector

**Required:**
- `current_narratives` (list): Current narrative/topic IDs (from symbol_pool)
- `baseline_narratives` (list): Baseline narrative IDs (from history)
- `sufficient_history` (bool): At least 3 history entries (configurable)

**Optional:**
- `current_sources` (list): Current source IDs
- `baseline_sources` (list): Baseline source IDs
- `source_distribution` (dict): Source distribution (from FVC)
- `current_timestamp` (str): Current observation timestamp

---

## Output Schema

All detectors return a `DetectorValue` with:

```python
{
    "id": DetectorId,               # Enum: COMPLIANCE_REMIX, META_AWARENESS, NEGATIVE_SPACE
    "status": DetectorStatus,       # Enum: OK, NOT_COMPUTABLE
    "value": Optional[float],       # Overall value [0.0, 1.0] (None if not_computable)
    "subscores": Dict[str, float],  # Subscores [0.0, 1.0] each (sorted keys)
    "missing_keys": List[str],      # Sorted list of missing required keys
    "evidence": Optional[Dict],     # Additional evidence metadata (sorted keys)
    "provenance": DetectorProvenance,  # Full provenance tracking
    "bounds": Tuple[float, float],  # Always (0.0, 1.0)
}
```

### Provenance Schema

```python
{
    "detector_id": str,             # Detector ID
    "used_keys": List[str],         # Sorted list of keys used in computation
    "missing_keys": List[str],      # Sorted list of missing required keys
    "history_len": int,             # Length of history (0 if not used)
    "envelope_version": Optional[str],  # Envelope version if present
    "inputs_hash": str,             # SHA-256 hash of inputs (canonical JSON)
    "config_hash": str,             # SHA-256 hash of config (canonical JSON)
    "computed_at_utc": str,         # ISO8601 timestamp with 'Z' timezone
    "seed_compliant": bool,         # Always True
    "no_influence_guarantee": bool, # Always True
}
```

---

## Usage

### Via Registry

```python
from abraxas.detectors.shadow.registry import compute_all_detectors, serialize_detector_results

context = {
    "text": "Example text",
    "drift": {"drift_score": 0.5},
    "lifecycle_state": "Front",
    "tau": {"tau_velocity": 0.5},
    "symbol_pool": [
        {"narrative_id": "topic_A", "source": "source1"},
    ],
}

history = [
    {"symbol_pool": [{"narrative_id": "topic_A"}, {"narrative_id": "topic_B"}]},
    {"symbol_pool": [{"narrative_id": "topic_A"}, {"narrative_id": "topic_C"}]},
    {"symbol_pool": [{"narrative_id": "topic_A"}]},
]

# Compute all detectors
results = compute_all_detectors(context, history)

# Serialize for deterministic output
serialized = serialize_detector_results(results)
```

### Individual Detectors

```python
from abraxas.detectors.shadow import compliance_remix, meta_awareness, negative_space

# Compliance vs Remix
cr_result = compliance_remix.compute_detector(context)

# Meta-Awareness
ma_result = meta_awareness.compute_detector(context)

# Negative Space (requires history)
ns_result = negative_space.compute_detector(context, history)
```

### Integration with Shadow Metrics

Shadow metrics automatically consume detector results if present in context:

```python
context = {
    "symbol_pool": [...],
    "shadow_detectors": {
        "compliance_remix": {...},  # DetectorValue serialized
        "meta_awareness": {...},
        "negative_space": {...},
    },
}

# Shadow metrics will include detector evidence in metadata
scg_value, scg_metadata = scg.compute(scg.extract_inputs(context), scg.get_default_config())

# scg_metadata["shadow_detector_evidence"] contains detector results
```

---

## not_computable Behavior

Detectors return `status=NOT_COMPUTABLE` when:

1. **Compliance vs Remix**: Missing `drift_score`, `lifecycle_state`, or `tau_velocity`
2. **Meta-Awareness**: Missing or empty `text`
3. **Negative Space**: Insufficient history (< 3 entries by default)

When `not_computable`:
- `value` is `None`
- `subscores` is empty dict `{}`
- `missing_keys` lists all missing required keys (sorted)
- `evidence` may contain error details

Shadow metrics that depend on detector outputs **must also return not_computable** if required detectors are not_computable.

---

## Determinism Guarantees

All outputs are **strictly deterministic**:

1. **Sorted Keys**: All dict keys sorted alphabetically
2. **Sorted Lists**: `missing_keys`, `used_keys`, lists in subscores/evidence
3. **Stable Hashing**: SHA-256 of canonical JSON (sorted keys, no whitespace)
4. **No Randomness**: No random operations, no unstable sorting
5. **No Timestamps in Computation**: Timestamps only in provenance metadata

### Verifying Determinism

```python
# Same inputs → identical outputs
result1 = detector.compute_detector(context, history)
result2 = detector.compute_detector(context, history)

assert result1.model_dump() == result2.model_dump()
```

---

## Bounds Enforcement

All values and subscores are **strictly clamped to [0.0, 1.0]**:

- Uses `clamp01(value)` utility function
- Applies to overall `value` and all `subscores`
- Extreme inputs (negative, > 1.0) are clamped
- Bounds field always `(0.0, 1.0)`

---

## Rent-Payment Gates (Stub)

**Status:** Skeleton only (dormant)

Future governance gates for detector evolution:

1. **Correlation Check**: Detect redundancy with existing metrics
2. **Stability Check**: Verify output stability over time
3. **Utility Check**: Measure incremental value vs cost

**Current Behavior:** Gates are not run; logs `"gate_not_run"` with provenance

---

## Testing

Three test suites validate detector correctness:

### 1. Determinism Tests (`tests/test_shadow_detectors_determinism.py`)

Verifies:
- Same inputs → identical outputs
- Serialization is deterministic
- Dict keys are sorted
- Lists are sorted

### 2. Missing Inputs Tests (`tests/test_shadow_detectors_missing_inputs.py`)

Verifies:
- `not_computable` when required inputs missing
- `OK` when all required inputs present
- `missing_keys` correctly populated and sorted

### 3. Bounds Tests (`tests/test_shadow_detectors_bounds.py`)

Verifies:
- All values in [0.0, 1.0]
- All subscores in [0.0, 1.0]
- Extreme inputs are clamped correctly
- Bounds field is `(0.0, 1.0)`

---

## Version History

### v0.1.0 (2025-12-29)

- Initial implementation of three shadow detectors
- Compliance vs Remix Detector
- Meta-Awareness Detector
- Negative Space / Silence Detector
- Integration with Shadow Structural Metrics
- Comprehensive test suite
- ABX-Runes ϟ₇ access control

---

## Governance & Evolution

### Current Status

- **Mode:** `shadow` (observe-only)
- **Influence:** `no_influence=True` (guaranteed)
- **Governance:** `emergent_candidate` (subject to evolution)

### Incremental Patch Only

All modifications **MUST** follow Incremental Patch Only policy:

- No full rewrites
- Minimal diffs only
- Patch ledger tracking (future)
- Backward compatible when possible

### Access Control

- **Direct Access:** FORBIDDEN
- **ABX-Runes ϟ₇ (SSO):** Required for invocation
- **Isolation Proof:** Included in all outputs
- **No Hidden Coupling:** No undocumented dependencies

---

## Known Limitations

1. **Keyword Detection**: Meta-awareness uses simple keyword matching (not semantic analysis)
2. **History Required**: Negative Space requires ≥3 history entries (configurable)
3. **Proxy Metrics**: Some subscores use proxies (e.g., template_phrase_density from fog types)
4. **No Real-Time Adaptation**: Detectors do not learn or adapt (fully deterministic)

---

## Future Enhancements (Roadmap)

1. **Semantic Analysis**: Replace keyword matching with embedding-based semantic similarity
2. **Adaptive Thresholds**: Allow configuration tuning based on domain
3. **Multi-Language Support**: Extend beyond English keyword lists
4. **Temporal Analysis**: Add time-series analysis for trend detection
5. **Rent-Payment Gates**: Activate governance gates with real correlation/stability checks

---

## References

- **Shadow Structural Metrics Spec:** `docs/specs/shadow_structural_metrics.md`
- **ABX-Runes Specification:** `docs/specs/abx_runes.md` (if exists)
- **SEED Compliance:** `docs/canon/ABRAXAS_CANON_LEDGER.txt`
- **Oracle Signal Layer:** `abraxas/oracle/v2/`

---

**END OF DOCUMENTATION**
