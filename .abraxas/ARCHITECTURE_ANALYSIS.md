# Abraxas Architecture Analysis
## Current State Assessment

**Generated:** 2025-11-20
**Agent:** Abraxas Core Architect
**Version:** ABX-Core v1.2 + SEED Framework

---

## Executive Summary

The current Abraxas codebase exhibits strong conceptual foundations but suffers from structural fragmentation, code duplication, and lack of symbolic kernel integration. This analysis identifies critical refactoring opportunities to transform Abraxas into a modular, deterministic, testable oracle engine.

---

## Current Module Inventory

### Server Modules (Existing)

#### 1. `server/abraxas.ts` ✓ SEED Compliant
**Purpose:** Core scoring engine
**Lines:** 244
**Entropy Class:** Medium
**Deterministic:** True

**Exports:**
- `getWeights()` - Weight configuration retrieval
- `setWeights(weights)` - Weight configuration update
- `scoreWatchlists(watchlists, ritual)` - Main scoring pipeline

**Features:**
- DEFAULT_WEIGHTS (13 features)
- Demo feature generation (ticker/FX)
- Esoteric calculations (numerology, gematria, astrology)
- Transient delta application
- Confidence/risk classification

**Issues:**
- Hardcoded feature extraction
- No symbolic kernel integration
- Missing archetype mappings
- Demo features not extensible

---

#### 2. `server/abraxas-server.ts` ⚠️ Requires Refactoring
**Purpose:** Express routing + duplicate logic
**Lines:** 373
**Entropy Class:** High
**Deterministic:** Partially

**Contains:**
- SQLite database schema
- **DUPLICATE:** Rune system (lines 43-87)
- **DUPLICATE:** Scoring logic (lines 90-194)
- **DUPLICATE:** Metrics tracker (lines 197-239)
- Express endpoints (13 routes)
- WebSocket setup (disabled)

**Issues:**
- ⚠️ **Code Duplication:** Re-implements runes, scoring, metrics
- ⚠️ **Mixed Concerns:** Routing + business logic + data access
- ⚠️ **Inconsistent Scoring:** Different algorithm than abraxas.ts
- ⚠️ **No Separation:** Single monolithic file
- **Blocking Issue:** Must be decomposed before further work

---

#### 3. `server/runes.js` ✓ SEED Compliant
**Purpose:** Runic symbolic system
**Lines:** 46
**Entropy Class:** Low
**Deterministic:** True

**Exports:**
- `getTodayRunes()` - Date-seeded rune selection
- `runRitual()` - Ritual initialization

**Features:**
- 6 runes with symbolic meaning
- Deterministic selection from date seed
- Hash-based pseudo-randomness

**Status:** ✓ Well-structured, ready for integration

---

#### 4. `server/metrics.js`
**Purpose:** Metrics tracking
**Lines:** 89
**Entropy Class:** Low
**Deterministic:** False (uses timestamps)

**Issues:**
- Duplicated in abraxas-server.ts
- Mock accuracy calculations
- No persistence layer integration

---

#### 5. `server/sigil.js`
**Purpose:** Sigil generation
**Lines:** 22
**Entropy Class:** Low
**Deterministic:** False (uses crypto.randomBytes)

**Issues:**
- Not integrated with ritual system
- No symbolic binding

---

#### 6. `server/vc_oracle.js`
**Purpose:** VC analysis
**Lines:** 96
**Entropy Class:** Medium
**Deterministic:** False (uses Math.random)

**Issues:**
- Not bound to ritual system
- No symbolic modulation
- Hardcoded sector data

---

### Client Components (Renderers)

**Identified:** 8 primary components
- RitualRunner
- VCOracle
- MetricsPanel
- DynamicWatchlist
- SigilGenerator
- GrimoireView
- SocialTrendsPanel
- Config

**Status:** Functional, awaiting backend refactor

---

## Critical Issues

### 1. Code Duplication ⚠️ HIGH PRIORITY
**abraxas-server.ts lines 43-194:**
- Duplicate rune system (already in runes.js)
- Duplicate scoring logic (already in abraxas.ts)
- Duplicate metrics tracker (already in metrics.js)

**Impact:**
- Maintenance burden
- Inconsistent behavior
- Entropy leakage
- SEED compliance violation

**Resolution:** Decompose abraxas-server.ts into routing layer only

---

### 2. Missing Symbolic Kernel ⚠️ HIGH PRIORITY
**Required Metrics (Abraxas Kernel v1.2):**
- ❌ SDR (Symbolic Drift Ratio)
- ❌ MSI (Memetic Saturation Index)
- ❌ ARF (Archetype Resonance Factor)
- ❌ NMC (Narrative Momentum Coefficient)
- ❌ RFR (Runic Flux Ratio)
- ❌ Hσ (Entropy sigma)
- ❌ λN (Narrative lambda)
- ❌ ITC (Inter-Temporal Coherence)

**Current:** Only basic esoteric features (numerology, gematria, astrology)

**Impact:**
- Symbolic integrity compromised
- No drift tracking
- No archetype binding
- Weak predictive power

---

### 3. No ERS Integration
**Current:** Ad-hoc ritual execution
**Required:** Event-driven scheduler with:
- Task registration
- Deterministic scheduling
- Provenance tracking
- Resource isolation

---

### 4. Lack of Modular Structure
**Current:**
```
server/
├── abraxas.ts
├── abraxas-server.ts
├── runes.js
├── metrics.js
├── sigil.js
├── vc_oracle.js
├── indicators.ts
└── ...
```

**Issues:**
- Flat structure
- No separation of concerns
- Difficult to test
- Hard to extend

---

### 5. No Test Suite
**Current:** 0 tests
**Required:** Golden tests for:
- Daily oracle
- Watchlist scoring
- VC analysis
- Social scanning
- Ritual execution

---

## Dependency Graph

```
abraxas-server.ts (373 lines)
├── [DUPLICATE] runes logic → should import from runes.js
├── [DUPLICATE] scoring → should import from abraxas.ts
├── [DUPLICATE] metrics → should import from metrics.js
├── Express routing (legitimate)
└── Database access (needs abstraction)

abraxas.ts (244 lines)
├── indicators.ts (evalDynamicIndicators)
├── crypto (hseed function)
└── [MISSING] symbolic kernel

runes.js (46 lines)
└── [STANDALONE] ✓

metrics.js (89 lines)
└── [STANDALONE] but duplicated in abraxas-server.ts

sigil.js (22 lines)
└── [ISOLATED] not integrated

vc_oracle.js (96 lines)
└── [ISOLATED] not integrated
```

---

## Proposed Architecture

### New Structure

```
server/abraxas/
├── core/
│   ├── kernel.ts           # Symbolic metrics (SDR, MSI, ARF, NMC, RFR, Hσ, λN, ITC)
│   ├── scoring.ts          # Core scoring logic (from abraxas.ts)
│   ├── archetype.ts        # Archetype mappings & resonance
│   ├── features.ts         # Feature extraction (modular)
│   └── weights.ts          # Weight management
├── models/
│   ├── ritual.ts           # Ritual type definitions
│   ├── oracle.ts           # Oracle result types
│   ├── vector.ts           # Input/output vectors (ABX-Runes IR)
│   └── metrics.ts          # Metric types
├── pipelines/
│   ├── daily-oracle.ts     # Daily oracle synthesis
│   ├── watchlist-scorer.ts # Equity/FX watchlist scoring
│   ├── vc-analyzer.ts      # VC forecast pipeline
│   ├── social-scanner.ts   # Social trend analysis
│   └── sigil-forge.ts      # Sigil generation pipeline
├── integrations/
│   ├── runes-adapter.ts    # ABX-Runes IR binding
│   ├── ers-scheduler.ts    # ERS task registration
│   └── storage-adapter.ts  # Database abstraction
├── routes/
│   └── api.ts              # Clean routing layer (from abraxas-server.ts)
└── tests/
    ├── golden/
    │   ├── daily-oracle.test.ts
    │   ├── watchlist-scoring.test.ts
    │   └── ritual-execution.test.ts
    └── __snapshots__/
```

---

## Migration Plan

### Phase 1: Decompose abraxas-server.ts ⚠️ BLOCKING
1. Extract routing to `server/abraxas/routes/api.ts`
2. Remove duplicate rune logic → use `server/runes.js`
3. Remove duplicate scoring → use `server/abraxas.ts`
4. Remove duplicate metrics → use `server/metrics.js`
5. Abstract database access to `integrations/storage-adapter.ts`

**Outcome:** Clean separation of concerns

---

### Phase 2: Implement Symbolic Kernel
1. Create `server/abraxas/core/kernel.ts`
2. Implement 8 symbolic metrics (SDR, MSI, ARF, NMC, RFR, Hσ, λN, ITC)
3. Integrate with existing scoring engine
4. Add archetype mappings (`core/archetype.ts`)

**Outcome:** Full symbolic integrity

---

### Phase 3: Refactor Core Modules
1. Move scoring logic to `core/scoring.ts`
2. Modularize feature extraction (`core/features.ts`)
3. Extract weight management (`core/weights.ts`)
4. Add deterministic seeding throughout

**Outcome:** Testable, modular core

---

### Phase 4: Create Pipelines
1. `pipelines/watchlist-scorer.ts` - Equity/FX scoring
2. `pipelines/daily-oracle.ts` - Oracle synthesis
3. `pipelines/vc-analyzer.ts` - VC forecasting
4. `pipelines/social-scanner.ts` - Trend analysis
5. `pipelines/sigil-forge.ts` - Sigil generation

**Outcome:** Clean pipeline architecture

---

### Phase 5: ERS Integration
1. Create `integrations/ers-scheduler.ts`
2. Register all pipelines as SymbolicTasks
3. Bind to ABX-Runes IR (`integrations/runes-adapter.ts`)
4. Implement provenance tracking

**Outcome:** Event-driven execution

---

### Phase 6: Testing & Optimization
1. Create golden test suite
2. Add deterministic snapshots
3. Implement entropy tracking
4. Optimize performance per Abraxas Kernel v1.2

**Outcome:** Production-ready module

---

## Metrics & Goals

### Current State
- **Files:** 6 server modules
- **Lines:** ~870 (with duplication)
- **Code Duplication:** ~35%
- **Test Coverage:** 0%
- **SEED Compliance:** Partial
- **Symbolic Metrics:** 0/8 implemented
- **Determinism:** Inconsistent

### Target State
- **Files:** ~20 modules (organized)
- **Lines:** ~1200 (refactored, no duplication)
- **Code Duplication:** 0%
- **Test Coverage:** >80%
- **SEED Compliance:** 100%
- **Symbolic Metrics:** 8/8 implemented
- **Determinism:** Full (given seed)

---

## Next Actions

**Immediate (Blocking):**
1. ⚠️ Decompose `abraxas-server.ts` to remove duplication
2. Create `server/abraxas/` directory structure
3. Implement symbolic kernel (`core/kernel.ts`)

**Short-term:**
4. Refactor core modules (scoring, features, weights)
5. Build pipeline architecture
6. Add ERS integration

**Medium-term:**
7. Create golden test suite
8. Optimize performance
9. Generate comprehensive documentation

---

## Risk Assessment

**High Risk:**
- Code duplication causing inconsistent behavior
- Missing symbolic kernel limiting predictive power
- No test coverage preventing safe refactoring

**Medium Risk:**
- Flat structure making maintenance difficult
- Lack of ERS integration limiting scalability
- Non-deterministic elements causing entropy drift

**Low Risk:**
- Client components stable and awaiting backend updates
- Core concepts sound, execution needs refinement

---

**Status:** ANALYSIS COMPLETE — Ready for architectural evolution
