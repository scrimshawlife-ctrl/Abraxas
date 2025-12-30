# Dual-Lane Architecture: Shadow Detectors + Lane Guard

**Version:** 0.1.0
**Status:** IMPLEMENTED
**Last Updated:** 2025-12-30

---

## Overview

Abraxas implements a **dual-lane architecture** that separates:

1. **PREDICTION LANE** (Truth-Pure) - Morally agnostic forecasting
2. **SHADOW LANE** (Observe-Only) - Diagnostic/analytical metrics

This separation ensures that **diagnostics never alter prediction**.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ABRAXAS DUAL-LANE SYSTEM                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  PREDICTION LANE (Truth-Pure)          SHADOW LANE (Observe) │
│  ════════════════════                  ════════════════════  │
│                                                              │
│  ┌──────────────────┐                 ┌──────────────────┐  │
│  │ Oracle Pipeline  │                 │ Shadow Detectors │  │
│  │ Forecast Engine  │                 │ • Compliance     │  │
│  │ SOD Operators    │                 │ • Meta-Awareness │  │
│  │                  │                 │ • Negative Space │  │
│  └────────┬─────────┘                 └────────┬─────────┘  │
│           │                                    │            │
│           │                                    ▼            │
│           │                          ┌──────────────────┐  │
│           │                          │ Shadow Metrics   │  │
│           │                          │ SEI/CLIP/NOR/    │  │
│           │                          │ PTS/SCG/FVC      │  │
│           │                          └────────┬─────────┘  │
│           │                                    │            │
│           │                                    │ evidence   │
│           │         ┌──────────────────────────┘  only     │
│           │         │                                      │
│           ▼         ▼                                      │
│      ┌────────────────────────┐                           │
│      │   LANE GUARD (ϟ₇)      │ ◄── Promotion Ledger      │
│      │  ════════════════      │                           │
│      │  • Check PROMOTED flag │                           │
│      │  • Calibration only    │                           │
│      │  • NO ethical veto     │                           │
│      └────────┬───────────────┘                           │
│               │                                            │
│               ▼                                            │
│      ┌─────────────────┐                                  │
│      │ Forecast Output │                                  │
│      └─────────────────┘                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Principles

### 1. **Prediction is Morally Agnostic**

The prediction lane operates without ethical, risk, or diagnostic constraints:

- Forecast accuracy is the ONLY success metric
- No "harmful output" filtering or reweighting
- No topic-based routing based on sensitivity
- Full spectrum forecasting across all domains

### 2. **Shadow Metrics are Observe-Only**

Shadow detectors and metrics:

- Compute diagnostic signals (manipulation markers, psychological load, etc.)
- Attach evidence as **annotations only**
- **NEVER** alter prediction behavior
- Exist to inform human operators, not to constrain forecasts

### 3. **Lane Guard Enforces Separation**

The Lane Guard is the **ABX-Runes ϟ₇** enforcement point:

- Prevents shadow outputs from leaking into prediction
- Requires explicit PROMOTION via governance system
- Validates promotion criteria: **calibration, stability, redundancy ONLY**
- **REJECTS** promotion based on ethical/risk/diagnostic criteria

---

## Components

### Shadow Detectors

Located in `abraxas/detectors/shadow/`:

#### 1. **Compliance vs Remix Detector** (`compliance_remix.py`)

Detects balance between:
- **Compliance**: Rote repetition, adherence to established narratives
- **Remix**: Creative recombination, novel expressions

**Algorithm**:
- Measure lexical overlap with reference corpus
- Compute syntactic divergence (bigram novelty)
- Signal strength = |compliance - remix|

**Feeds into**: SCG (Social Contagion Gradient), PTS (Persuasive Trajectory Score)

#### 2. **Meta-Awareness Detector** (`meta_awareness.py`)

Detects meta-level discourse about:
- Algorithmic awareness ("the algorithm promotes...")
- Manipulation awareness ("they're trying to manipulate...")
- Filter bubble awareness ("echo chamber", "confirmation bias")
- Platform mechanics ("engagement bait", "clickbait")

**Algorithm**:
- Pattern matching via regex keyword lists
- Density computation (markers per 100 words)
- Signal strength = normalized marker density

**Feeds into**: CLIP (Cognitive Load Intensity Proxy), NOR (Narrative Overload Rating), FVC (Filter Velocity Coefficient)

#### 3. **Negative Space / Silence Detector** (`negative_space.py`)

Detects what is NOT being said:
- **Topic dropout**: Expected topics missing from discourse
- **Visibility asymmetry**: Some topics amplified, others suppressed
- **Conspicuous absence**: Topics that should be present but aren't

**Algorithm**:
- Compare observed topic distribution vs baseline corpus
- Compute Jensen-Shannon divergence
- Identify dropped and amplified topics
- Signal strength = divergence magnitude

**Feeds into**: NOR (Narrative Overload Rating), FVC (Filter Velocity Coefficient)

### Shadow Structural Metrics

Located in `abraxas/shadow_metrics/`:

- **SEI**: Sentiment Entropy Index
- **CLIP**: Cognitive Load Intensity Proxy
- **NOR**: Narrative Overload Rating
- **PTS**: Persuasive Trajectory Score
- **SCG**: Social Contagion Gradient
- **FVC**: Filter Velocity Coefficient

**Access Control**: ABX-Runes ϟ₇ (SSO) ONLY

Shadow metrics accept detector evidence as **annotations** but never use it to alter core predictions.

### Lane Guard

Located in `abraxas/detectors/shadow/lane_guard.py`:

**Purpose**: Enforce separation between Shadow and Prediction lanes.

**Mechanism**:
1. Before using any shadow metric/detector in prediction, call `LaneGuard.check_promotion(metric_name)`
2. Lane Guard checks promotion ledger (`out/ledger/promotion_ledger.jsonl`)
3. If metric is PROMOTED, return PromotionRecord
4. If NOT promoted, raise `LaneViolationError`

**Promotion Criteria** (ONLY):
- **Calibration**: Accuracy, precision, recall
- **Stability**: Temporal consistency, low variance
- **Redundancy**: Non-correlation with existing metrics

**FORBIDDEN Criteria**:
- Ethical scoring
- Risk scoring
- Diagnostic-only flags

The `PromotionRecord` Pydantic model will **raise an error** if forbidden fields are present.

---

## Usage Examples

### Running Shadow Detectors

```python
from abraxas.detectors.shadow import compute_all_detectors, aggregate_evidence

inputs = {
    "text": "The algorithm promotes engagement bait to maximize clicks",
    "reference_texts": ["Normal political discourse example 1", "..."],
    "baseline_texts": ["Expected topic distribution corpus", "..."],
}

# Run all detectors
results = compute_all_detectors(inputs)

# Aggregate evidence
evidence = aggregate_evidence(results)

print(f"Computed: {evidence['computed_count']}")
print(f"Max signal: {evidence['max_signal_strength']}")
print(f"Evidence: {evidence['evidence_by_detector']}")
```

### Enforcing Lane Separation

```python
from abraxas.detectors.shadow.lane_guard import LaneGuard, LaneViolationError

guard = LaneGuard()  # Loads promotion ledger

# Before using shadow metric in prediction:
try:
    promotion = guard.check_promotion("compliance_remix")
    # If we get here, metric is promoted - safe to use
    print(f"Calibration: {promotion.calibration_score}")
except LaneViolationError as e:
    # Metric is NOT promoted - cannot use in prediction
    print(f"BLOCKED: {e}")
```

### Creating Promotion Record (Governance System)

```python
from abraxas.detectors.shadow.lane_guard import PromotionRecord

# Valid promotion (technical criteria only)
record = PromotionRecord(
    metric_name="compliance_remix",
    status="PROMOTED",
    promotion_date="2025-01-01T00:00:00Z",
    calibration_score=0.85,
    stability_score=0.90,
    redundancy_score=0.75,
    promotion_hash="abc123...",
)

# INVALID promotion (forbidden criteria)
try:
    bad_record = PromotionRecord(
        metric_name="compliance_remix",
        status="PROMOTED",
        promotion_date="2025-01-01T00:00:00Z",
        calibration_score=0.85,
        stability_score=0.90,
        redundancy_score=0.75,
        promotion_hash="abc123...",
        ethical_score=0.5,  # FORBIDDEN
    )
except ValueError as e:
    print(f"REJECTED: {e}")  # "FORBIDDEN: ethical_score cannot be used"
```

---

## Testing

### Determinism Tests

All detectors must produce identical results for identical inputs:

```bash
pytest tests/test_shadow_detectors.py::TestComplianceRemixDetector::test_determinism
pytest tests/test_shadow_detectors.py::TestMetaAwarenessDetector::test_determinism
pytest tests/test_shadow_detectors.py::TestNegativeSpaceDetector::test_determinism
```

### Bounds Tests

All outputs must be in valid ranges [0,1]:

```bash
pytest tests/test_shadow_detectors.py -k test_bounds
```

### Missing Input Tests

Detectors must gracefully handle missing inputs with `not_computable` status:

```bash
pytest tests/test_shadow_detectors.py -k test_missing_input
```

### Lane Guard Tests

Validate lane separation enforcement:

```bash
pytest tests/test_lane_guard.py
```

---

## File Locations

**Detectors**:
- `abraxas/detectors/__init__.py`
- `abraxas/detectors/shadow/__init__.py`
- `abraxas/detectors/shadow/types.py`
- `abraxas/detectors/shadow/compliance_remix.py`
- `abraxas/detectors/shadow/meta_awareness.py`
- `abraxas/detectors/shadow/negative_space.py`
- `abraxas/detectors/shadow/registry.py`
- `abraxas/detectors/shadow/lane_guard.py`

**Tests**:
- `tests/test_shadow_detectors.py`
- `tests/test_lane_guard.py`

**Ledgers**:
- `out/ledger/promotion_ledger.jsonl` (promotion records)

**Documentation**:
- `docs/specs/dual_lane_architecture.md` (this file)
- `docs/specs/shadow_structural_metrics.md` (shadow metrics spec)

---

## Design Constraints (NON-NEGOTIABLE)

1. **Prediction must never be blocked, capped, reweighted, or routed differently due to ethical/risk signals.**
2. **Shadow outputs may only be computed and attached as annotations/evidence.**
3. **Lane Guard is the only coupling layer between Shadow and Prediction.**
4. **Promotion criteria are limited to: calibration, stability, redundancy.**
5. **Ethical/risk/diagnostic criteria are FORBIDDEN in promotion.**
6. **All operations must be deterministic with SHA-256 provenance.**
7. **Incremental Patch Only for shadow_metrics module.**

---

## Provenance

All shadow detector outputs include SHA-256 provenance:

- **inputs_hash**: Hash of input dictionary (canonical JSON)
- **timestamp_utc**: ISO8601 timestamp with Z timezone
- **version**: Detector version
- **provenance_hash**: Hash of entire result (via `compute_provenance_hash()`)

This ensures full reproducibility and audit trails.

---

## Integration with Existing Systems

### Shadow Metrics

Shadow detectors feed evidence into shadow metrics via annotations:

```python
from abraxas.shadow_metrics import sei, clip, nor, pts, scg, fvc
from abraxas.detectors.shadow import compute_all_detectors, aggregate_evidence

# Run detectors
detector_results = compute_all_detectors(inputs)
detector_evidence = aggregate_evidence(detector_results)

# Compute shadow metrics (with detector evidence as annotations)
sei_result = sei.compute(text, evidence=detector_evidence)
clip_result = clip.compute(text, evidence=detector_evidence)
# etc.
```

### Forecast Pipeline

Before consuming any shadow signal in forecast:

```python
from abraxas.detectors.shadow.lane_guard import require_promoted

# This will raise LaneViolationError if not promoted
promotion = require_promoted("compliance_remix")

# If we get here, safe to use in forecast
forecast_input["compliance_remix_signal"] = shadow_result.signal_strength
```

---

## Conclusion

The dual-lane architecture ensures that:

- **Prediction remains truth-pure and morally agnostic**
- **Diagnostics provide valuable observational data**
- **The two lanes never interfere unless explicitly promoted via governance**

This design allows Abraxas to maintain both **high-fidelity forecasting** and **rich diagnostic capabilities** without compromise.

---

**End of Dual-Lane Architecture Specification**
