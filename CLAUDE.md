# CLAUDE.md - AI Assistant Development Guide for Abraxas

**Last Updated:** 2026-01-11
**Guide Version:** 2.2.2
**Ecosystem Baseline:** v4.2.0
**Purpose:** Comprehensive guide for AI assistants working with the Abraxas codebase

---

## Recent Updates (v2.2.2)

**2026-01-11** - Comprehensive codebase audit identifying stubs and incomplete features:

### Audit Summary (150+ items cataloged)
- **P0 Critical**: 15 items blocking production readiness
  - Acceptance test suite has 7 TODOs requiring real oracle integration
  - Seal validation infrastructure lacks tests and documentation
  - Runtime infrastructure modules undertested (9 of 10 modules)
  - 3 placeholder test files with `assert True` stubs
- **P1 High Priority**: 45 items blocking feature completeness
  - 81 ABX-Runes coupling violations across 34 files (~10% migrated)
  - 6 auto-generated rune operator stubs (WSSS, RFA, SDS, IPL, ADD, TAM)
  - Oracle daily run missing data source integration
  - Scenario envelope runner missing weather/D/M/almanac snapshots
- **P2 Medium Priority**: 90+ technical debt items
  - ALIVE system export/integration stubs
  - TypeScript server TODOs (DB persistence, error handling)
  - 50+ placeholder comments across codebase
- **Test Coverage**: ~33% by file count (227 test files, 693 Python files in abraxas/)
- **Documentation Gaps**: Shadow detector integration example missing, seal validation guide needed

See "Known Stubs and Incomplete Features" section below for detailed inventory.

---

## Recent Updates (v2.2.0)

**2026-01-04** - Major release with seal validation, ABX-Runes coupling, and enhanced shadow metrics:

### 1. **Seal Release Pack** - Production-grade release validation
   - `VERSION` file + `abx_versions.json` for version management
   - `scripts/seal_release.py` - Deterministic seal script with artifact validation
   - `scripts/validate_artifacts.py` - Artifact validator CLI
   - 9 JSON schemas for artifact validation (`schemas/*.schema.json`)
   - `Makefile` with `seal` and `validate` targets
   - Complete SealReport.v0 artifact with provenance tracking

### 2. **ABX-Runes Coupling Architecture** (PR #83, #84)
   - **MANDATORY**: All `abx/` → `abraxas/` communication via capability contracts
   - New modules: `abraxas/runes/capabilities.py`, `abraxas/runes/registry.json`
   - Oracle v2 rune adapter: `abraxas/oracle/v2/rune_adapter.py`
   - Migration guide: `docs/migration/abx_runes_coupling.md`
   - **Forbidden**: Direct imports across subsystem boundaries (except `abraxas.runes.*` and `abraxas.core.provenance`)

### 3. **Shadow Detectors v0.1** - Observe-only pattern detection
   - **3 New Detectors**: Compliance vs Remix, Meta-Awareness, Negative Space
   - Complete infrastructure: `abraxas/detectors/shadow/` (7 files)
   - Integration with Shadow Structural Metrics (incremental patches only)
   - 22 comprehensive tests (determinism, bounds, missing inputs)
   - Documentation: `docs/detectors/shadow_detectors_v0_1.md`
   - **Guarantee**: `no_influence=True` - never affects forecasts or decisions

### 4. **Runtime Infrastructure** - Policy snapshots & invariance gates
   - `abraxas/runtime/` package (13 modules):
     - `policy_snapshot.py` - Immutable policy snapshots for provenance
     - `invariance_gate.py` - DozenRunGate for stability validation
     - `pipeline_bindings.py` - Native pipeline binding resolution
     - `artifacts.py`, `retention.py`, `results_pack.py` - Artifact management
   - `abraxas/ers/` - Event Runtime System (6 modules)
     - Scheduler, bindings, invariance, trace tracking
   - Enhanced `abraxas/oracle/registry.py` with capability contracts

### 5. **Enhanced Shadow Detectors** - Additional pattern detection
   - `abraxas/detectors/shadow/anagram.py` - Anagram pattern detection
   - `abraxas/detectors/shadow/token_density.py` - Token density analysis
   - `abraxas/detectors/shadow/normalize.py` - Text normalization utilities
   - `abraxas/detectors/shadow/util.py` - Shared utilities
   - `abraxas/detectors/shadow/registry_impl.py` - Enhanced registry implementation

**Total Changes**: 30+ new files, comprehensive testing infrastructure, production-ready release validation

---

## TODO

### Completed
- ✅ P0 (done): Add determinism + strict-execution tests for oracle runes (SDS/IPL/ADD)

### P0 - Production Blockers (2026-01-11 Audit)
1. **Complete Acceptance Test Suite** (`tools/acceptance/run_acceptance_suite.py`)
   - Wire up real oracle pipeline calls (7 TODOs at lines 128, 184, 240, 297, 353, 404, 438)
   - Implement schema validation using `schemas/*.schema.json`
   - Add drift classification logic from `abraxas.drift.*`
   - **Blocking**: Cannot verify production readiness without real oracle integration

2. **Fix or Remove Placeholder Tests**
   - `tests/test_scenario_router.py` - 2 tests with `assert True`
   - `tests/test_integrity_hash_chain.py` - 2 tests with `assert True`
   - `tests/test_integrity_brief.py` - 2 tests with `assert True`
   - **Blocking**: False test coverage - tests pass without verifying functionality

3. **Add Seal Release Tests**
   - Test `scripts/seal_release.py` end-to-end
   - Test `scripts/validate_artifacts.py` with valid/invalid inputs
   - Verify SealReport.v0 schema compliance
   - **Blocking**: No validation of seal infrastructure

4. **Add Runtime Infrastructure Tests**
   - Missing tests for 9 of 10 `abraxas/runtime/` modules:
     - `policy_snapshot.py`, `pipeline_bindings.py`, `artifacts.py`, `retention.py`
     - `results_pack.py`, `deterministic_executor.py`, `device_fingerprint.py`
     - `concurrency.py`, `perf_ledger.py`
   - **Blocking**: Cannot rely on runtime infrastructure without tests

5. **Document Seal Validation**
   - Create `docs/seal/SEAL_VALIDATION_GUIDE.md`
   - Document seal release process end-to-end
   - Explain artifact schemas and validation flow
   - **Blocking**: No operational guide for production releases

### P1 - Feature Completeness (In Progress)
1. **Migrate ABX-Runes Coupling Violations** (81 violations, ~10% migrated)
   - **Progress**: `abx/mwr.py` ✅ PARTIALLY FIXED, `abx/forecast_log.py` ✅ PARTIALLY FIXED
   - **Progress**: `abx/kernel.py` ✅ VERIFIED CORRECT
   - **Not Fixed**: `abx/forecast_score.py`, `abx/a2_phase.py`, `abx/term_claims_run.py`
   - **Not Fixed**: `abx/dap.py`, `abx/epp.py`, `abx/osh.py`
   - **Needs Audit**: `abx/server/app.py`, `abx/cli.py`, `abx/operators/alive_*`
   - **Top Offenders**:
     - forecast (23 violations) - brier_score, horizon_bucket, decide_gate
     - evolve (18 violations) - append_chained_jsonl, enforce_non_truncation
     - memetic (16 violations) - cluster_claims, compute_dmx, build_mimetic_weather
   - **Goal**: 10-15 violations per 2-week sprint, 50%+ complete in 2-3 months
   - See `docs/migration/coupling_violations_inventory.md` for full list

2. **Implement Critical Rune Operators** (6 stubs: WSSS, RFA, SDS, IPL, ADD, TAM)
   - **Priority**: SDS (ϟ₂), IPL (ϟ₄), ADD (ϟ₅) - needed for oracle pipeline
   - **Issue**: All raise `NotImplementedError` in `strict_execution=True` mode
   - **Action**: Replace stubs with real logic, add golden tests
   - Location: `abraxas/runes/operators/*.py`

3. **Complete Oracle Daily Run Integration** (`abraxas/cli/oracle_daily_run.py`)
   - TODO line 64: Integrate with real data sources (RSS, APIs, Decodo)
   - TODO line 214: Load DCE (Domain Compression Engine) from configuration
   - **Blocking**: Oracle cannot run in production without data integration

4. **Complete Scenario Envelope Runner** (`abraxas/cli/scenario_run.py`)
   - TODO lines 125-127: Load weather, D/M snapshot, almanac snapshot
   - **Missing**: Critical context for scenario testing

5. **Add Shadow Detectors Integration Example**
   - Create `examples/shadow_detectors_integration.py`
   - Show how to invoke `compute_all_detectors()`
   - Document integration patterns with Shadow Structural Metrics

6. **Create Rune Operator Development Guide**
   - Document how to convert auto-generated stubs to real implementations
   - Explain provenance requirements and golden test patterns
   - Add to `docs/runes/OPERATOR_DEVELOPMENT_GUIDE.md`

### P2 - Technical Debt
- Complete ALIVE system (PDF/CSV export, Slack integration, DB persistence)
- Complete ABX core pipeline (remove stub oracle generation)
- Review and fix 50+ placeholder comments
- Add OpenAPI spec for TypeScript server endpoints
- Enable and track TypeScript test coverage metrics

### Branch Conflicts (Lower Priority - Handled in Other Branches)
- **P0 (2026-01-10)**: Resolve pending merge conflicts in 3 active development branches
  - Priority 1: claude/resolve-merge-conflicts-Vg6qy (acceptance tests + dashboard)
  - Priority 2: cursor/mda-signal-layer-v2-2c0d (MDA package)
  - Priority 3: cursor/oracle-bridge-mda-canary-87a3 (MDA engine + Oracle bridge)
  - **Note**: Being handled in separate branches, not blocking current work

## Pending Branch Conflicts (2026-01-10)

**Analysis Date:** 2026-01-10
**Main Branch:** 8672ab0 (AALmanac integration PR #95)

### Quick Reference - Branch URLs & Checkout Commands

```bash
# Priority 1: Acceptance Test Suite + Dashboard (8 conflicts)
git fetch origin claude/resolve-merge-conflicts-Vg6qy
git checkout -b codex/resolve-vg6qy-<session-id> origin/claude/resolve-merge-conflicts-Vg6qy
# URL: https://github.com/scrimshawlife-ctrl/Abraxas/tree/claude/resolve-merge-conflicts-Vg6qy

# Priority 2: MDA Signal Layer (3 conflicts)
git fetch origin cursor/mda-signal-layer-v2-2c0d
git checkout -b codex/resolve-mda-signal-<session-id> origin/cursor/mda-signal-layer-v2-2c0d
# URL: https://github.com/scrimshawlife-ctrl/Abraxas/tree/cursor/mda-signal-layer-v2-2c0d

# Priority 3: Oracle Bridge + MDA Engine (9+ conflicts)
git fetch origin cursor/oracle-bridge-mda-canary-87a3
git checkout -b codex/resolve-oracle-mda-<session-id> origin/cursor/oracle-bridge-mda-canary-87a3
# URL: https://github.com/scrimshawlife-ctrl/Abraxas/tree/cursor/oracle-bridge-mda-canary-87a3
```

---

### Priority 1: claude/resolve-merge-conflicts-Vg6qy
**Status:** 7 commits ahead, 122 commits behind main
**Severity:** HIGH - 8 file conflicts
**Branch URL:** https://github.com/scrimshawlife-ctrl/Abraxas/tree/claude/resolve-merge-conflicts-Vg6qy

**Key Features:**
- Abraxas Acceptance Test Suite v1.0
- Dashboard Lens artifact viewer (merged PRs #58, #57, #55, #54)
- Resonance narratives renderer

**Conflicting Files:**
1. `.gitignore`
2. `abraxas/overlay/__init__.py`
3. `abraxas/overlay/phases.py`
4. `abraxas/overlay/run.py`
5. `abraxas/overlay/schema.py`
6. `client/src/components/DashboardLens.tsx` (add/add conflict)
7. `client/src/components/app-sidebar.tsx`
8. `tools/acceptance/run_acceptance_suite.py` (add/add conflict)

**Recommendation:** Resolve first - contains valuable acceptance testing infrastructure and dashboard features.

---

### Priority 2: cursor/mda-signal-layer-v2-2c0d
**Status:** 1 commit ahead, 108 commits behind main
**Severity:** MEDIUM - 3 file conflicts (all add/add)
**Branch URL:** https://github.com/scrimshawlife-ctrl/Abraxas/tree/cursor/mda-signal-layer-v2-2c0d

**Key Features:**
- New `abraxas.mda` package for MDA (Multi-Dimensional Analysis)

**Conflicting Files:**
1. `abraxas/mda/__init__.py` (add/add)
2. `abraxas/mda/cli.py` (add/add)
3. `abraxas/mda/signal_layer_v2.py` (add/add)

**Recommendation:** Coordinate with Priority 3 - both branches add MDA infrastructure.

---

### Priority 3: cursor/oracle-bridge-mda-canary-87a3
**Status:** 1 commit ahead, 108 commits behind main
**Severity:** HIGH - 9+ file conflicts
**Branch URL:** https://github.com/scrimshawlife-ctrl/Abraxas/tree/cursor/oracle-bridge-mda-canary-87a3

**Key Features:**
- MDA engine and Oracle bridge implementation
- Extends shadow detectors and symbolic compression

**Conflicting Files:**
1. `abraxas/detectors/shadow/registry.py`
2. `abraxas/detectors/shadow/types.py`
3. `abraxas/mda/__init__.py` (add/add - conflicts with Priority 2)
4. `abraxas/mda/cli.py` (add/add - conflicts with Priority 2)
5. `abraxas/mda/run.py` (add/add)
6. `abraxas/mda/signal_layer_v2.py` (add/add - conflicts with Priority 2)
7. `abraxas/operators/symbolic_compression.py`
8. `abraxas/oracle/mda_bridge.py` (add/add)
9. `pydantic/__init__.py`

**Recommendation:** Merge after Priority 2, or merge both MDA branches together to avoid duplicate work.

---

### Stale Branches (Recommend Cleanup)

These branches have NO unique commits and are significantly behind main:
- `claude/merge-pull-requests-xCwWp` (0 ahead, 327 behind)
- `claude/resolve-merge-conflicts-a9OJO` (0 ahead, 157 behind)
- `claude/resolve-merge-conflicts-au7CD` (0 ahead, 0 behind - current, can be deleted)
- `codex/refactor-code-for-improvements` (0 ahead, 306 behind)
- `codex/add-bell-constraint-canon-entry-and-abx-rune` (0 ahead, 290 behind)
- `cursor/pull-request-conflict-resolution-5149` (0 ahead, 120 behind)

**Action:** Delete these branches after verifying no valuable work was lost.

---

### Resolution Strategy

**Option A: Sequential (Safest)**
1. Resolve `claude/resolve-merge-conflicts-Vg6qy` first (acceptance tests + dashboard)
2. Merge both MDA branches (`cursor/mda-signal-layer-v2-2c0d` + `cursor/oracle-bridge-mda-canary-87a3`) together
3. Clean up stale branches

**Option B: Parallel (Faster)**
1. Assign Vg6qy to one agent/session
2. Assign combined MDA work to another agent/session
3. Merge both PRs when complete

**Option C: Audit First**
1. Review all conflicting changes in detail
2. Determine if features duplicate existing main branch work
3. Cherry-pick valuable commits instead of full merge

---

### Next Steps for Codex

**Immediate Actions Required:**

1. **Choose Resolution Strategy** - Select Option A, B, or C based on:
   - Available time/resources (parallel vs sequential)
   - Risk tolerance (audit first vs merge and test)
   - Feature priority (acceptance tests vs MDA infrastructure)

2. **Create Working Branch** - For each conflict resolution:
   ```bash
   # Create new branch with proper session ID format
   git checkout -b codex/<descriptive-name>-<session-id>
   git fetch origin
   git merge origin/<source-branch> origin/main
   # Resolve conflicts...
   ```

3. **Conflict Resolution Checklist** - For each branch:
   - [ ] Checkout target branch and merge main
   - [ ] Resolve conflicts following `CONFLICT_RESOLUTION_GUIDE.md`
   - [ ] Verify determinism (same inputs → same outputs)
   - [ ] Run all tests: `pytest tests/` and `npm test`
   - [ ] Check provenance integrity (SHA-256 hashes preserved)
   - [ ] Verify ABX-Runes coupling rules (no direct imports)
   - [ ] Update CLAUDE.md TODO section when complete
   - [ ] Create PR with conflict resolution summary
   - [ ] Push and verify CI passes

4. **Stale Branch Cleanup** - After verifying no valuable work lost:
   ```bash
   # Delete stale branches (backup first if uncertain)
   git push origin --delete claude/merge-pull-requests-xCwWp
   git push origin --delete claude/resolve-merge-conflicts-a9OJO
   git push origin --delete claude/resolve-merge-conflicts-au7CD
   git push origin --delete codex/refactor-code-for-improvements
   git push origin --delete codex/add-bell-constraint-canon-entry-and-abx-rune
   git push origin --delete cursor/pull-request-conflict-resolution-5149
   ```

5. **Documentation Updates** - After all resolutions:
   - Update this section in CLAUDE.md with completion status
   - Remove "P0 (NEW - 2026-01-10)" from TODO when done
   - Add any new architectural patterns to relevant sections

**Critical Reminders:**
- ✅ Preserve determinism in all conflict resolutions
- ✅ Include provenance metadata (SHA-256 hashes)
- ✅ Follow ABX-Runes coupling rules (capability contracts only)
- ✅ Run full test suite before creating PRs
- ✅ Use descriptive commit messages with conflict resolution context

---

## Known Stubs and Incomplete Features

**Last Audited:** 2026-01-11
**Total Items:** 150+ (15 P0, 45 P1, 90+ P2)
**Test Coverage:** ~33% by file count (227 test files, 693 abraxas/ Python files)

This section catalogs known incomplete implementations, TODOs, and stubs in the codebase. Items are prioritized by impact on production readiness.

### P0 - Critical Production Blockers

#### 1. Acceptance Test Suite Stubs
**Location:** `tools/acceptance/run_acceptance_suite.py`
**Issue:** 7 TODOs preventing real oracle integration
**Lines:** 128, 184, 240, 297, 353, 404, 438

```python
# TODO: Call actual oracle pipeline here
# TODO: Load schemas and validate artifacts
# TODO: Run oracle with removed evidence source
# TODO: Run oracle with shadow detectors on/off
# TODO: Load narrative bundle and validate all pointers
# TODO: Replace with actual oracle pipeline call
# TODO: Implement actual drift classification logic
```

**Impact:** Cannot verify production readiness without real oracle calls.
**Action Required:** Wire up `abraxas.oracle.v2.pipeline.run_oracle()` via capability contract.

---

#### 2. Placeholder Test Files (False Coverage)
**Files:**
- `tests/test_scenario_router.py` - 2 tests with `assert True`
- `tests/test_integrity_hash_chain.py` - 2 tests with `assert True`
- `tests/test_integrity_brief.py` - 2 tests with `assert True`

```python
def test_routing_logic():
    """Test scenario routing logic."""
    # Placeholder test - implement when scenario router is complete
    assert True, "Placeholder test for rent enforcement"
```

**Impact:** False positive test coverage - tests pass without verifying functionality.
**Action Required:** Implement real tests or delete files.

---

#### 3. Ed25519 Signing Backend (Optional P0)
**Location:** `shared/signing.py:90-109`
**Issue:** Digital signature backend not implemented

```python
def sign_ed25519(message: str, private_key_b64: str) -> str:
    """Placeholder for Ed25519 backend (future)."""
    raise NotImplementedError("Ed25519 backend not enabled. Use SHA-256 for now.")
```

**Impact:** No cryptographic signatures - system relies on SHA-256 hashes only.
**Action Required:** Implement Ed25519 backend if digital signatures needed, otherwise downgrade to P2.

---

#### 4. Missing Test Coverage - Runtime Infrastructure
**Missing Tests for 9 of 10 modules in `abraxas/runtime/`:**
- `policy_snapshot.py` - Policy snapshot creation and hash chaining
- `pipeline_bindings.py` - Pipeline binding resolution
- `artifacts.py` - Artifact management
- `retention.py` - Artifact retention and pruning
- `results_pack.py` - Results pack utilities
- `deterministic_executor.py` - Deterministic execution
- `device_fingerprint.py` - Device fingerprinting
- `concurrency.py` - Concurrency control
- `perf_ledger.py` - Performance ledger

**Existing Tests:** Only `test_runtime_dozen_run_gate.py` and `test_runtime_tick.py`

**Impact:** Cannot rely on runtime infrastructure without test validation.
**Action Required:** Add comprehensive tests for each module.

---

#### 5. No Seal Release Documentation
**Missing:** `docs/seal/SEAL_VALIDATION_GUIDE.md`
**Gap:** No operational guide for production seal process

**Impact:** No documented workflow for seal validation, artifact verification, or production releases.
**Action Required:** Document end-to-end seal process, artifact schemas, validation tooling.

---

### P1 - High Priority (Feature Completeness)

#### 6. Auto-Generated Rune Operator Stubs
**Count:** 6 operators
**Location:** `abraxas/runes/operators/`

**Stub Operators:**
- `wsss.py` - ϟ₃ WSSS (Weak Signal · Strong Structure)
- `rfa.py` - ϟ₁ RFA
- `sds.py` - ϟ₂ SDS ⚠️ **CRITICAL for oracle pipeline**
- `ipl.py` - ϟ₄ IPL ⚠️ **CRITICAL for oracle pipeline**
- `add.py` - ϟ₅ ADD ⚠️ **CRITICAL for oracle pipeline**
- `tam.py` - TAM

**Pattern:**
```python
def apply_wsss(signal_amplitude, structural_coherence, pattern_matrix, *, strict_execution=False):
    if strict_execution:
        raise NotImplementedError(f"Operator WSSS not implemented yet.")

    # Stub implementation - returns empty outputs
    return {"structure_score": None, "signal_quality": None, "validation_result": None}
```

**Impact:** Runes fail in `strict_execution=True` mode. Placeholder outputs (all None) may cause downstream issues.
**Action Required:** Implement SDS, IPL, ADD first (needed for oracle), then WSSS, RFA, TAM.

---

#### 7. ABX-Runes Coupling Violations
**Count:** 81 violations across 34 files
**Progress:** ~10% migrated (8 files partially/fully fixed)
**Documentation:** `docs/migration/coupling_violations_inventory.md`

**Top Offenders:**
- **forecast** (23 violations) - `brier_score`, `horizon_bucket`, `decide_gate`
- **evolve** (18 violations) - `append_chained_jsonl`, `enforce_non_truncation`
- **memetic** (16 violations) - `cluster_claims`, `compute_dmx`, `build_mimetic_weather`
- **conspiracy** (4 violations) - `compute_claim_csp`

**Files Needing Immediate Attention:**
```
✅ PARTIALLY FIXED: abx/mwr.py, abx/forecast_log.py
✅ VERIFIED CORRECT: abx/kernel.py
❌ NOT FIXED: abx/forecast_score.py, abx/a2_phase.py, abx/term_claims_run.py
❌ NOT FIXED: abx/dap.py, abx/epp.py, abx/osh.py
⚠️ NEEDS AUDIT: abx/server/app.py, abx/cli.py, abx/operators/alive_*
```

**Impact:** Violates ABX-Runes coupling architecture. Direct imports bypass capability contracts.
**Action Required:** Migrate 10-15 violations per sprint. Create capability contracts for top offenders.

---

#### 8. Oracle Daily Run TODOs
**Location:** `abraxas/cli/oracle_daily_run.py`
**Lines:** 64, 214

```python
# TODO: Integrate with actual data sources (RSS, APIs, Decodo, etc.)
# TODO: Load DCE from configuration
```

**Impact:** Oracle cannot run in production without real data source integration.
**Action Required:** Wire up Decodo API, RSS feeds, load DCE from config.

---

#### 9. Scenario Envelope Runner TODOs
**Location:** `abraxas/cli/scenario_run.py`
**Lines:** 125-127

```python
"weather": None,  # TODO: Load from weather engine if available
"dm_snapshot": None,  # TODO: Load from D/M metrics if available
"almanac_snapshot": None,  # TODO: Load from almanac if available
```

**Impact:** Scenario runs missing critical context (weather, D/M, almanac).
**Action Required:** Load snapshots from respective modules.

---

### P2 - Medium Priority (Technical Debt)

#### 10. TypeScript Server TODOs
**Location:** `server/alive/`

```typescript
// Step 3: Persist raw results (TODO: add DB storage)
// TODO: Consider using a persistent Python worker or HTTP bridge
// TODO: Implement proper error handling
// TODO: Implement actual user tier lookup from database
```

**Impact:** ALIVE system lacks DB persistence and proper error handling.

---

#### 11. ABX Core Pipeline Stub
**Location:** `abx/core/pipeline.py:92-93`

```python
# Generate oracle output (stub - replace with real implementation)
# TODO: Wire real oracle generation logic here
```

**Impact:** ABX core pipeline generates stub oracle outputs.

---

#### 12. ALIVE Operator Stubs
**Location:** `abx/operators/alive_*.py`

```python
# TODO: Implement PDF export
raise NotImplementedError("PDF export not yet implemented")

# TODO: Implement CSV export with proper formatting
# TODO: Actually send to Slack webhook
```

**Impact:** ALIVE export and Slack integration are stubs.

---

#### 13. Placeholder Comments (~50 occurrences)
**Examples:**
```python
# Fallback: Placeholder compression when DCE not available
# Placeholder: In production, compare cross-domain signal patterns
# Falls back to safe placeholders when keys missing
# Placeholder - in production, compute from ledgers
avg_compression_ratio = 2.5  # Placeholder
```

**Impact:** Low - most are fallback behaviors or safe defaults.
**Action Required:** Review each and decide if real implementation needed.

---

### Missing Documentation

**P0:**
- `docs/seal/SEAL_VALIDATION_GUIDE.md` - Seal validation end-to-end guide

**P1:**
- `examples/shadow_detectors_integration.py` - Shadow detector usage example
- `docs/runes/OPERATOR_DEVELOPMENT_GUIDE.md` - Rune operator development guide

**P2:**
- `docs/api/openapi.yaml` - OpenAPI spec for TypeScript server

---

### Test Coverage Summary

**Python Tests:**
- Total test files: 227
- Total Python files in abraxas/: 693
- Coverage ratio: ~33% by file count

**TypeScript Tests:**
- No coverage metrics tracked
- Action: Enable `npm run test:coverage`

**Missing Critical Tests:**
- Seal release scripts (seal_release.py, validate_artifacts.py)
- Runtime infrastructure (9 of 10 modules)
- ERS integration (scheduler, bindings, trace)
- Rune operators (6 stubs need tests)

---

### v2.2.0 Feature Verification Status

✅ **Shadow Detectors v0.1:** COMPLETE
- All 13 detector files implemented
- 4 comprehensive test files (determinism, bounds, missing inputs)
- Documentation: `docs/detectors/shadow_detectors_v0_1.md`

✅ **ABX-Runes Coupling Infrastructure:** PRESENT (but violations remain)
- All capability contract files exist
- Migration guide complete
- 81 coupling violations documented, 10% migrated

⚠️ **Seal Validation Infrastructure:** PRESENT (but undertested)
- Scripts exist: `seal_release.py`, `validate_artifacts.py`
- Schemas exist: 9 JSON schemas
- Missing: Tests and documentation

⚠️ **Runtime Infrastructure:** PRESENT (but undertested)
- All 19 files in abraxas/runtime/ exist
- Only 2 test files
- Missing: Comprehensive test coverage

⚠️ **ERS (Event Runtime System):** PRESENT (reasonably tested)
- All 6 files in abraxas/ers/ exist
- 4 test files exist
- Missing: Some module tests

---

**For detailed audit report, see task output from 2026-01-11 audit agent (ID: a2878b2).**

---

## RuneInvocationContext (Oracle Pipeline)

Oracle pipeline rune calls require a validated `RuneInvocationContext` with:

- `run_id`: stable ID for the session/run (string)
- `subsystem_id`: caller identifier (string, use `abx.core.pipeline` for `run_oracle`)
- `git_hash`: repo revision identifier (string)

Example:

```python
from abraxas.runes.ctx import RuneInvocationContext

ctx = RuneInvocationContext(
    run_id="ORACLE_RUN",
    subsystem_id="abx.core.pipeline",
    git_hash="unknown",
)
```

## Recommendations

- Standardize rune invocation context construction by centralizing defaults in a helper
  (e.g., `abx.oracle.context.build_rune_ctx`) to prevent drift across pipelines.
- Expand oracle pipeline tests to cover strict execution behavior (stub blocking and error
  propagation) in addition to provenance checks.
- Audit ABX-Runes capability IDs to ensure naming consistency (`rune:*` vs domain-specific
  namespaces) and update migration docs accordingly.

---

## Previous Updates (v1.4.1 - 2025-12-29)

Merged 4 major PRs consolidating governance, acquisition, and infrastructure:

1. **PR #20** - Python cache patterns + kernel phase system
2. **PR #22** - Anti-hallucination metric governance system (6-gate promotion)
3. **PR #28** - WO-100: Acquisition & analysis infrastructure
4. **PR #36** - Documentation enhancements

**Total Changes**: 120 files changed, 15,654 additions, 466 deletions

---

## Table of Contents

1. [Repository Overview](#repository-overview)
2. [Architecture & Structure](#architecture--structure)
3. [Development Workflows](#development-workflows)
4. [Key Conventions & Principles](#key-conventions--principles)
5. [Module Organization](#module-organization)
6. [Testing Patterns](#testing-patterns)
7. [Common Development Tasks](#common-development-tasks)
8. [Git Workflow](#git-workflow)
9. [Integration Points](#integration-points)
10. [Important Files & Directories](#important-files--directories)

---

## Repository Overview

### What is Abraxas?

**Abraxas** is a production-grade symbolic intelligence system that:
- Detects linguistic compression patterns (SCO/ECO)
- Tracks memetic drift and lifecycle dynamics
- Operates as an always-on edge appliance with self-healing capabilities
- Generates deterministic provenance for every linguistic event
- Provides "weather forecasts" for language and symbolic patterns

Think of it as a **weather system for language** — detecting when symbols compress, tracking affective drift, and generating deterministic provenance.

### Core Technology Stack

- **Python 3.11+**: Core linguistic analysis, operators, pipelines
- **TypeScript 5.6+**: API server, orchestration, UI components
- **Node.js 18+**: Express server, Weather Engine, integrations
- **SQLite/PostgreSQL**: Data persistence
- **React 18**: UI components (client/)
- **Drizzle ORM**: Database management
- **Vite**: Build tooling
- **Pytest**: Python testing
- **Vitest**: TypeScript testing

### Project Philosophy

Abraxas follows strict **deterministic, provenance-first design principles**:

1. **Determinism**: Same inputs always produce same outputs
2. **Provenance**: Every artifact includes SHA-256 hash for reproducibility
3. **Write-Once, Annotate-Only**: Canonical state is immutable
4. **Anti-Hallucination**: Metrics are contracts, not ideas
5. **Rent-Payment**: Complexity must justify its existence
6. **Edge-Ready**: Optimized for NVIDIA Jetson Orin deployment

---

## Architecture & Structure

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ABRAXAS ECOSYSTEM v4.2.0                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  TypeScript/Express Layer (Node.js)                      │  │
│  │  • API Routes & Express Server                           │  │
│  │  • Weather Engine Integration                            │  │
│  │  • Chat UI & Admin Handshake                             │  │
│  │  • Task Registry & ERS Scheduling                        │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   │                                             │
│  ┌────────────────▼─────────────────────────────────────────┐  │
│  │  Python SCO/ECO Core                                     │  │
│  │  • Symbolic Compression Operator                         │  │
│  │  • Phonetic & Semantic Analysis                          │  │
│  │  • Transparency Index (STI) Calculation                  │  │
│  │  • Replacement Direction Vector (RDV)                    │  │
│  │  • Temporal Tau Operator (τ)                             │  │
│  │  • D/M Layer (Information Integrity)                     │  │
│  │  • SOD (Second-Order Dynamics)                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Orin Boot Spine (Edge Infrastructure)                   │  │
│  │  • Drift Detection & Health Monitoring                   │  │
│  │  • Overlay Lifecycle Management                          │  │
│  │  • Atomic Updates with Rollback                          │  │
│  │  • Systemd Integration                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Data Layer                                              │  │
│  │  • Decodo Web Scraping API Integration                  │  │
│  │  • SQLite/PostgreSQL Storage                             │  │
│  │  • JSONL Event Persistence                               │  │
│  │  • AAlmanac Ledger (Write-Once)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
Abraxas/
├── abraxas/                    # Python core modules
│   ├── core/                   # Core utilities (provenance, metrics, tau)
│   ├── operators/              # Symbolic operators (SCO, etc.)
│   ├── linguistic/             # Linguistic analysis utilities
│   ├── pipelines/              # Processing pipelines
│   ├── cli/                    # CLI entry points
│   │   └── sim_map.py          # Simulation mapping CLI
│   ├── lexicon/                # Lexicon engine v1
│   ├── oracle/                 # Oracle pipeline v1
│   ├── slang/                  # Slang analysis & AAlmanac
│   ├── integrity/              # D/M layer (information integrity)
│   ├── sod/                    # Second-Order Dynamics
│   │   └── sim_adapter.py      # Simulation adapter for SOD
│   ├── weather/                # Weather engine (Python)
│   ├── kernel/                 # Execution kernel (5-phase ASCEND)
│   │   ├── __init__.py         # Exports run_phase, Phase, execute_ascend
│   │   ├── entry.py            # Phase router (OPEN/ALIGN/ASCEND/CLEAR/SEAL)
│   │   └── ascend_ops.py       # Whitelisted ASCEND operations
│   ├── shadow_metrics/         # Shadow Structural Metrics (observe-only analytical layer)
│   │   ├── __init__.py         # Access control and version
│   │   ├── core.py             # Core types and utilities
│   │   ├── sei.py              # Sentiment Entropy Index
│   │   ├── clip.py             # Cognitive Load Intensity Proxy
│   │   ├── nor.py              # Narrative Overload Rating
│   │   ├── pts.py              # Persuasive Trajectory Score
│   │   ├── scg.py              # Social Contagion Gradient
│   │   ├── fvc.py              # Filter Velocity Coefficient
│   │   └── patch_registry.py   # Incremental patch tracking
│   ├── detectors/              # Pattern detectors
│   │   └── shadow/             # Shadow detectors (feed evidence to shadow_metrics)
│   │       ├── __init__.py     # Package exports
│   │       ├── types.py        # Base detector types
│   │       ├── registry.py     # Detector registry
│   │       ├── registry_impl.py # Enhanced registry implementation
│   │       ├── compliance_remix.py       # Compliance vs Remix detector
│   │       ├── meta_awareness.py         # Meta-Awareness detector
│   │       ├── negative_space.py         # Negative Space / Silence detector
│   │       ├── anagram.py      # Anagram pattern detector
│   │       ├── token_density.py # Token density analyzer
│   │       ├── normalize.py    # Text normalization utilities
│   │       └── util.py         # Shared utilities
│   ├── overlay/                # Overlay management
│   ├── drift/                  # Drift detection
│   ├── storage/                # Data persistence
│   ├── decodo/                 # Decodo API integration
│   ├── backtest/               # Backtesting system
│   ├── learning/               # Active learning loops
│   ├── evolution/              # Metric evolution
│   ├── metrics/                # Metric governance (6-gate promotion)
│   │   ├── governance.py       # Candidate metrics & promotion system
│   │   ├── evaluate.py         # MetricEvaluator with 6 gates
│   │   ├── registry_io.py      # CandidateRegistry & PromotionLedger
│   │   ├── hashutil.py         # Provenance hash utilities
│   │   └── cli.py              # Metric governance CLI
│   ├── simulation/             # Simulation mapping layer
│   │   ├── add_metric.py       # Metric candidate creation from papers
│   │   ├── registries/         # Metric, outcome, rune, simvar registries
│   │   ├── schemas/            # JSON schemas for validation
│   │   ├── validation.py       # Schema validation utilities
│   │   └── examples/           # Exemplar implementations
│   ├── sim_mappings/           # Academic paper → Abraxas variable mappings
│   │   ├── mapper.py           # Core mapping engine
│   │   ├── family_maps.py      # Family-specific mappings (ABM, diffusion, etc.)
│   │   ├── normalizers.py      # Variable name normalization
│   │   ├── importers.py        # CSV/JSON import utilities
│   │   └── registry.py         # Paper registry management
│   ├── scoreboard/             # Scoreboard system
│   ├── forecast/               # Forecasting
│   ├── scenario/               # Scenario envelope runner
│   ├── evidence/               # Evidence management
│   ├── governance/             # Governance policies
│   ├── policy/                 # Policy enforcement
│   ├── economics/              # Economics models
│   ├── conspiracy/             # Conspiracy detection
│   ├── disinfo/                # Disinformation analysis
│   │
│   ├── runtime/                # Runtime infrastructure (NEW v2.2.0)
│   │   ├── __init__.py         # Package exports
│   │   ├── policy_snapshot.py  # Immutable policy snapshots for provenance
│   │   ├── policy_ref.py       # Policy reference management
│   │   ├── invariance_gate.py  # DozenRunGate for stability validation
│   │   ├── pipeline_bindings.py # Native pipeline binding resolution
│   │   ├── artifacts.py        # Artifact management utilities
│   │   ├── retention.py        # Artifact retention & pruning
│   │   ├── results_pack.py     # Results pack utilities
│   │   ├── deterministic_executor.py # Deterministic execution
│   │   ├── device_fingerprint.py # Device fingerprinting
│   │   ├── concurrency.py      # Concurrency utilities
│   │   └── perf_ledger.py      # Performance ledger
│   │
│   ├── ers/                    # Event Runtime System (NEW v2.2.0)
│   │   ├── __init__.py         # Package exports
│   │   ├── scheduler.py        # Event scheduling
│   │   ├── bindings.py         # Event bindings
│   │   ├── invariance.py       # Invariance tracking
│   │   ├── trace.py            # Trace management
│   │   └── types.py            # Type definitions
│   │
│   ├── runes/                  # ABX-Runes capability contracts (NEW v2.2.0)
│   │   ├── capabilities.py     # Capability registry & invocation
│   │   ├── invoke.py           # Capability invocation utilities
│   │   ├── ctx.py              # RuneInvocationContext
│   │   └── registry.json       # Capability registry
│   │
│   ├── oracle/                 # Oracle pipeline
│   │   ├── registry.py         # Oracle capability registry
│   │   └── v2/
│   │       └── rune_adapter.py # Oracle v2 rune adapter
│   │
│   └── ...                     # Additional modules
│
├── abx/                        # ABX runtime & utilities
│   ├── cli.py                  # Main ABX CLI entry point
│   ├── core/                   # Core ABX utilities
│   ├── runtime/                # Runtime management
│   ├── server/                 # ABX server components
│   ├── ingest/                 # Data ingestion
│   ├── ui/                     # UI components
│   ├── assets/                 # Asset management
│   ├── overlays/               # Overlay modules
│   ├── operators/              # ABX operators
│   ├── bus/                    # Event bus
│   ├── store/                  # Storage utilities
│   ├── util/                   # Utility functions
│   ├── codex/                  # Codex integration
│   │
│   ├── # WO-100: Acquisition & Analysis Modules
│   ├── acquisition_execute.py  # Task executor with ROI calculation
│   ├── task_ledger.py          # Task lifecycle event tracking
│   ├── anchor_url_resolver.py  # Anchor → URL resolution
│   ├── reupload_storm_detector.py # Reupload pattern detection
│   ├── media_origin_verify.py  # Media fingerprint verification
│   ├── manipulation_metrics.py # Manipulation front detection
│   ├── manipulation_fronts_to_tasks.py # Front → task generation
│   │
│   ├── # Forecast & Oracle Modules
│   ├── oracle_ingest.py        # Oracle result ingestion
│   ├── forecast_accuracy.py    # Forecast accuracy tracking
│   ├── forecast_ledger.py      # Forecast storage & retrieval
│   ├── forecast_review_state.py # Review state management
│   ├── horizon.py              # Horizon band definitions
│   ├── review_scheduler.py     # Review scheduling system
│   │
│   ├── # AAlmanac & Slang Processing
│   ├── aalmanac.py             # AAlmanac ledger management
│   ├── aalmanac_enrich.py      # AAlmanac enrichment
│   ├── aalmanac_tau.py         # Temporal Tau processing
│   ├── slang_extract.py        # Slang candidate extraction
│   ├── slang_migration.py      # Slang lifecycle migration
│   │
│   ├── # Weather & Task Orchestration
│   ├── mimetic_weather.py      # Memetic weather calculation
│   ├── weather_to_tasks.py     # Weather → task generation
│   ├── cycle_runner.py         # Cycle execution runner
│   ├── task_union.py           # Task union operations
│   ├── task_union_ledger.py    # Union ledger tracking
│   ├── task_roi_report.py      # Task ROI reporting
│   │
│   ├── # Binding & Pollution Analysis
│   ├── term_claim_binder.py    # Term ↔ claim binding
│   ├── truth_pollution.py      # Truth pollution metrics
│   │
│   └── providers/              # External provider adapters
│       └── fetch_adapter.py    # HTTP fetch adapter
│
├── server/                     # TypeScript Express server
│   ├── index.ts                # Server entry point
│   ├── routes.ts               # Main route definitions
│   ├── abraxas.ts              # Abraxas integration
│   ├── abraxas-server.ts       # Abraxas routes setup
│   ├── storage.ts              # Storage abstraction
│   ├── replitAuth.ts           # Replit authentication
│   ├── abraxas/                # Abraxas server modules
│   │   ├── integrations/       # Python bridge, external APIs
│   │   ├── pipelines/          # TS pipelines
│   │   ├── routes/             # Module-specific routes
│   │   ├── weather/            # Weather engine modules
│   │   └── tests/              # Server tests
│   ├── alive/                  # ALIVE system routes
│   └── integrations/           # External integrations
│
├── client/                     # React frontend
│   ├── src/                    # React source code
│   │   ├── components/         # React components
│   │   ├── hooks/              # Custom hooks
│   │   ├── lib/                # Client utilities
│   │   └── pages/              # Page components
│   └── public/                 # Static assets
│
├── shared/                     # Shared TypeScript code
│   └── schema.ts               # Drizzle schema definitions
│
├── tests/                      # Python tests
│   ├── fixtures/               # Test fixtures
│   ├── golden/                 # Golden test data
│   ├── helpers/                # Test helpers
│   └── test_*.py               # Test files
│
├── data/                       # Data storage
│   ├── acquire/                # Acquisition data
│   ├── backtests/              # Backtest results
│   ├── evolution/              # Evolution ledgers
│   ├── forecast/               # Forecast data
│   ├── rent_manifests/         # Rent manifests
│   ├── run_plans/              # Run plans
│   ├── vector_maps/            # Vector maps
│   └── sim_sources/            # Simulation sources & paper data
│       ├── papers.json         # Academic paper metadata
│       ├── paper_mapping_table.csv # Paper → variable mappings
│       └── examples/           # Example paper extracts (PMC, arXiv, etc.)
│
├── out/                        # Output artifacts
│   ├── reports/                # Generated reports
│   ├── evolution_ledgers/      # Evolution outputs
│   └── ledger/                 # Append-only JSONL ledgers
│       ├── aalmanac.jsonl      # AAlmanac entries
│       ├── aalmanac_events.jsonl # AAlmanac lifecycle events
│       ├── task_ledger.jsonl   # Task execution events
│       ├── task_outcomes.jsonl # Task outcome tracking
│       ├── oracle_runs.jsonl   # Oracle execution history
│       ├── forecast_outcomes.jsonl # Forecast accuracy results
│       ├── manipulation_metrics.jsonl # Manipulation front metrics
│       ├── media_origin_ledger.jsonl # Media verification results
│       ├── reupload_fronts.jsonl # Reupload detection results
│       ├── binder_ledger.jsonl # Term-claim bindings
│       ├── union_ledger.jsonl  # Task union operations
│       ├── scheduler_ledger.jsonl # Review scheduling events
│       └── slang_candidates.jsonl # Slang candidate tracking
│
├── docs/                       # Documentation
│   ├── canon/                  # Canonical documentation
│   │   └── ABRAXAS_CANON_LEDGER.txt
│   ├── specs/                  # Specification documents
│   │   ├── metric_governance.md # 6-gate metric promotion system
│   │   ├── simulation_architecture.md # Simulation layer architecture
│   │   ├── simulation_mapping_layer.md # Paper → variable mappings
│   │   ├── paper_triage_rules.md # Paper triage & classification
│   │   └── paper_mapping_table_template.csv # Mapping table template
│   └── plan/                   # Implementation plans
│       └── simulation_mapping_layer_plan.md # Mapping layer implementation
│
├── systemd/                    # Systemd service files
├── scripts/                    # Utility scripts
├── tools/                      # Development tools
├── examples/                   # Example code
├── registry/                   # Registry files
│   ├── metrics_candidate.json  # Metric candidate registry
│   └── examples/               # Example candidate metrics
│       └── candidate_MEDIA_COMPETITION_MISINFO_PRESSURE.json
│
├── schemas/                    # JSON schemas
│   └── metric_candidate.schema.json # Metric candidate validation schema
│
├── package.json                # Node.js dependencies
├── pyproject.toml              # Python project config
├── tsconfig.json               # TypeScript config
├── vite.config.ts              # Vite build config
├── vitest.config.ts            # Vitest test config
├── drizzle.config.ts           # Drizzle ORM config
├── tailwind.config.ts          # Tailwind CSS config
│
├── README.md                   # Main README
├── README_SCO.md               # SCO stack documentation
├── README_ORIN.md              # Orin spine documentation
├── INTEGRATION_SCO.md          # Integration guide
├── DEPLOYMENT_SCO.md           # Deployment guide
├── CONFLICT_RESOLUTION_GUIDE.md # Merge conflict guide
├── design_guidelines.md        # Design guidelines
├── CHANGELOG.md                # Changelog
└── CLAUDE.md                   # This file
```

---

## Development Workflows

### Initial Setup

```bash
# Clone repository
git clone https://github.com/scrimshawlife-ctrl/Abraxas.git
cd Abraxas

# Install Python dependencies
pip install -e .

# Install Node.js dependencies
npm install

# Run system diagnostic
abx doctor

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials
```

### Development Server

```bash
# Start TypeScript development server (hot reload)
npm run dev

# Start production server
npm run build
npm start

# Start Python CLI tools
python -m abraxas.cli.sco_run --help
abx --help
```

### Running Tests

```bash
# Python tests
pytest tests/                    # Run all tests
pytest tests/test_oracle_runner.py  # Run specific test
pytest -v                        # Verbose output
pytest --cov=abraxas            # With coverage

# TypeScript tests
npm test                         # Run all tests
npm run test:watch              # Watch mode
npm run test:ui                 # UI mode
npm run test:coverage           # With coverage

# Smoke test (deterministic)
abx smoke
```

### Type Checking

```bash
# TypeScript type checking
npm run check

# Python type hints (if using mypy)
mypy abraxas/
```

### Building for Production

```bash
# Build TypeScript
npm run build

# The build creates:
# - dist/index.js (server bundle)
# - client/dist/ (client bundle)
```

---

## Key Conventions & Principles

### 1. Determinism

**CRITICAL**: All operations must be deterministic. Same inputs → same outputs.

- Use stable sorting (e.g., `sorted()` with explicit key)
- No random operations without fixed seeds
- Timestamps should be ISO8601 with 'Z' timezone
- SHA-256 hashes for all provenance tracking

### 2. Provenance-First Design

Every artifact includes provenance metadata:

```python
from abraxas.core.provenance import Provenance, hash_canonical_json

# Example provenance creation
provenance = Provenance(
    run_id="RUN-001",
    started_at_utc=Provenance.now_iso_z(),
    inputs_hash=hash_canonical_json(inputs),
    config_hash=hash_canonical_json(config),
    git_sha="abc123",
    host="prod-01"
)
```

### 3. Write-Once, Annotate-Only

Canonical data (like AAlmanac) is **write-once, annotate-only**:

- Create entries once with immutable core fields
- Modifications happen via annotations (append-only)
- Never mutate existing canonical entries
- See `docs/canon/ABRAXAS_CANON_LEDGER.txt` for canonical patterns

### 4. Naming Conventions

#### Python

- **Files**: `snake_case.py` (e.g., `temporal_tau.py`, `symbolic_compression.py`)
- **Classes**: `PascalCase` (e.g., `TauCalculator`, `SymbolicCompressionEvent`)
- **Functions**: `snake_case` (e.g., `compute_snapshot`, `hash_canonical_json`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_THRESHOLD`, `MAX_ITERATIONS`)
- **Private**: `_leading_underscore` (e.g., `_internal_helper`)

#### TypeScript

- **Files**: `kebab-case.ts` (e.g., `sco-bridge.ts`, `weather-engine.ts`)
- **Classes/Types**: `PascalCase` (e.g., `WeatherModule`, `ProvenanceBundle`)
- **Functions**: `camelCase` (e.g., `analyzeSymbolPool`, `computeRisk`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `API_BASE_URL`, `DEFAULT_PORT`)
- **React Components**: `PascalCase` files and exports

#### Module Naming Patterns

- **Operators**: `<name>_operator.py` or just `<name>.py` in `operators/`
- **Pipelines**: `<name>_pipeline.py` in `pipelines/`
- **CLI tools**: `<name>_run.py` or `<name>.py` in `cli/`
- **Tests**: `test_<name>.py` in `tests/`

### 5. Data Structures

#### Pydantic Models (Python)

Prefer Pydantic for data validation:

```python
from pydantic import BaseModel, Field

class MyModel(BaseModel):
    name: str = Field(..., description="The name")
    value: float = Field(default=0.0, description="The value")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
```

#### Zod Schemas (TypeScript)

Use Zod for TypeScript validation:

```typescript
import { z } from 'zod';

const MySchema = z.object({
  name: z.string(),
  value: z.number().default(0.0),
});

type MyType = z.infer<typeof MySchema>;
```

### 6. Error Handling

#### Python

```python
# Use specific exceptions
class AbraxasError(Exception):
    """Base exception for Abraxas errors."""
    pass

class ValidationError(AbraxasError):
    """Raised when validation fails."""
    pass

# Raise with context
if not is_valid:
    raise ValidationError(f"Invalid input: {reason}")
```

#### TypeScript

```typescript
// Use Error subclasses
class AbraxasError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AbraxasError';
  }
}

// Or return Result types
type Result<T, E = Error> = { ok: true; value: T } | { ok: false; error: E };
```

### 7. Logging

#### Python

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Processing started")
logger.warning("Potential issue detected")
logger.error("Operation failed", exc_info=True)
```

#### TypeScript

```typescript
// Use console with structured logging
console.log('[INFO]', 'Processing started');
console.warn('[WARN]', 'Potential issue');
console.error('[ERROR]', 'Operation failed', error);
```

### 8. Configuration

- Environment variables in `.env` (never commit)
- Defaults in code or config files
- Use `os.getenv()` in Python, `process.env` in TypeScript
- Document all environment variables in `.env.example`

---

## Module Organization

### Python Core Modules

#### `abraxas/core/`

Core utilities used across the system:

- **`provenance.py`**: Provenance tracking, hashing utilities
- **`metrics.py`**: Metric calculation utilities
- **`temporal_tau.py`**: Temporal τ operator (τₕ, τᵥ, τₚ)
- **`canonical.py`**: Canonical data handling
- **`registry.py`**: Registry management
- **`scheduler.py`**: Task scheduling
- **`rendering.py`**: Output rendering utilities
- **`resonance_frame.py`**: Resonance frame calculations

#### `abraxas/operators/`

Symbolic operators:

- **`symbolic_compression.py`**: SCO/ECO operator
- Other operators as they're added

#### `abraxas/linguistic/`

Linguistic analysis utilities:

- **`phonetics.py`**: Soundex, phonetic keys
- **`similarity.py`**: Edit distance, IPS
- **`transparency.py`**: STI calculation
- **`rdv.py`**: Replacement Direction Vector (affect detection)
- **`tokenize.py`**: Token extraction, n-grams

#### `abraxas/cli/`

CLI entry points:

- **`sco_run.py`**: SCO analysis CLI
- **`abx_run_v1_4.py`**: v1.4 unified CLI
- **`scenario_run.py`**: Scenario envelope runner
- **`rent_check.py`**: Rent enforcement checker
- **`backtest.py`**: Backtesting CLI
- **`learning.py`**: Active learning CLI
- **`oasis_cli.py`**: OASIS pipeline CLI
- And many more...

#### `abraxas/lexicon/`

Lexicon engine v1:

- Domain-scoped, versioned token-weight mapping
- Deterministic compression with provenance
- See README.md for details

#### `abraxas/oracle/`

Oracle pipeline v1:

- Deterministic daily oracle generation
- Correlation delta processing
- Time-weighted decay

#### `abraxas/slang/`

Slang analysis & AAlmanac:

- **`a_almanac_store.py`**: Write-once ledger
- **`operators/`**: Slang-specific operators
- Lifecycle state machine

#### `abraxas/integrity/`

D/M layer (Disinformation/Misinformation):

- Information integrity metrics
- NOT truth adjudication—evidence-based risk scores
- Artifact integrity, narrative manipulation detection

#### `abraxas/sod/`

Second-Order Dynamics:

- **NCP**: Narrative Cascade Predictor
- **CNF**: Counter-Narrative Forecaster
- **EFTE**: Epistemic Fatigue Threshold Engine
- **SPM**: Susceptibility Profile Mapper
- **RRM**: Recovery & Re-Stabilization Model
- **`sim_adapter.py`**: Adapter for simulation variable integration

#### `abraxas/metrics/`

**Metric Governance System** - 6-gate anti-hallucination promotion framework:

- **`governance.py`**: Core governance types (CandidateMetric, CandidateStatus, EvidenceBundle, PromotionDecision)
- **`evaluate.py`**: MetricEvaluator implementing 6 promotion gates:
  1. **Provenance Gate**: SHA-256 hash chain verification
  2. **Falsifiability Gate**: Test specification & concrete failure modes
  3. **Non-Redundancy Gate**: Correlation analysis vs existing metrics
  4. **Rent-Payment Gate**: Complexity justification
  5. **Ablation Gate**: Removal impact validation
  6. **Stabilization Gate**: Temporal stability verification
- **`registry_io.py`**: CandidateRegistry, PromotionLedger, promotion workflow
- **`hashutil.py`**: Canonical JSON hashing, provenance chain verification
- **`cli.py`**: Command-line interface for metric governance operations

**Philosophy**: Metrics are Contracts, not Ideas. All emergent metrics must earn promotion through evidence.

#### `abraxas/simulation/`

**Simulation Mapping Layer** - Academic paper → Abraxas metric extraction:

- **`add_metric.py`**: Extract metric candidates from simulation papers
- **`registries/`**: Registry management for metrics, outcomes, runes, simvars
  - **`metric_registry.py`**: Metric definition storage
  - **`outcome_ledger.py`**: Simulation outcome tracking
  - **`rune_registry.py`**: Rune (symbolic binding) registry
  - **`simvar_registry.py`**: Simulation variable registry
- **`schemas/`**: JSON schemas for validation
  - `metric.schema.json`, `outcome_ledger.schema.json`, `rune_binding.schema.json`, `simvar.schema.json`
- **`validation.py`**: Schema validation utilities
- **`examples/`**: Exemplar implementations (e.g., `media_competition_exemplar.py`)

Supports 22 academic papers across ABM, diffusion, opinion dynamics, game theory, and cascade families.

#### `abraxas/sim_mappings/`

**Academic Paper → Abraxas Variable Mappings**:

- **`mapper.py`**: Core mapping engine for variable translation
- **`family_maps.py`**: Family-specific mappings:
  - Agent-Based Models (ABM)
  - Diffusion models
  - Opinion dynamics
  - Game theory
  - Cascade models
- **`normalizers.py`**: Variable name normalization (Greek letters, subscripts, etc.)
- **`importers.py`**: CSV/JSON import utilities for paper data
- **`registry.py`**: Paper registry management
- **`types.py`**: Type definitions for mapping system

Enables systematic extraction of simulation priors from academic literature.

#### `abraxas/kernel/`

**5-Phase Execution Kernel** (OPEN → ALIGN → ASCEND → CLEAR → SEAL):

- **`entry.py`**: Phase router with deterministic dispatch
- **`ascend_ops.py`**: Whitelisted ASCEND operations (no IO, no writes)
- **`__init__.py`**: Exports `run_phase`, `Phase`, `execute_ascend`, `OPS`

Provides scoped execution environment for overlay operations.

#### `abraxas/shadow_metrics/`

**Shadow Structural Metrics (Cambridge Analytica-derived)** - Observe-only analytical layer:

- **LOCKED MODULE**: v1.0.0 (2025-12-29)
- Six observe-only psychological manipulation metrics:
  - **SEI**: Sentiment Entropy Index
  - **CLIP**: Cognitive Load Intensity Proxy
  - **NOR**: Narrative Overload Rating
  - **PTS**: Persuasive Trajectory Score
  - **SCG**: Social Contagion Gradient
  - **FVC**: Filter Velocity Coefficient
- **Access Control**: ABX-Runes ϟ₇ (SSO) ONLY - direct access forbidden
- **No-Influence Guarantee**: Metrics observe but never affect system decisions
- **SEED Compliant**: Fully deterministic with SHA-256 provenance
- **Incremental Patch Only**: All modifications via versioned patches
- **Coexists with Predictive Layer**: Analytical/observational metrics complement v1.5 predictive capabilities
- See `docs/specs/shadow_structural_metrics.md` for full specification

#### `abraxas/detectors/shadow/`

**Shadow Detectors v0.1** (NEW in v2.2.0) - Pattern detectors that feed evidence to Shadow Structural Metrics:

**Core Detectors**:
- **Compliance vs Remix Detector** (`compliance_remix.py`): Balance between rote repetition and creative remix
- **Meta-Awareness Detector** (`meta_awareness.py`): Meta-level discourse about manipulation and algorithms
- **Negative Space / Silence Detector** (`negative_space.py`): Topic dropout and visibility asymmetry
- **Anagram Detector** (`anagram.py`): Anagram pattern detection
- **Token Density Analyzer** (`token_density.py`): Token density analysis

**Infrastructure**:
- **`types.py`**: Base detector types (DetectorId, DetectorStatus, DetectorValue, DetectorProvenance)
- **`registry.py`**: Detector registry interface
- **`registry_impl.py`**: Enhanced registry implementation
- **`normalize.py`**: Text normalization utilities
- **`util.py`**: Shared utilities (clamp01, etc.)

**Integration**: `compute_all_detectors()` with deterministic provenance tracking

See `docs/detectors/shadow_detectors_v0_1.md` for full specification

#### `abraxas/runtime/` (NEW in v2.2.0)

**Runtime Infrastructure** - Policy snapshots, invariance gates, and artifact management:

**Policy & Provenance**:
- **`policy_snapshot.py`**: Immutable policy snapshots for reproducibility
  - Create versioned snapshots of policies at execution time
  - SHA-256 hash-based provenance chain
- **`policy_ref.py`**: Policy reference management and resolution
- **`invariance_gate.py`**: DozenRunGate for stability validation
  - Validates that dozen runs produce stable, equivalent results
  - RunHeader invariance checking

**Artifact Management**:
- **`artifacts.py`**: Core artifact utilities and types
- **`retention.py`**: Artifact retention policies and pruning
- **`results_pack.py`**: Results pack creation and validation

**Execution & Performance**:
- **`pipeline_bindings.py`**: Native pipeline binding resolution
- **`deterministic_executor.py`**: Deterministic execution environment
- **`device_fingerprint.py`**: Device fingerprinting for provenance
- **`concurrency.py`**: Concurrency control utilities
- **`perf_ledger.py`**: Performance metrics ledger

#### `abraxas/ers/` (NEW in v2.2.0)

**Event Runtime System** - Event scheduling, bindings, and trace management:

- **`scheduler.py`**: Event scheduling with priority and dependencies
- **`bindings.py`**: Event binding management
- **`invariance.py`**: Invariance tracking across event executions
- **`trace.py`**: Execution trace management
- **`types.py`**: Core type definitions for ERS

#### `abraxas/runes/` (NEW in v2.2.0)

**ABX-Runes Capability Contracts** - Cross-subsystem communication via capability contracts:

- **`capabilities.py`**: Capability registry and invocation
  - `load_capability_registry()` - Load available capabilities
  - `find_capability()` - Lookup by ID
  - `list_by_prefix()` - Filter by prefix
- **`invoke.py`**: Capability invocation utilities
- **`ctx.py`**: RuneInvocationContext for provenance tracking
- **`registry.json`**: Capability registry (oracle.v2.run, etc.)

**Philosophy**: All `abx/` → `abraxas/` communication MUST use capability contracts. Direct imports forbidden.

See `docs/migration/abx_runes_coupling.md` for migration guide.

#### `abraxas/oracle/`

**Oracle Pipeline** - Deterministic daily oracle generation with capability contracts:

- **`registry.py`** (ENHANCED in v2.2.0): Oracle capability registry with rune integration
- **`v2/rune_adapter.py`** (NEW in v2.2.0): Oracle v2 rune adapter for capability invocation
- Deterministic daily oracle generation
- Correlation delta processing
- Time-weighted decay

### TypeScript Server Modules

#### `server/`

Main Express server:

- **`index.ts`**: Server entry point
- **`routes.ts`**: Route registration
- **`storage.ts`**: Storage abstraction
- **`abraxas.ts`**: Abraxas integration
- **`abraxas-server.ts`**: Abraxas route setup

#### `server/abraxas/`

Abraxas-specific server modules:

- **`integrations/`**: Python bridge, external APIs
  - **`sco-bridge.ts`**: Python SCO CLI bridge
- **`pipelines/`**: TypeScript pipelines
  - **`sco-analyzer.ts`**: TS wrapper for SCO
- **`routes/`**: Module-specific routes
  - **`sco-routes.ts`**: SCO API endpoints
- **`weather/`**: Weather engine modules
- **`tests/`**: Server-side tests

#### `client/src/`

React frontend:

- **`components/`**: Reusable UI components
- **`hooks/`**: Custom React hooks
- **`lib/`**: Client utilities
- **`pages/`**: Page components

### ABX Runtime

#### `abx/`

ABX runtime and utilities with **WO-100** acquisition & analysis modules:

**Core Runtime**:
- **`cli.py`**: Main CLI (`abx` command)
- **`core/`**: Core utilities
- **`runtime/`**: Runtime management
- **`server/`**: ABX server components
- **`ingest/`**: Data ingestion
- **`ui/`**: UI components
- **`overlays/`**: Overlay modules
- **`codex/`**: Codex integration

**WO-100: Acquisition & Analysis**:
- **`acquisition_execute.py`**: Task executor with ROI calculation and outcome tracking
- **`task_ledger.py`**: Task lifecycle event tracking (STARTED/COMPLETED/BLOCKED)
- **`anchor_url_resolver.py`**: Anchor → URL resolution system
- **`reupload_storm_detector.py`**: Reupload pattern detection via fingerprinting
- **`media_origin_verify.py`**: Media fingerprint verification
- **`manipulation_metrics.py`**: Manipulation front detection & metrics
- **`manipulation_fronts_to_tasks.py`**: Convert detected fronts to acquisition tasks

**Forecast & Oracle Systems**:
- **`oracle_ingest.py`**: Oracle result ingestion and processing
- **`forecast_accuracy.py`**: Forecast accuracy tracking & horizon band analysis
- **`forecast_ledger.py`**: Forecast storage & retrieval
- **`forecast_review_state.py`**: Review state management
- **`horizon.py`**: Horizon band definitions (near/medium/far)
- **`review_scheduler.py`**: Automated review scheduling system

**AAlmanac & Slang Processing**:
- **`aalmanac.py`**: AAlmanac ledger management (write-once, append-only)
- **`aalmanac_enrich.py`**: AAlmanac enrichment with context & metadata
- **`aalmanac_tau.py`**: Temporal Tau (τ) processing for AAlmanac entries
- **`slang_extract.py`**: Slang candidate extraction from observations
- **`slang_migration.py`**: Slang lifecycle state migration

**Weather & Task Orchestration**:
- **`mimetic_weather.py`**: Memetic weather calculation & signal generation
- **`weather_to_tasks.py`**: Weather signal → acquisition task generation
- **`cycle_runner.py`**: Cycle execution runner for orchestrated workflows
- **`task_union.py`**: Task union operations (merge, deduplicate, prioritize)
- **`task_union_ledger.py`**: Union operation ledger tracking
- **`task_roi_report.py`**: Task ROI reporting & analytics

**Binding & Pollution Analysis**:
- **`term_claim_binder.py`**: Term ↔ claim binding with ledger tracking
- **`truth_pollution.py`**: Truth pollution metrics & narrative contamination

**External Providers**:
- **`providers/fetch_adapter.py`**: HTTP fetch adapter for external sources

Key ABX commands:
```bash
abx doctor          # System diagnostics
abx up              # Start HTTP server
abx smoke           # Run deterministic smoke test
abx ui              # Start chat UI server
abx ingest          # Start data ingestion
```

---

## Testing Patterns

### Python Testing (Pytest)

#### Test File Structure

```python
# tests/test_example.py
import pytest
from abraxas.core.provenance import hash_canonical_json

def test_hash_canonical_json_determinism():
    """Test that hash_canonical_json produces deterministic results."""
    obj = {"b": 2, "a": 1}
    hash1 = hash_canonical_json(obj)
    hash2 = hash_canonical_json(obj)
    assert hash1 == hash2

@pytest.fixture
def sample_data():
    """Fixture providing sample test data."""
    return {"key": "value"}

def test_with_fixture(sample_data):
    """Test using a fixture."""
    assert sample_data["key"] == "value"
```

#### Golden Tests

Golden tests verify output matches expected:

```python
# tests/golden/ contains reference outputs
def test_oracle_output_matches_golden():
    result = run_oracle(inputs)
    expected = load_golden("oracle_output.json")
    assert result == expected
```

### TypeScript Testing (Vitest)

#### Test File Structure

```typescript
// server/abraxas/tests/example.test.ts
import { describe, it, expect } from 'vitest';
import { myFunction } from '../myModule';

describe('myFunction', () => {
  it('should return expected result', () => {
    const result = myFunction('input');
    expect(result).toBe('expected');
  });

  it('should handle edge cases', () => {
    expect(() => myFunction(null)).toThrow();
  });
});
```

### Test Organization

- **Unit tests**: Test individual functions/methods
- **Integration tests**: Test module interactions
- **Golden tests**: Verify deterministic output stability
- **Smoke tests**: Quick sanity checks (`abx smoke`)

---

## Common Development Tasks

### Adding a New Python Module

1. Create module file in appropriate directory:
   ```bash
   touch abraxas/mymodule/my_operator.py
   ```

2. Add `__init__.py` if new package:
   ```python
   # abraxas/mymodule/__init__.py
   from abraxas.mymodule.my_operator import MyOperator

   __all__ = ["MyOperator"]
   ```

3. Update `pyproject.toml` if adding new package:
   ```toml
   [tool.setuptools]
   packages = [..., "abraxas.mymodule"]
   ```

4. Add tests:
   ```bash
   touch tests/test_my_operator.py
   ```

5. Document in relevant README

### Adding a New API Endpoint

1. Create route handler in `server/routes.ts` or module-specific routes:
   ```typescript
   app.post('/api/myendpoint', isAuthenticated, async (req, res) => {
     try {
       const result = await myHandler(req.body);
       res.json(result);
     } catch (error) {
       res.status(500).json({ error: error.message });
     }
   });
   ```

2. Add TypeScript types in `shared/` if needed

3. Add tests in `server/abraxas/tests/`

4. Update API documentation

### Adding a New CLI Command

1. Create CLI module in `abraxas/cli/`:
   ```python
   # abraxas/cli/my_command.py
   import argparse

   def main():
       parser = argparse.ArgumentParser(description="My command")
       parser.add_argument("--input", required=True)
       args = parser.parse_args()
       # Implementation

   if __name__ == "__main__":
       main()
   ```

2. Add entry point in `pyproject.toml` if needed:
   ```toml
   [project.scripts]
   my-command = "abraxas.cli.my_command:main"
   ```

3. Update CLI documentation

### Working with Provenance

Always include provenance for deterministic operations:

```python
from abraxas.core.provenance import Provenance, hash_canonical_json

# Create provenance
prov = Provenance(
    run_id=f"RUN-{uuid.uuid4().hex[:8]}",
    started_at_utc=Provenance.now_iso_z(),
    inputs_hash=hash_canonical_json(inputs),
    config_hash=hash_canonical_json(config),
    git_sha=get_git_sha(),  # Optional
    host=socket.gethostname()  # Optional
)

# Include in output
output = {
    "result": my_result,
    "provenance": prov.__dict__
}
```

### Database Migrations (Drizzle)

```bash
# Generate migration
npm run db:push

# Migrations are auto-applied with drizzle-kit
```

---

## Git Workflow

### Branch Naming Convention

**CRITICAL**: Branch names must follow this pattern for push to work:

```
claude/<descriptive-name>-<session-id>
```

Examples:
- `claude/add-weather-engine-5XgrC`
- `claude/fix-tau-calculation-k7dXE`
- `claude/implement-new-operator-EmBu1`

The session ID at the end is required for git push authentication.

### Commit Message Conventions

Use clear, descriptive commit messages:

```bash
# Good
git commit -m "Add temporal tau operator with confidence bands"
git commit -m "Fix: Handle edge case in phonetic similarity calculation"
git commit -m "Refactor: Extract provenance logic to core module"

# Prefix patterns
# - Add: New feature
# - Fix: Bug fix
# - Refactor: Code restructure without behavior change
# - Update: Modify existing feature
# - Remove: Delete code/feature
# - Docs: Documentation only
# - Test: Add or modify tests
```

### Creating Commits

Follow the git safety protocol from the system instructions:

1. Check status and diff:
   ```bash
   git status
   git diff
   git log --oneline -5
   ```

2. Stage relevant files:
   ```bash
   git add <files>
   ```

3. Create commit with descriptive message:
   ```bash
   git commit -m "$(cat <<'EOF'
   Add comprehensive CLAUDE.md documentation

   - Repository overview and architecture
   - Development workflows and conventions
   - Module organization and testing patterns
   - Git workflow and integration points
   EOF
   )"
   ```

4. Verify commit:
   ```bash
   git log -1
   git status
   ```

### Pushing Changes

**CRITICAL**: Use `-u origin <branch-name>` and retry on network failures:

```bash
# Push with upstream tracking
git push -u origin claude/my-feature-5XgrC

# If network error, retry with exponential backoff:
# Wait 2s, try again
# Wait 4s, try again
# Wait 8s, try again
# Wait 16s, try again (max 4 retries)
```

### Creating Pull Requests

Use GitHub CLI (`gh`):

```bash
# Check current state
git status
git diff main...HEAD
git log main..HEAD

# Create PR with descriptive title and body
gh pr create --title "Add weather engine integration" --body "$(cat <<'EOF'
## Summary
- Implement weather engine module
- Add TypeScript bridge to Python operators
- Include comprehensive tests

## Test plan
- [x] Run pytest tests
- [x] Run npm test
- [x] Test API endpoints manually
- [x] Verify deterministic output
EOF
)"
```

### Merge Conflict Resolution

See `CONFLICT_RESOLUTION_GUIDE.md` for detailed strategies.

General principles:
- Prefer more complete implementation
- Keep provenance and determinism
- Always run tests after resolution
- Document deviations

---

## Integration Points

### Python ↔ TypeScript Bridge

TypeScript calls Python CLI via subprocess:

```typescript
// server/abraxas/integrations/sco-bridge.ts
import { spawn } from 'child_process';

export async function runSCOAnalysis(records: any[], domain: string) {
  return new Promise((resolve, reject) => {
    const python = spawn('python', [
      '-m', 'abraxas.cli.sco_run',
      '--records', recordsPath,
      '--domain', domain,
      '--out', outputPath
    ]);

    // Handle output, errors, completion
  });
}
```

### Express API ↔ React Frontend

Frontend calls backend via fetch/React Query:

```typescript
// client/src/hooks/useAnalysis.ts
import { useQuery } from '@tanstack/react-query';

export function useAnalysis(domain: string) {
  return useQuery({
    queryKey: ['analysis', domain],
    queryFn: async () => {
      const res = await fetch(`/api/sco/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain })
      });
      return res.json();
    }
  });
}
```

### Python CLI Usage

Direct CLI invocation for batch processing:

```bash
# SCO Analysis
python -m abraxas.cli.sco_run \
  --records data.json \
  --out events.jsonl \
  --domain music

# v1.4 Unified CLI
python -m abraxas.cli.abx_run_v1_4 \
  --observations data/obs.json \
  --format both \
  --artifacts cascade_sheet,contamination_advisory

# Scenario Runner
python -m abraxas.cli.scenario_run \
  --input scenario.json \
  --output results/
```

---

## Important Files & Directories

### Must-Read Documentation

1. **`README.md`**: Main project overview
2. **`docs/canon/ABRAXAS_CANON_LEDGER.txt`**: Canonical patterns and principles
3. **`README_SCO.md`**: SCO stack documentation
4. **`README_ORIN.md`**: Orin spine documentation
5. **`INTEGRATION_SCO.md`**: Python/TypeScript integration
6. **`DEPLOYMENT_SCO.md`**: Deployment guide
7. **`CONFLICT_RESOLUTION_GUIDE.md`**: Merge conflict resolution

### Configuration Files

- **`.env`**: Environment variables (never commit)
- **`.env.example`**: Environment variable template
- **`package.json`**: Node.js dependencies and scripts
- **`pyproject.toml`**: Python project configuration
- **`tsconfig.json`**: TypeScript compiler options
- **`vite.config.ts`**: Vite build configuration
- **`vitest.config.ts`**: Vitest test configuration
- **`drizzle.config.ts`**: Drizzle ORM configuration
- **`tailwind.config.ts`**: Tailwind CSS configuration

### Key Data Directories

- **`data/`**: Input data, manifests, maps
- **`out/`**: Output artifacts, reports
- **`tests/fixtures/`**: Test fixture data
- **`tests/golden/`**: Golden test reference data

### Ignore Patterns

See `.gitignore`:
- `node_modules/`, `__pycache__/`, `.pytest_cache/`
- `dist/`, `build/`, `*.egg-info/`
- `.env`, `*.log`, `.DS_Store`
- `abraxas.db`, `*.tar.gz`

---

## Quick Reference

### Common Commands

```bash
# Development
npm run dev              # Start dev server
npm run build            # Build for production
npm test                 # Run TypeScript tests
pytest tests/            # Run Python tests
abx doctor              # System diagnostics
abx smoke               # Quick smoke test

# Type checking
npm run check           # TypeScript type check
mypy abraxas/           # Python type check

# Database
npm run db:push         # Push schema changes

# Git
git status              # Check status
git diff                # View changes
git log --oneline -10   # Recent commits
```

### Environment Variables

```bash
# Required
SESSION_SECRET=<random-string>
DATABASE_URL=file:./abraxas.db

# Optional
GOOGLE_CLIENT_ID=<oauth-client-id>
GOOGLE_CLIENT_SECRET=<oauth-secret>
OPENAI_API_KEY=<api-key>
ANTHROPIC_API_KEY=<api-key>
DECODO_AUTH_B64=<decodo-credentials>
ABX_PORT=8765
ABX_UI_PORT=8780
```

### Key Concepts

**Core Operators & Metrics**:
- **SCO/ECO**: Symbolic Compression Operator / Eggcorn Compression Operator
- **STI**: Symbolic Transparency Index
- **RDV**: Replacement Direction Vector
- **τ (Tau)**: Temporal operator (τₕ, τᵥ, τₚ)
- **D/M Layer**: Disinformation/Misinformation metrics
- **SOD**: Second-Order Dynamics
- **AAlmanac**: Write-once, annotate-only symbolic ledger
- **SER**: Scenario Envelope Runner
- **Provenance**: SHA-256 tracked execution metadata

**Metric Governance (New in v1.4.1)**:
- **6-Gate Promotion**: Provenance, Falsifiability, Non-Redundancy, Rent-Payment, Ablation, Stabilization
- **Candidate Metrics**: Metrics are Contracts, not Ideas - must earn promotion through evidence
- **Evidence Bundle**: Required documentation for metric promotion
- **Promotion Ledger**: Append-only record of promotion decisions with hash chain

**Simulation Layer (New in v1.4.1)**:
- **Simulation Mapping**: Academic paper → Abraxas variable translation
- **Family Maps**: ABM, diffusion, opinion dynamics, game theory, cascade model mappings
- **Rune Registry**: Symbolic bindings between simulation variables and Abraxas metrics
- **SimVar**: Simulation variable definitions with normalization

**WO-100: Acquisition & Analysis (New in v1.4.1)**:
- **Anchor Resolution**: Anchor → URL resolution system
- **Reupload Storm**: Reupload pattern detection via fingerprinting
- **Manipulation Front**: Coordinated manipulation pattern detection
- **Forecast Horizon**: Near/medium/far horizon bands for forecast accuracy
- **Task ROI**: Return-on-investment tracking for acquisition tasks
- **Truth Pollution**: Narrative contamination metrics

**Kernel System (v1.4.1)**:
- **5-Phase Model**: OPEN → ALIGN → ASCEND → CLEAR → SEAL
- **ASCEND Operations**: Whitelisted execution environment (no IO, no writes)
- **Overlay Lifecycle**: Phase-based overlay management

**ABX-Runes & Runtime (NEW in v2.2.0)**:
- **Capability Contracts**: All `abx/` → `abraxas/` communication via rune capabilities
- **Policy Snapshots**: Immutable policy provenance with SHA-256 chains
- **Invariance Gates**: DozenRunGate for stability validation
- **Seal Validation**: Production-ready artifact validation infrastructure
- **ERS**: Event Runtime System for scheduling and trace management
- **No Direct Imports**: Cross-subsystem coupling forbidden (except runes & provenance)

**Shadow Detectors (NEW in v2.2.0)**:
- **Observe-Only**: Pattern detectors that feed evidence without influencing decisions
- **5 Detectors**: Compliance/Remix, Meta-Awareness, Negative Space, Anagram, Token Density
- **Evidence Chain**: Deterministic provenance for all detector outputs
- **No Influence Guarantee**: `no_influence=True` - never affects forecasts
- **Bounds Enforced**: All values clamped to [0.0, 1.0]

---

## Additional Resources

### External Documentation

- **Decodo API**: Web scraping integration
- **Drizzle ORM**: Database ORM documentation
- **Pydantic**: Python data validation
- **Zod**: TypeScript schema validation
- **Vitest**: Test framework documentation

### Internal Documentation

**Specification Documents** (`docs/specs/`):
- `metric_governance.md` - 6-gate metric promotion system
- `simulation_architecture.md` - Simulation layer architecture
- `simulation_mapping_layer.md` - Paper → variable mappings
- `paper_triage_rules.md` - Paper triage & classification
- `paper_mapping_table_template.csv` - Mapping table template

**Detector Documentation** (`docs/detectors/`) - NEW in v2.2.0:
- `shadow_detectors_v0_1.md` - Shadow Detectors v0.1 specification (430 lines)
  - Input requirements, output schemas, determinism guarantees
  - Integration notes, governance policies

**Migration Guides** (`docs/migration/`) - NEW in v2.2.0:
- `abx_runes_coupling.md` - ABX-Runes coupling migration guide
  - Step-by-step migration from direct imports to capability contracts
  - Example code, best practices, troubleshooting

**Artifact Schemas** (`schemas/`) - NEW in v2.2.0:
- 9 JSON schemas for artifact validation:
  - `runindex.v0.schema.json`, `runheader.v0.schema.json`
  - `trendpack.v0.schema.json`, `resultspack.v0.schema.json`
  - `viewpack.v0.schema.json`, `policysnapshot.v0.schema.json`
  - `runstability.v0.schema.json`, `stabilityref.v0.schema.json`
  - `sealreport.v0.schema.json`
- `docs/artifacts/SCHEMA_INDEX.md` - Schema index and validation tooling

**Implementation Plans** (`docs/plan/`):
- `simulation_mapping_layer_plan.md` - Mapping layer implementation

**Example Code**:
- `examples/` - General examples
- `examples/shadow_detectors_integration.py` - NEW: Shadow detector usage
- `abraxas/simulation/examples/` - Simulation exemplars
- `registry/examples/` - Example candidate metrics
- `data/sim_sources/examples/` - 22 academic paper extracts

**Scripts** (`scripts/`) - NEW in v2.2.0:
- `seal_release.py` - Deterministic seal script (seal tick + validation + dozen-run gate)
- `validate_artifacts.py` - Artifact validator CLI

**Test Resources**:
- `tests/fixtures/` - Test fixture data
- `tests/golden/` - Golden test reference data
- `tests/test_metric_governance.py`, `test_sim_mappings_*.py`, `test_promotion_ledger_chain.py`
- NEW in v2.2.0: `test_shadow_detectors_determinism.py`, `test_shadow_detectors_missing_inputs.py`, `test_shadow_detectors_bounds.py`

---

## ABX-Runes Coupling Rules (MANDATORY)

**CRITICAL**: All cross-subsystem communication must flow through ABX-Runes capability contracts. Direct imports between `abx/` and `abraxas/` are forbidden.

### DO NOT Do This (Coupling Violation) ❌

```python
# ❌ WRONG - Direct import across subsystem boundary
from abraxas.oracle.v2.pipeline import run_oracle
from abraxas.memetic.metrics_reduce import reduce_provenance_means

result = run_oracle(observations, config)
means = reduce_provenance_means(profiles)
```

### DO This Instead (Rune Contract) ✅

```python
# ✅ CORRECT - Via capability contract
from abraxas.runes.capabilities import load_capability_registry
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext

# Create invocation context
ctx = RuneInvocationContext(
    run_id="RUN-001",
    caller="abx.mymodule",
    environment="production"
)

# Invoke oracle capability
oracle_result = invoke_capability(
    capability="oracle.v2.run",
    inputs={
        "run_id": "RUN-001",
        "observations": observations,
        "config": config,
        "seed": 42  # For determinism
    },
    ctx=ctx,
    strict_execution=True
)

# Extract results with provenance
oracle_output = oracle_result["oracle_output"]
provenance = oracle_result["provenance"]
```

### Allowed Exceptions

Only these `abraxas.*` imports are allowed in `abx/`:
- ✅ `abraxas.runes.*` - Rune system itself (capabilities, invoke, ctx, registry)
- ✅ `abraxas.core.provenance` - Provenance utilities (canonical_envelope, hash_canonical_json)
- ✅ Test files only: Any import for testing purposes

**All other imports must use capability contracts.**

### How to Add a New Capability

1. **Create JSON schemas** for inputs/outputs in `schemas/capabilities/`
2. **Create rune adapter** in the subsystem (thin wrapper, no core logic changes)
3. **Register capability** in `abraxas/runes/registry.json`
4. **Add golden test** proving determinism
5. **Update coupling lint** to verify violation count decreased

See `docs/migration/abx_runes_coupling.md` for detailed migration guide.

---

## Getting Help

### When Working on Tasks

1. **Check existing documentation**: README files, specs, guides
2. **Examine similar code**: Find patterns in existing modules
3. **Run tests**: Ensure changes don't break existing functionality
4. **Verify determinism**: Same inputs should produce same outputs
5. **Add provenance**: Include SHA-256 hashes for traceability
6. **Use capability contracts**: Never directly import across subsystems

### Best Practices for AI Assistants

1. **Read before modifying**: Always read files before editing
2. **Follow conventions**: Match existing code style and patterns
3. **Test changes**: Run tests to verify functionality
4. **Document changes**: Update relevant documentation
5. **Preserve determinism**: Maintain reproducible behavior
6. **Include provenance**: Track all transformations with hashes
7. **Avoid over-engineering**: Keep solutions simple and focused
8. **No security vulnerabilities**: Check for injection, XSS, etc.
9. **Respect ABX-Runes boundaries**: Use capability contracts, not direct imports

---

## Maintenance Notes (Keep This Doc Timeless)

- Avoid embedding **session-specific state** (current branch names, “last session”, active branches). Prefer links to canonical docs (`docs/`) and code locations.
- Update **Guide Version** when making structural edits to this document (new major sections, new enforcement rules, new subsystems).
- Keep the **Ecosystem Baseline** aligned with repo-wide docs (e.g. `CONFLICT_RESOLUTION_GUIDE.md`) when the overall system versioning changes.

### Operational checklists

**When changing `abx/` and any cross-subsystem boundary**

- Run coupling lint:
  - `grep -r "from abraxas\." abx/ --include="*.py" | grep -v "abraxas.runes" | grep -v "abraxas.core.provenance"`
- If you add a new capability:
  - Add JSON schemas under `schemas/capabilities/`
  - Register it in `abraxas/runes/registry.json`
  - Add a determinism test (golden or equivalent)

**Before release / sealing**

- `pytest tests/ -v`
- `npm test`
- `make seal`
- `make validate`

---

**End of CLAUDE.md**

*This document is maintained as part of the Abraxas project. When in doubt, refer to canonical documentation in `docs/canon/` and existing code patterns.*
