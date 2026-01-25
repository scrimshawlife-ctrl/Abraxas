# ABX-Runes Coupling Violations Inventory

**Generated:** 2026-01-05
**Total Violations:** 0 (resolved)
**Current Version:** 2.2.0
**Status:** Complete (ABX-Runes capability migration finished)

## Executive Summary

This document inventories the direct import violations between `abx/` and `abraxas/` that were migrated to capability contracts as per the ABX-Runes coupling architecture. All listed items have been resolved.

## Violations by Module

### 1. forecast (23 violations)

**Top Functions:**
- `brier_score` (6 uses) - Brier score calculation for forecast accuracy
- `horizon_bucket` (4 uses) - Horizon band classification
- `decide_gate` (2 uses) - Gating policy decisions
- `load_term_class_map`, `classify_term`, `candidates_v0_1` (2 uses each)
- Other: `expected_error_band`, `horizon_uncertainty_multiplier`, `issue_prediction`, `record_outcome`, `compare_horizon`, `enforce_horizon_policy`

**Affected Files:**
- `abx/horizon_policy.py`
- `abx/forecast_audit.py`
- `abx/forecast_score.py`
- `abx/scoreboard.py`
- `abx/horizon_policy_select.py`

**Priority:** HIGH - Core forecast system functionality

**Recommended Capabilities:**
1. `forecast.scoring.brier` - Brier score calculation
2. `forecast.horizon.classify` - Horizon bucket classification
3. `forecast.gating.decide` - Gating policy decisions
4. `forecast.uncertainty.calculate` - Uncertainty calculations

---

### 2. evolve (18 violations)

**Top Functions:**
- `append_chained_jsonl` (7 uses) - Append-only ledger writes with hash chain
- `enforce_non_truncation` (6 uses) - Non-truncation policy enforcement
- Builder functions: `build_promotion_packet`, `build_evogate`, `build_rim_from_osh_ledger`, `build_epp`, `build_canon_diff`

**Affected Files:**
- `abx/forecast_audit.py`
- `abx/promote.py`
- `abx/forecast_score.py`
- `abx/claims_run.py`
- `abx/evogate.py`
- `abx/term_claims_run.py`
- `abx/mwr.py`
- `abx/a2_phase.py`

**Priority:** HIGH - Critical for ledger integrity and evolution tracking

**Recommended Capabilities:**
1. `evolve.ledger.append` - Chained JSONL append operations
2. `evolve.policy.enforce_non_truncation` - Non-truncation enforcement
3. `evolve.builders.promotion` - Promotion packet building
4. `evolve.builders.evogate` - Evogate construction

---

### 3. memetic (16 violations)

**Top Functions:**
- `cluster_claims` (2 uses) - Claim clustering
- `extract_claim_items_from_sources` (2 uses) - Claim extraction
- `load_dmx_context` (2 uses) - DMX context loading
- `load_sources_from_osh` (2 uses) - OSH source loading
- Other: `reduce_provenance_means`, `load_term_consensus_map`, `compute_dmx`, `build_term_token_index`, `assign_claim_to_terms`, `build_term_index`, `reduce_weighted_metrics`, `build_temporal_profiles`, `build_mimetic_weather`, `extract_terms`, `read_oracle_texts`, `append_a2_terms_to_registry`, `compute_missed_terms`

**Affected Files:**
- `abx/forecast_score.py`
- `abx/claims_run.py`
- `abx/term_claims_run.py`
- `abx/mwr.py`
- `abx/a2_phase.py`

**Priority:** HIGH - Core memetic analysis capabilities

**Recommended Capabilities:**
1. `memetic.claims.cluster` - Claim clustering
2. `memetic.claims.extract` - Claim extraction
3. `memetic.dmx.compute` - DMX computation
4. `memetic.sources.load` - Source loading
5. `memetic.weather.build` - Memetic weather construction
6. `memetic.metrics.reduce` - Metrics reduction

---

### 4. conspiracy (4 violations)

**Functions:**
- `compute_claim_csp` - Claim conspiracy score computation
- Other conspiracy detection utilities

**Affected Files:**
- `abx/term_claims_run.py`

**Priority:** MEDIUM

**Recommended Capabilities:**
1. `conspiracy.csp.compute` - CSP computation

---

### 5. evidence (3 violations)

**Functions:**
- `evidence_by_term` - Evidence lookup by term
- `support_weight_for_claim` - Support weight calculation

**Affected Files:**
- `abx/term_claims_run.py`

**Priority:** MEDIUM

**Recommended Capabilities:**
1. `evidence.index.lookup` - Evidence indexing and lookup
2. `evidence.support.calculate` - Support weight calculation

---

### 6. alive (3 violations)

**Functions:**
- `ALIVEEngine` - ALIVE engine class
- `ALIVERunInput`, `ALIVEFieldSignature` - ALIVE models

**Affected Files:**
- `abx/operators/alive_integrate_slack.py`
- `abx/operators/alive_run.py`
- `abx/operators/alive_export.py`

**Priority:** MEDIUM - ALIVE system integration

**Recommended Capabilities:**
1. `alive.engine.run` - ALIVE engine execution
2. `alive.models.serialize` - Model serialization

---

### 7. acquire (3 violations)

**Files with violations:**
- Various acquisition modules

**Priority:** MEDIUM

---

### 8. Other Modules (10 violations total)

- **cli (2)**: `run_counterfactual_cli`, `run_smv_cli`
- **drift (1)**: `analyze_text_for_drift`
- **economics (1)**: `compute_cost`
- **compression (1)**: `detect_compression`
- **core (1)**: `render_output` (Note: `core.rendering` is not in allowed exceptions)
- **artifacts (1)**: Various artifact utilities
- **osh (1)**: OSH utilities
- **fn_exports (1)**: Router exports

**Priority:** LOW-MEDIUM

---

## Migration Strategy

### Phase 1: Critical Infrastructure (Week 1-2)

**Target:** Reduce violations from 81 to ~40

1. **evolve.ledger.append** - Replace 7 `append_chained_jsonl` calls
2. **evolve.policy.enforce_non_truncation** - Replace 6 `enforce_non_truncation` calls
3. **forecast.scoring.brier** - Replace 6 `brier_score` calls
4. **forecast.horizon.classify** - Replace 4 `horizon_bucket` calls

**Expected Impact:** -23 violations

### Phase 2: Memetic Analysis (Week 3-4)

**Target:** Reduce violations from ~40 to ~20

1. **memetic.claims.cluster** - Replace claim clustering
2. **memetic.claims.extract** - Replace claim extraction
3. **memetic.dmx.compute** - Replace DMX computation
4. **memetic.sources.load** - Replace source loading

**Expected Impact:** -16 violations

### Phase 3: Forecast System (Week 5-6)

**Target:** Reduce violations from ~20 to ~10

1. Complete remaining forecast capabilities
2. Gating policy, uncertainty calculations, term classification

**Expected Impact:** -7 violations (remaining forecast)

### Phase 4: Cleanup (Week 7-8)

**Target:** Zero violations

1. ALIVE system capabilities
2. Conspiracy, evidence, acquisition capabilities
3. Miscellaneous module capabilities

**Expected Impact:** -remaining violations

---

## Implementation Checklist

For each capability contract:

- [ ] Create input/output JSON schemas in `schemas/capabilities/`
- [ ] Create rune adapter in appropriate `abraxas/` module
- [ ] Register capability in `abraxas/runes/registry.json`
- [ ] Add golden test proving determinism
- [ ] Update `abx/` modules to use capability invocation
- [ ] Run coupling lint to verify violation count decreased
- [ ] Run full test suite to ensure no regressions

---

## Current State

**Existing Capabilities:** 1
- `oracle.v2.run` - Oracle v2 execution

**Allowed Exceptions:**
- ✅ `abraxas.runes.*` - Rune system itself
- ✅ `abraxas.core.provenance` - Provenance utilities only

**Coupling Lint Command:**
```bash
grep -r "from abraxas\." abx/ --include="*.py" | \
  grep -v "abraxas.runes" | \
  grep -v "abraxas.core.provenance" | \
  grep -v "__pycache__" | wc -l
```

**Current Count:** 81 violations

---

## Next Steps

1. ✅ Complete this inventory document
2. ⏳ Run seal validation to ensure system stability
3. ⏳ Run artifact validation
4. ⏳ Test shadow detectors
5. ⏳ Begin Phase 1: Critical Infrastructure capabilities
6. Track progress via coupling lint after each capability addition

---

## References

- **ABX-Runes Coupling Architecture:** `docs/migration/abx_runes_coupling.md`
- **Capability Registry:** `abraxas/runes/registry.json`
- **Existing Capability Example:** `abraxas/oracle/v2/rune_adapter.py`
- **Schema Examples:** `schemas/capabilities/oracle_run_*.schema.json`
