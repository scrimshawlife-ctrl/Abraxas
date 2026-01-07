# ABX-Runes Coupling Migration - Session 2026-01-07

**Session ID**: `claude/continue-work-ILQQS`
**Date**: 2026-01-07
**Starting violations**: 48
**Ending violations**: 39
**Eliminated**: 9 violations (18.75% session reduction)
**Total progress**: 75 → 39 (48% total reduction)

---

## Session Summary

Successfully implemented 9 new capability contracts across 4 subsystems (memetic, evidence, conspiracy, forecast):

### Capabilities Implemented

#### 1. **memetic.dmx_context.load** (ϟ_MEMETIC_DMX_CONTEXT)
- **Files**: `schemas/capabilities/load_dmx_context_{input,output}.schema.json`
- **Adapter**: `abraxas/memetic/rune_adapter.py:load_dmx_context_deterministic`
- **Purpose**: Loads DMX manipulation risk context (overall_manipulation_risk, bucket classification)
- **Migrated**: `abx/forecast_score.py`, `abx/forecast_log.py`
- **Commit**: `1a7a27c`

#### 2. **memetic.term_index.build** (ϟ_MEMETIC_TERM_INDEX_BUILD)
- **Files**: `schemas/capabilities/term_index_build_{input,output}.schema.json`
- **Adapter**: `abraxas/memetic/rune_adapter.py:build_term_index_deterministic`
- **Purpose**: Builds term → metrics index from A2 phase artifacts
- **Output**: Lowercase term keys → {manipulation_risk, attribution_strength, source_diversity, consensus_gap}

#### 3. **memetic.term_index.reduce** (ϟ_MEMETIC_TERM_INDEX_REDUCE)
- **Files**: `schemas/capabilities/term_index_reduce_{input,output}.schema.json`
- **Adapter**: `abraxas/memetic/rune_adapter.py:reduce_weighted_metrics_deterministic`
- **Purpose**: Aggregates metrics across terms using term index
- **Output**: Weighted means and counts for all metrics
- **Migrated**: `abx/forecast_log.py`
- **Commit**: `dca5e16`

#### 4. **memetic.term_assign.build_index** (ϟ_MEMETIC_TERM_TOKEN_INDEX)
- **Files**: `schemas/capabilities/term_token_index_build_{input,output}.schema.json`
- **Adapter**: `abraxas/memetic/rune_adapter.py:build_term_token_index_deterministic`
- **Purpose**: Tokenizes terms and builds term → token set index for claim assignment
- **Algorithm**: Regex `[a-z0-9]{3,}` token extraction, sorted lists for determinism

#### 5. **memetic.term_assign.assign** (ϟ_MEMETIC_TERM_ASSIGN)
- **Files**: `schemas/capabilities/term_assign_{input,output}.schema.json`
- **Adapter**: `abraxas/memetic/rune_adapter.py:assign_claim_to_terms_deterministic`
- **Purpose**: Assigns claims to terms via token overlap ranking
- **Parameters**: `min_overlap` (default 1), `max_terms` (default 5)
- **Determinism**: Stable sort by (-overlap, term)
- **Migrated**: `abx/term_claims_run.py`
- **Commit**: `3c48bdd`

#### 6. **evidence.index.evidence_by_term** (ϟ_EVIDENCE_INDEX_BY_TERM)
- **Files**: `schemas/capabilities/evidence_by_term_{input,output}.schema.json`
- **Adapter**: `abraxas/evidence/rune_adapter.py:evidence_by_term_deterministic` (NEW FILE)
- **Purpose**: Loads evidence bundles and indexes them by lowercase term
- **Output**: Dict[str, List[Dict]] mapping terms to evidence bundles

#### 7. **evidence.support.support_weight** (ϟ_EVIDENCE_SUPPORT_WEIGHT)
- **Files**: `schemas/capabilities/evidence_support_weight_{input,output}.schema.json`
- **Adapter**: `abraxas/evidence/rune_adapter.py:support_weight_for_claim_deterministic`
- **Purpose**: Computes support weight bonus based on Jaccard similarity
- **Algorithm**: Token overlap between claim and evidence, credence-weighted
- **Output**: (support_weight [0, max_bonus], debug_dict)
- **Migrated**: `abx/term_claims_run.py`
- **Commit**: `b9045e3`

#### 8. **conspiracy.csp.compute_claim** (ϟ_CSP_COMPUTE_CLAIM)
- **Files**: `schemas/capabilities/csp_compute_claim_{input,output}.schema.json`
- **Adapter**: `abraxas/conspiracy/rune_adapter.py:compute_claim_csp_deterministic` (NEW FILE)
- **Purpose**: Computes Conspiracy Susceptibility Profile (CSP) for claims
- **Algorithm**: Inherits term CSP, infers COH (Coordination Hypothesis) from claim text, boosts EA with evidence
- **Output**: CSP dict with {COH, EA, CIP, MIO, FF, tag, flags}
- **Migrated**: `abx/term_claims_run.py`
- **Commit**: `2548c07`

#### 9. **forecast.gating_policy.decide_gate** (ϟ_FORECAST_GATING_POLICY)
- **Files**: `schemas/capabilities/gating_policy_decide_{input,output}.schema.json`
- **Adapter**: `abraxas/forecast/rune_adapter.py:decide_gate_deterministic`
- **Purpose**: Determines forecast gating decision based on DMX context and metrics
- **Algorithm**: Applies DMX bucket logic (LOW/MED/HIGH), returns EEB multiplier, horizon_max, evidence escalation
- **Output**: GateDecision dict with version, eeb_multiplier, horizon_max, evidence_escalation, flags, provenance
- **Migrated**: `abx/forecast_log.py`, `abx/forecast_score.py` (2 calls)
- **Commit**: `5c1e071`

---

## Files Modified This Session

### New Files Created (22 total)
**Schemas** (18 files):
- `schemas/capabilities/load_dmx_context_{input,output}.schema.json`
- `schemas/capabilities/term_index_{build,reduce}_{input,output}.schema.json`
- `schemas/capabilities/term_token_index_build_{input,output}.schema.json`
- `schemas/capabilities/term_assign_{input,output}.schema.json`
- `schemas/capabilities/evidence_by_term_{input,output}.schema.json`
- `schemas/capabilities/evidence_support_weight_{input,output}.schema.json`
- `schemas/capabilities/csp_compute_claim_{input,output}.schema.json`
- `schemas/capabilities/gating_policy_decide_{input,output}.schema.json`

**Adapters** (2 files):
- `abraxas/evidence/rune_adapter.py` - NEW rune adapter for evidence subsystem
- `abraxas/conspiracy/rune_adapter.py` - NEW rune adapter for conspiracy subsystem

**Documentation** (1 file):
- `docs/work_sessions/abx_runes_session_2026_01_07.md` - This file

### Modified Files (6 total)
- `abraxas/memetic/rune_adapter.py` - Extended with 5 new functions (380 lines total)
- `abraxas/forecast/rune_adapter.py` - Extended with decide_gate_deterministic
- `abraxas/runes/registry.json` - Added 9 capability registrations
- `abx/forecast_log.py` - Migrated dmx_context, term_index, decide_gate capabilities
- `abx/forecast_score.py` - Migrated decide_gate capability (2 calls)
- `abx/term_claims_run.py` - Migrated term_assign, evidence, compute_claim_csp capabilities

---

## Remaining Violations Analysis (39 total)

### Top 10 Files by Violation Count
```
5 - abx/a2_phase.py
3 - abx/acquisition_plan.py
2 - abx/forecast_log.py (conspiracy.policy, forecast.horizon_policy, forecast.ledger)
2 - abx/ui/chat_engine.py
2 - abx/operators/alive_run.py
2 - abx/mwr.py
2 - abx/evogate.py
2 - abx/cli.py
1 - abx/forecast_score.py (forecast.uncertainty only)
1 - abx/term_claims_run.py (conspiracy.csp.compute_term_csp only)
```

### Violation Breakdown by Module

**forecast.* (9 violations)**:
- ~~`forecast.gating_policy.decide_gate`~~ ✅ MIGRATED (was 2x: forecast_log, forecast_score)
- `forecast.horizon_policy.{compare_horizon, enforce_horizon_policy}` (2x: forecast_log)
- `forecast.ledger.issue_prediction` (1x: forecast_log)
- `forecast.uncertainty.horizon_uncertainty_multiplier` (1x: forecast_score)
- `forecast.scoring.ExpectedErrorBand` (1x: forecast_score - TYPE import only)
- `forecast.policy_candidates.candidates_v0_1` (2x: horizon_policy_select, horizon_policy_select_tc)

**conspiracy.* (3 violations)**:
- `conspiracy.csp.compute_term_csp` (1x: a2_phase) - NOTE: compute_claim_csp migrated ✅
- `conspiracy.policy.{csp_horizon_clamp, apply_horizon_cap}` (2x: forecast_log)

**memetic.* (5 violations)**:
- `memetic.metrics_reduce.reduce_provenance_means` (1x: a2_phase)
- `memetic.term_consensus_map.load_term_consensus_map` (1x: a2_phase)
- `memetic.temporal.build_temporal_profiles` (1x: a2_phase)
- `memetic.extract.{build_mimetic_weather, extract_terms, read_oracle_texts}` (1x: mwr.py)
- `memetic.dmx.compute_dmx` (1x: mwr.py)

**evidence.* (3 violations)**:
- `evidence.lift.{load_bundles_from_index, term_lift, uplift_factors}` (1x: a2_phase)

**Other modules** (19 violations):
- `alive.*` (4x: operators/alive_run, alive_export, alive_integrate_slack)
- `drift.orchestrator`, `core.rendering` (2x: ui/chat_engine)
- `osh.executor`, `evolve.promotion_builder`, `artifacts.proof_bundle`, etc.

---

## Next Recommended Steps

### High-Priority Targets (Most Impact)

#### 1. ~~**conspiracy.csp.compute_claim_csp**~~ ✅ COMPLETED
- Migrated in capability `conspiracy.csp.compute_claim` (ϟ_CSP_COMPUTE_CLAIM)
- Reduced violations: 42 → 41

#### 2. ~~**forecast.gating_policy.decide_gate**~~ ✅ COMPLETED
- Migrated in capability `forecast.gating_policy.decide_gate` (ϟ_FORECAST_GATING_POLICY)
- Reduced violations: 41 → 39

#### 3. **evidence.lift.* functions** (3 functions, 1 file → 3 violations)
- **Used in**: `a2_phase.py`
- **Functions**: `load_bundles_from_index`, `term_lift`, `uplift_factors`
- **Purpose**: Evidence-based attribution/diversity uplift for terms
- **Impact**: Could reduce a2_phase violations from 5 → 2

#### 4. **memetic.temporal.build_temporal_profiles** (1 usage → 1 violation)
- **Used in**: `a2_phase.py`
- **Purpose**: Builds temporal profiles for terms (half-life, momentum, recurrence)
- **Impact**: Core memetic dynamics calculation

---

## Implementation Patterns (Copy-Paste Template)

### Schema Creation Pattern

**Input Schema** (`schemas/capabilities/<name>_input.schema.json`):
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "<Capability Name> Input",
  "description": "Input schema for <capability_id> capability",
  "type": "object",
  "required": ["param1", "param2"],
  "properties": {
    "param1": {
      "type": "string",
      "description": "Parameter description"
    },
    "seed": {
      "type": ["integer", "null"],
      "description": "Optional deterministic seed"
    }
  },
  "additionalProperties": false
}
```

**Output Schema** (`schemas/capabilities/<name>_output.schema.json`):
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "<Capability Name> Output",
  "description": "Output schema for <capability_id> capability",
  "type": "object",
  "required": ["result_field", "provenance", "not_computable"],
  "properties": {
    "result_field": {
      "type": "object",
      "description": "Result description"
    },
    "provenance": {
      "type": ["object", "null"],
      "properties": {
        "operation_id": {
          "type": "string",
          "const": "<capability_id>"
        },
        "inputs_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
        "timestamp_utc": {"type": "string", "format": "date-time"}
      }
    },
    "not_computable": {
      "type": "null",
      "description": "Always null - operation never fails"
    }
  },
  "additionalProperties": false
}
```

### Rune Adapter Pattern

**Create or extend adapter** (`abraxas/<subsystem>/rune_adapter.py`):
```python
"""Rune adapter for <subsystem> capabilities.

SEED Compliant: Deterministic, provenance-tracked.
"""
from __future__ import annotations
from typing import Any, Dict, Optional
from abraxas.core.provenance import canonical_envelope
from abraxas.<subsystem>.<module> import <function> as <function>_core

def <function>_deterministic(
    param1: str,
    param2: Dict[str, Any],
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible <function> wrapper.

    Args:
        param1: Description
        param2: Description
        seed: Optional deterministic seed

    Returns:
        Dictionary with result, provenance, not_computable
    """
    # Call core function
    result = <function>_core(param1, param2)

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result={"result_key": result},
        config={},
        inputs={"param1": param1, "param2": param2},
        operation_id="<subsystem>.<module>.<function>",
        seed=seed
    )

    return {
        "result_key": result,
        "provenance": envelope["provenance"],
        "not_computable": None
    }

__all__ = ["<function>_deterministic"]
```

### Registry Entry Pattern

**Add to** `abraxas/runes/registry.json`:
```json
{
  "capability_id": "<subsystem>.<module>.<function>",
  "rune_id": "ϟ_<SUBSYSTEM>_<NAME>",
  "operator_path": "abraxas.<subsystem>.rune_adapter:<function>_deterministic",
  "version": "1.0.0",
  "input_schema": "schemas/capabilities/<name>_input.schema.json",
  "output_schema": "schemas/capabilities/<name>_output.schema.json",
  "provenance_required": true,
  "deterministic": true,
  "evidence_mode": "data_processing"
}
```

**Evidence modes**: `data_loading`, `data_processing`, `classification`, `prediction_lane`, `policy_enforcement`, `ledger_integrity`

### Migration Pattern

**In** `abx/<file>.py`:
```python
# At top of file:
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext

# Replace direct import:
# from abraxas.<subsystem>.<module> import <function>

# Create context (once per script):
ctx = RuneInvocationContext(
    run_id=args.run_id,
    subsystem_id="abx.<filename>",
    git_hash="unknown"
)

# Replace function call:
# result = <function>(param1, param2)

# With capability invocation:
result_dict = invoke_capability(
    "<subsystem>.<module>.<function>",
    {"param1": param1, "param2": param2},
    ctx=ctx,
    strict_execution=True
)
result = result_dict["result_key"]
```

---

## Testing Checklist

Before committing each capability:
- [ ] Schemas created with correct capability_id in output
- [ ] Adapter function wraps core function (no logic changes)
- [ ] Adapter converts non-JSON types (sets → sorted lists)
- [ ] Registry entry points to correct adapter function
- [ ] Capability invocation tested manually (optional but recommended)
- [ ] All migrations compile (no import errors)
- [ ] Coupling lint decreases: `grep -r "from abraxas\." abx/ --include="*.py" | grep -v "abraxas.runes" | grep -v "abraxas.core.provenance" | wc -l`

---

## Git Workflow

```bash
# Create new capability (schemas + adapter + registry)
git add schemas/capabilities/<name>_*.schema.json
git add abraxas/<subsystem>/rune_adapter.py
git add abraxas/runes/registry.json

# Migrate files
git add abx/<file>.py

# Commit with descriptive message
git commit -m "feat: Add <subsystem>.<capability> capability contract

Implements <description> via ABX-Runes:
- Created schemas/capabilities/<name>_{input,output}.schema.json
- Extended abraxas/<subsystem>/rune_adapter.py with <function>_deterministic
- Registered in abraxas/runes/registry.json with ϟ_<RUNE_ID>
- Migrated abx/<files>
- Reduced coupling violations: <before> → <after>

<Additional context>"

# Push to branch
git push -u origin claude/continue-work-ILQQS
```

---

## Current State

### Git Branch
- **Branch**: `claude/continue-work-ILQQS`
- **Last commit**: `5c1e071` - forecast.gating_policy.decide_gate capability
- **Commits this session**: 6 total
  - `1a7a27c` - memetic.dmx_context.load
  - `dca5e16` - memetic.term_index.{build,reduce}
  - `3c48bdd` - memetic.term_assign.{build_index,assign}
  - `b9045e3` - evidence.{index,support}
  - `2548c07` - conspiracy.csp.compute_claim
  - `5c1e071` - forecast.gating_policy.decide_gate

### Violations Progress
```
Session start:         48 violations
After dmx/term_index:  45 violations (-3)
After term_assign:     44 violations (-1)
After evidence:        42 violations (-2)
After csp:             41 violations (-1)
After gating_policy:   39 violations (-2)
Total session:         -9 violations (18.75% reduction)
```

### Capability Registry State
Total capabilities: 17
- forecast.* : 5 capabilities
- evolve.* : 2 capabilities
- memetic.* : 7 capabilities
- evidence.* : 2 capabilities
- conspiracy.* : 1 capability

---

## Known Issues & Considerations

### Set→List Conversion
When core functions return `Dict[str, Set[str]]`, convert to `Dict[str, List[str]]` for JSON serialization:
```python
# Core returns sets
result_sets = core_function(...)

# Convert to sorted lists
result = {key: sorted(list(val)) for key, val in result_sets.items()}
```

### Type-Only Imports
Some violations are TYPE imports only (e.g., `ExpectedErrorBand` in forecast_score.py). These may need special handling:
- Option 1: Keep type import, accept 1 violation per file
- Option 2: Move type to shared location, import from there
- Option 3: Inline type definition

### Evidence Mode Selection
Choose appropriate evidence_mode:
- **data_loading**: Reads from disk/database (evidence_by_term, load_dmx_context)
- **data_processing**: Transforms data (term_index.reduce, support_weight)
- **classification**: Assigns categories (term_assign, horizon_classify)
- **prediction_lane**: Forecast generation (oracle.v2.run, brier_score)
- **policy_enforcement**: Applies governance rules (enforce_non_truncation)
- **ledger_integrity**: Append-only operations (ledger.append)

### CSP (Conspiracy Susceptibility Profile) Module
The `conspiracy.csp` module is complex with multiple interdependent functions:
- `compute_ea_from_profile` - Evidence Adequacy
- `compute_ff_from_profile` - Falsifiability / Fork resistance
- `compute_mio_from_context` - Manipulation Impact Opacity
- `compute_term_csp` - Term-level CSP (5 violations elsewhere use this)
- `compute_claim_csp` - Claim-level CSP (2 violations in term_claims_run, a2_phase)
- `tag_csp` - CSP tagging logic

**Recommendation**: Create single `conspiracy.csp.compute_csp` capability that handles both term and claim CSP, or create two separate capabilities.

---

## Handoff Checklist

✅ All changes committed and pushed
✅ TODO list updated
✅ Coupling violations verified (48 → 42)
✅ Documentation created
✅ Next steps clearly defined
✅ Code patterns documented
✅ Git state documented

**Ready for next session.**

---

## Quick Start for Next Session

```bash
# 1. Verify current state
cd /home/user/Abraxas
git status
git log --oneline -5

# 2. Check current violations
grep -r "from abraxas\." abx/ --include="*.py" | grep -v "abraxas.runes" | grep -v "abraxas.core.provenance" | wc -l
# Should show: 39

# 3. Pick next target (recommended: evidence.lift.* functions or conspiracy.csp.compute_term_csp)
# See "Next Recommended Steps" section above

# 4. Follow implementation patterns
# Create schemas → Create/extend adapter → Register → Migrate → Test → Commit

# 5. Update this document with new progress
# Edit: docs/work_sessions/abx_runes_session_2026_01_07.md
```

---

**End of session documentation.**
