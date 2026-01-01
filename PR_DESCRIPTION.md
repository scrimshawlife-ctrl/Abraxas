# Shadow Detectors v0.1: Compliance/Remix, Meta-Awareness, Negative Space

## Summary

Implements three **shadow-only pattern detectors** that feed Shadow Structural Metrics (SCG, FVC, NOR, PTS, CLIP, SEI) as evidence without influencing system decisions, forecasts, or state transitions.

**Status:** Emergent Candidate
**Governance:** ABX-Runes ϟ₇ (SSO) Access Only
**Version:** 0.1.0
**SEED Compliant:** ✅ Full provenance tracking

---

## The Three Detectors

### 1. Compliance vs Remix Detector (`compliance_remix`)
Detects the balance between rote compliance/repetition and creative remix/mutation.

**Subscores:**
- `remix_rate`: Creative mutation vs established patterns [0,1]
- `rote_repetition_rate`: Verbatim repetition intensity [0,1]
- `template_phrase_density`: Template/manufactured phrase density [0,1]
- `anchor_stability`: Topic anchor stability [0,1]

**Input Sources:**
- Slang drift metrics (drift_score, similarity_early_late)
- Lifecycle states (Proto, Front, Saturated, Dormant, Archived)
- Tau metrics (tau_velocity, tau_half_life, observation_count)
- Weather classification (MW-01 through MW-05)
- CSP fields (Formulaic Flag, MIO)
- Fog type counts from MWR enrichment

### 2. Meta-Awareness Detector (`meta_awareness`)
Detects meta-level discourse about manipulation, algorithms, and epistemic fatigue.

**Subscores:**
- `manipulation_discourse_score`: Awareness of manipulation techniques [0,1]
- `algorithm_awareness_score`: Discussion of algorithmic behavior [0,1]
- `fatigue_joke_rate`: Epistemic fatigue humor/irony [0,1]
- `predictive_mockery_rate`: Predictive pattern mockery [0,1]

**Input Sources:**
- Text content for keyword detection
- DMX manipulation metrics (overall_manipulation_risk, bucket)
- RDV affect axes (irony, humor, nihilism)
- EFTE fatigue metrics (threshold, saturation_risk, declining_engagement)
- Narrative manipulation metrics (RRS, CIS, EIL)
- Network campaign metrics (CUS)
- Risk indices (MRI, IRI)

### 3. Negative Space / Silence Detector (`negative_space`)
Detects topic dropout, visibility asymmetry, and abnormal silences.

**Subscores:**
- `topic_dropout_score`: Topics present in baseline but absent now [0,1]
- `visibility_asymmetry_score`: Source coverage asymmetry [0,1]
- `mention_gap_halflife_score`: Time since last mention normalized [0,1]

**Input Sources:**
- Symbol pool narratives (narrative_id, topic, theme)
- Source distribution (from FVC)
- History (minimum 3 entries for baseline comparison)
- Timestamps for gap calculation

---

## Changes

### New Components

**Detector Infrastructure** (`abraxas/detectors/shadow/`)
- `types.py`: Base types (DetectorId, DetectorStatus, DetectorValue, DetectorProvenance, clamp01)
- `compliance_remix.py`: Compliance vs Remix detector implementation (329 lines)
- `meta_awareness.py`: Meta-Awareness detector implementation (378 lines)
- `negative_space.py`: Negative Space detector implementation (337 lines)
- `registry.py`: Detector registry with compute_all_detectors() (184 lines)
- `__init__.py`: Package exports

**Shadow Metrics Integration** (Incremental Patch Only)
- Modified `abraxas/shadow_metrics/scg.py`: +9 lines (extract detectors, add to metadata)
- Modified `abraxas/shadow_metrics/fvc.py`: +9 lines (extract detectors, add to metadata)
- Modified `abraxas/shadow_metrics/nor.py`: +9 lines (extract detectors, add to metadata)
- Modified `abraxas/shadow_metrics/pts.py`: +9 lines (extract detectors, add to metadata)
- Modified `abraxas/shadow_metrics/clip.py`: +9 lines (extract detectors, add to metadata)
- Modified `abraxas/shadow_metrics/sei.py`: +9 lines (extract detectors, add to metadata)

**Test Suite** (22 tests, 100% passing)
- `tests/test_shadow_detectors_determinism.py`: 5 tests (171 lines)
- `tests/test_shadow_detectors_missing_inputs.py`: 10 tests (182 lines)
- `tests/test_shadow_detectors_bounds.py`: 7 tests (219 lines)

**Documentation**
- `docs/detectors/shadow_detectors_v0_1.md`: Complete specification (430 lines)

**Total:** +2,426 insertions across 16 files

---

## Test Results

```bash
$ python -m pytest tests/test_shadow_detectors_*.py -v

============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/user/Abraxas
configfile: pyproject.toml
collected 22 items

tests/test_shadow_detectors_determinism.py::test_compliance_remix_determinism PASSED
tests/test_shadow_detectors_determinism.py::test_meta_awareness_determinism PASSED
tests/test_shadow_detectors_determinism.py::test_negative_space_determinism PASSED
tests/test_shadow_detectors_determinism.py::test_registry_compute_all_determinism PASSED
tests/test_shadow_detectors_determinism.py::test_sorted_keys_in_output PASSED
tests/test_shadow_detectors_missing_inputs.py::test_compliance_remix_missing_required_inputs PASSED
tests/test_shadow_detectors_missing_inputs.py::test_compliance_remix_with_some_inputs PASSED
tests/test_shadow_detectors_missing_inputs.py::test_compliance_remix_with_all_required_inputs PASSED
tests/test_shadow_detectors_missing_inputs.py::test_meta_awareness_missing_text PASSED
tests/test_shadow_detectors_missing_inputs.py::test_meta_awareness_with_empty_text PASSED
tests/test_shadow_detectors_missing_inputs.py::test_meta_awareness_with_text PASSED
tests/test_shadow_detectors_missing_inputs.py::test_negative_space_missing_history PASSED
tests/test_shadow_detectors_missing_inputs.py::test_negative_space_with_sufficient_history PASSED
tests/test_shadow_detectors_missing_inputs.py::test_missing_keys_are_sorted PASSED
tests/test_shadow_detectors_missing_inputs.py::test_optional_vs_required_inputs PASSED
tests/test_shadow_detectors_bounds.py::test_clamp01_utility PASSED
tests/test_shadow_detectors_bounds.py::test_compliance_remix_bounds PASSED
tests/test_shadow_detectors_bounds.py::test_meta_awareness_bounds PASSED
tests/test_shadow_detectors_bounds.py::test_negative_space_bounds PASSED
tests/test_shadow_detectors_bounds.py::test_all_detectors_bounds PASSED
tests/test_shadow_detectors_bounds.py::test_zero_and_one_edge_cases PASSED
tests/test_shadow_detectors_bounds.py::test_mid_range_values PASSED

============================== 22 passed in 0.27s ==============================
```

**Coverage:**
- ✅ Determinism: Same inputs → identical outputs
- ✅ Missing inputs: `not_computable` when required fields absent
- ✅ Bounds enforcement: All values clamped to [0.0, 1.0]
- ✅ Sorted keys: All dicts/lists deterministically ordered
- ✅ Edge cases: Zero, one, and extreme values handled correctly

---

## Critical Guarantees

### SHADOW-ONLY (No Influence)
```python
# Every detector value includes:
provenance.no_influence_guarantee = True  # ALWAYS

# Shadow metrics only add to metadata, never affect computation:
if detectors:
    metadata["shadow_detector_evidence"] = detectors  # Evidence only
```

### Determinism (SEED Compliant)
```python
# Identical inputs → identical outputs
result1 = detector.compute_detector(context, history)
result2 = detector.compute_detector(context, history)
assert result1.model_dump() == result2.model_dump()  # ✅ Always true

# Provenance includes SHA-256 hashes
provenance.inputs_hash = hash_canonical_json(inputs)   # Sorted keys
provenance.config_hash = hash_canonical_json(config)   # Deterministic
```

### Bounds Enforcement
```python
# All values strictly clamped to [0.0, 1.0]
from abraxas.detectors.shadow.types import clamp01

value = clamp01(computed_value)  # max(0.0, min(1.0, value))
subscores = {k: clamp01(v) for k, v in raw_scores.items()}
```

### Access Control
```python
# ABX-Runes ϟ₇ (SSO) ONLY
# Direct access FORBIDDEN
from abraxas.runes.operators.sso import apply_sso

context = apply_sso(symbol_pool)  # Includes isolation proof
# context["shadow_detectors"] now populated
```

---

## Integration Notes

### Wiring Shadow Metrics

Shadow metrics automatically consume detector results when present:

```python
from abraxas.detectors.shadow.registry import compute_all_detectors, serialize_detector_results

# 1. Compute detectors (via ABX-Runes ϟ₇)
detector_results = compute_all_detectors(context, history)

# 2. Add to context
context["shadow_detectors"] = serialize_detector_results(detector_results)

# 3. Shadow metrics extract automatically
scg_inputs = scg.extract_inputs(context)
# scg_inputs["shadow_detectors"] contains detector evidence

# 4. Shadow metrics include in metadata (no influence on value)
scg_value, scg_metadata = scg.compute(scg_inputs, scg_config)
# scg_metadata["shadow_detector_evidence"] contains detector results
```

### not_computable Behavior

Detectors return `status=NOT_COMPUTABLE` when required inputs missing:

```python
result = compliance_remix.compute_detector({})  # Empty context
assert result.status == DetectorStatus.NOT_COMPUTABLE
assert result.value is None
assert "drift_score" in result.missing_keys
```

Shadow metrics that depend on detector outputs **must also return not_computable** if required detectors are not_computable.

---

## Review Checklist

### Code Quality
- [x] All code follows Abraxas naming conventions (snake_case, PascalCase)
- [x] Type hints on all functions
- [x] Docstrings for all public functions/classes
- [x] No placeholders or TODOs
- [x] No dead code or commented-out sections

### Determinism & SEED Compliance
- [x] All outputs deterministic (22 tests verify)
- [x] Sorted keys in all dicts/lists
- [x] SHA-256 provenance for all computations
- [x] `hash_canonical_json()` used for hashing
- [x] No timestamps in computation (only in provenance)
- [x] No random operations

### Shadow-Only Guarantee
- [x] `no_influence_guarantee=True` in all provenance
- [x] Shadow metrics only add to metadata (never affect value)
- [x] No hidden coupling to forecasts/decisions
- [x] Clear documentation of shadow-only behavior

### Bounds & Error Handling
- [x] All values clamped to [0.0, 1.0] via `clamp01()`
- [x] `not_computable` when required inputs missing
- [x] `missing_keys` sorted and documented
- [x] Edge cases tested (zero, extreme values)

### Integration
- [x] Minimal diffs to shadow metrics (Incremental Patch Only)
- [x] No breaking changes to existing APIs
- [x] Backward compatible (metrics work without detectors)
- [x] ABX-Runes ϟ₇ access control documented

### Testing
- [x] 22 tests, 100% passing
- [x] Determinism tests (5 tests)
- [x] Missing inputs tests (10 tests)
- [x] Bounds tests (7 tests)
- [x] Test coverage for all three detectors

### Documentation
- [x] Complete specification in `docs/detectors/shadow_detectors_v0_1.md`
- [x] Usage examples provided
- [x] Input requirements documented (required vs optional)
- [x] Output schemas documented
- [x] Integration notes included

---

## Known Limitations

1. **Keyword Detection**: Meta-awareness uses simple keyword matching (not semantic analysis)
2. **History Requirement**: Negative Space requires ≥3 history entries (configurable)
3. **Proxy Metrics**: Some subscores use proxies (e.g., template_phrase_density from fog types)
4. **No Real-Time Adaptation**: Detectors do not learn or adapt (fully deterministic)

These are by design for v0.1 (emergent candidate). Future enhancements tracked in docs.

---

## Future Work (Not in Scope)

- [ ] Semantic analysis for meta-awareness (replace keyword matching)
- [ ] Adaptive thresholds based on domain
- [ ] Multi-language support
- [ ] Temporal analysis for trend detection
- [ ] Activate rent-payment gates with real correlation/stability checks
- [ ] Patch ledger system for incremental evolution

---

## Deployment Steps

1. **Merge this PR** (after review approval)
2. **Activate ABX-Runes ϟ₇ (SSO)** integration
3. **Monitor shadow outputs** for 1-2 weeks
4. **Governance review** for promotion from emergent candidate
5. **Enable rent-payment gates** after stability verified

---

## References

- **Shadow Structural Metrics Spec:** `docs/specs/shadow_structural_metrics.md`
- **Abraxas Canon Ledger:** `docs/canon/ABRAXAS_CANON_LEDGER.txt`
- **Oracle Signal Layer:** `abraxas/oracle/v2/`
- **Slang Drift Analysis:** `abx/slang_drift.py`
- **Weather Registry:** `abraxas/weather/registry.py`

---

## Questions for Reviewers

1. **Access Control**: Should we add explicit runtime checks for ABX-Runes ϟ₇ invocation, or rely on documentation?
2. **Keyword Lists**: Should meta-awareness keyword lists be configurable, or hardcoded for v0.1?
3. **History Length**: Is 3-entry minimum for Negative Space appropriate, or should it be higher?
4. **Naming**: Are detector names clear? (`compliance_remix` vs `compliance_vs_remix`?)

---

**Ready for review.** All tests passing, documentation complete, zero placeholders.
