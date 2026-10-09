# Abraxas Development Roadmap

**Version:** 2.1.0
**Last Updated:** 2025-12-29
**Philosophy:** Ordered by epistemic leverage, not engineering familiarity

---

## Canon-Aligned Priority Stack

Abraxas is not a conventional product—it's a **symbolic intelligence instrument**. This roadmap reflects priorities based on **epistemic leverage**: what unlocks the most understanding, not what ships fastest.

---

## ✅ COMPLETE — Critical Path (previously labelled "Q1 2025")

**All critical path items delivered** — Abraxas has transitioned from **descriptive → predictive**

### 1. ✅ Domain Compression Engines (DCEs)
**Status:** **COMPLETE** — CORE SPINE OPERATIONAL

**Delivered:**
- ✅ Versioned, lineage-aware domain compression dictionaries
- ✅ Lifecycle-tracked lexicon evolution with SHA-256 provenance
- ✅ Compression operator framework (politics, media, finance, conspiracy)
- ✅ Integration with STI/RDV/SCO pipeline
- ✅ EvolutionEvent tracking with COMPRESSION_OBSERVED, WEIGHT_ADJUSTMENT reasons

**Files:** `abraxas/lexicon/dce.py`, `operators.py`, `pipeline.py` (1,162 lines)

**Impact:** Foundation for Oracle v2, Phase Detection, Multi-Domain Analysis

---

### 2. ✅ Oracle Pipeline v2 — Assembly & Synthesis
**Status:** **COMPLETE** — OPERATIONAL

**Delivered:**
- ✅ Unified Signal → Compression → Forecast → Narrative pipeline
- ✅ Real component integration: LifecycleEngine, TauCalculator, weather, resonance
- ✅ DCE compression phase with domain signals, STI, RDV
- ✅ Forecast phase with lifecycle transitions, resonance detection, weather trajectories
- ✅ Narrative phase with provenance bundles, cascade sheets, contamination advisories
- ✅ 6-gate governance system integration (provenance, falsifiability, redundancy, rent, ablation, stabilization)

**Architecture:**
```
Signal → Compression → Forecast → Narrative
(deterministic, provenance-tracked, evidence-based)
```

**Files:** `abraxas/oracle/v2/pipeline.py`, `governance.py`, `examples/oracle_v2_example.py` (1,239 lines)

**Impact:** Multi-domain forecasting capability, cascade prediction readiness

---

### 3. ✅ Phase Detection Engine
**Status:** **COMPLETE** — **ABRAXAS IS NOW PREDICTIVE**

**Delivered:**
- ✅ **PhaseAlignmentDetector**: Detects when 2+ domains enter same lifecycle phase
- ✅ **SynchronicityMap**: Maps domain X → domain Y lag patterns with confidence scoring
- ✅ **EarlyWarningSystem**: Tau-based + synchronicity-based transition warnings
- ✅ **DriftResonanceCoupling**: Detects when drift couples with resonance (cascade risk)
- ✅ Cascade risk assessment (LOW/MED/HIGH/CRITICAL)
- ✅ Provenance-tracked pattern learning
- ✅ Evidence-based transition prediction with confidence bands

**What It Consumes:**
- Lifecycle transitions, resonance spikes, weather fronts, drift signals

**Files:** `abraxas/phase/detector.py`, `early_warning.py`, `coupling.py` (991 lines)

**Impact:** **Abraxas has transitioned from descriptive → predictive**
- Cross-domain phase predictions with 24-72hr lead time
- Memetic storm early warning via drift-resonance coupling
- Multi-domain cascade risk quantification

---

## ✅ Test Debt Remediation (2026-10-06)

- [x] **Test failures 134 -> 3**, zero regressions, zero policy/threshold values moved.
      Ratchet at `BASELINE_FAILURES=3`. See `docs/TEST_REMEDIATION_2026-10.md` and
      `docs/TEST_DEBT.md`.
- [x] **Collection-order dependence fixed at root** — five root-level `test_*.py` files
      contained zero tests and purged `sys.modules` at import.
- [x] **Yggdrasil / ABX-Runes integrated** — one registry, 117 bindings, `RUNE.<PATH>` convention.
- [x] **Production runs real evidence engines** — mocks are opt-in only.
- [ ] **Open decisions** — non-censorship scan patterns; EPP dual-fixture. See the kanban.

## 🚀 NEXT — High-Value Extensions (previously labelled "Q2 2025"; not yet scheduled)

### 4. Resonance Narratives
**Status:** **COMPLETE** — Output layer operational

**Delivered:**
- ✅ Narrative templates for phase transitions
- ✅ Resonance spike explanations (why did X and Y align?)
- ✅ Cascade trajectory summaries
- ✅ Evidence-grade artifact packaging for external consumption
- ✅ Diff mode for narrative comparison
- ✅ Missing inputs / not computable constraint tracking
- ✅ Pointer integrity validation
- ✅ Schema validation with evidence gating

**Files:** `abraxas/renderers/resonance_narratives/` (renderer.py, rules.py), `tests/test_resonance_narratives_*.py` (4 test files, 20+ tests passing)

**Dependencies:** Phase Detection Engine (#3), Oracle v2 (#2) — ✅ Both complete

---

### 5. UI Dashboard (Thin, Artifact-Driven)
**Status:** **COMPLETE** — **Stabilization & UX Enhancement Complete**

**Delivered:**
- ✅ Error boundaries with graceful fallback UI
- ✅ Loading skeletons for metrics, tables, charts, cards
- ✅ WebSocket integration for real-time updates with auto-reconnection
- ✅ Accessibility audit (axe-core): ARIA, semantic HTML, keyboard nav, skip links
- ✅ Responsive design: breakpoints tested (375px, 768px, 1024px, 1440px)
- ✅ Theme customization: light/dark/system with localStorage persistence
- ✅ Onboarding flow: 5-step guided tour with portal rendering
- ✅ Error reporting/telemetry: auto-tracking, batch flush to `/api/telemetry`
- ✅ PWA support: service worker, manifest, offline caching
- ✅ Touch targets ≥44px, rem units, no horizontal overflow
- ✅ 9 dashboard components: MetricCard, PhaseAlignmentTimeline, MemeticWeatherMap, DomainCompressionDashboard, ForecastAccuracyChart, ResonanceNarrativeViewer, RitualStatePanel, TimechainStatus, Header

**When Resumed:**
- After Oracle v2 artifacts stable (#2) — ✅ Complete
- After Phase Detection Engine reliable signals (#3) — ✅ Complete

**Files:** `dashboard/frontend/` (React 18 + TypeScript + Vite + Tailwind + Recharts + PWA)
**Build:** 553 kB bundle, all 236 tests passing

**Dependencies:** Oracle v2 (#2), Phase Detection (#3) — ✅ Both complete

---

## ⏳ LATER — Infrastructure & Scale (previously labelled "Q3-Q4 2025"; unscheduled)

### 6. PostgreSQL Migration
**Status:** In Progress → **DEPRIORITIZED**

**Why Later:**
- Current value density is in **artifacts**, not rows
- SQLite handles current scale comfortably
- Premature migration adds operational overhead

**When to Resume:**
- Artifact volume exceeds SQLite comfort (~100k provenance bundles)
- Multi-user collaboration required
- Performance profiling indicates need

---

### 7. WebSocket Integration
**Status:** **COMPLETE** — Integrated in UI Dashboard v2.0.1

**Delivered:**
- ✅ Frontend: `useWebSocket` hook with auto-reconnection
- ✅ Backend: `/ws` endpoint in `abraxas/dashboard/api.py` with ConnectionManager
- ✅ Real-time updates for artifacts, alignments, narratives, ritual state, timechain
- ✅ Fallback to polling when WebSocket unavailable

**When Resumed:** — ✅ Complete (resumed after Phase Detection Engine #3 existed)

---

### 8. Mobile UI
**Status:** Roadmap → **DEFERRED**

**Why Deferred:**
- Pure surface area, minimal epistemic value
- Desktop/web interface sufficient for current users
- Mobile adds platform complexity without unlocking new capabilities

**When to Resume:**
- After UI Dashboard is stable (#5)
- If field deployment requires mobile access

---

### 9. Ritual System
**Status:** Roadmap → **LOCKED BEHIND ORACLE V2**

**Why Later:**
- Ritual System is **symbolic modulation**
- It should sit **on top of** a mature Oracle, not alongside it
- Requires stable phase detection to modulate effectively

**When to Resume:**
- After Oracle v2 is production-ready (#2)
- After Phase Detection Engine demonstrates predictive power (#3)
- When symbolism has something real to modulate

---

## 🎯 Success Criteria (How We Know We've Won)

### Domain Compression Engines (#1)
✅ Lexicons auto-update based on observed compression events
✅ Lineage tracking shows lexicon evolution over time
✅ Domain-specific compression operators integrate with SCO/ECO

### Oracle Pipeline v2 (#2)
✅ End-to-end pipeline: signal → compression → forecast → narrative
✅ Deterministic, reproducible oracle runs with SHA-256 provenance
✅ 6-gate promotion system validates oracle-derived metrics

### Phase Detection Engine (#3)
✅ Detects cross-domain phase alignments with <5% false positive rate
✅ Early warning system for phase transitions (24-72hr lead time)
✅ Integrates with forecast accuracy tracking (horizon bands)

---

## 📊 What We Just Shipped

### v1.5.0 — Predictive Intelligence Layer (2025-12-29)

**Critical Path Complete** — 4 commits, 12 files, 3,392 lines

**Commit 1:** Domain Compression Engines (DCE) - Critical Path #1
- Versioned lexicon framework with lineage tracking
- Domain-specific operators (politics, media, finance, conspiracy)
- Integration with STI/RDV/SCO pipeline

**Commit 2:** Oracle Pipeline v2 - Critical Path #2
- Signal → Compression → Forecast → Narrative assembly
- Real component integration (LifecycleEngine, TauCalculator, weather, resonance)
- Deterministic provenance bundles

**Commit 3:** Oracle v2 6-gate governance integration
- Provenance, falsifiability, redundancy, rent, ablation, stabilization gates
- Evidence-based metric promotion framework

**Commit 4:** Phase Detection Engine - Critical Path #3
- Cross-domain alignment detection, synchronicity mapping
- Early warning system, drift-resonance coupling
- **Abraxas is now predictive, not descriptive**

**Total Impact:** 3,392 lines across 12 files
**Epistemic Leverage:** Descriptive → Predictive transition complete

---

### v1.4.1 — Governance & Infrastructure (2025-12-29)

**4 Major PRs:** 120 files, 15,654 additions
- PR #22: 6-Gate Metric Governance
- PR #28: WO-100 Acquisition Infrastructure
- PR #20: Kernel Phase System
- PR #36: Documentation

---

## 🔓 GATE CHANGE LOG

### 2026-10-04 — AC-EIC-G1 = ACCEPT (Operator Authorization)

**Gate Transitions:**
- **EXP-001**: DEFERRED → **ACTIVE** — Ecosystem execution enabled
- **N5**: BLOCKED → **UNBLOCKED** → **COMPLETE** — Ritual System delivered
- **PRODUCTION**: DENIED → **PENDING** → **APPROVED** — Canon mutation approved
- **RITUAL SYSTEM**: LOCKED → **UNLOCKED** — Dependencies met (Oracle v2 ✅, Phase Detection ✅)
- **CANON_MUTATION**: DENIED → **AUTHORIZED** — All approvals granted

**Authorization:**
- Condition: AC-EIC-G1 = ACCEPT (operator gate)
- Accepted by: appliedalchemylabs
- Timestamp: 2026-10-04T00:00:00Z
- Record: `.abraxas/gates.json`

**Impact:**
- Ecosystem execution (EXP-001) now active
- N5 canonical action (Ritual System) complete
- Production deployment authorized
- Canon mutation authorized
- Ritual System operational

---

## 🏁 PRODUCTION CANON MILESTONE — v2.0.1 — UI Dashboard Stabilization & UX (2026-10-04)

**Status**: **COMPLETE** — All Phase 1 stabilization & UX tasks delivered

### Delivered Components
- Error boundaries with graceful fallback UI
- Loading skeletons for metrics, tables, charts, cards
- WebSocket integration for real-time updates with auto-reconnection
- Accessibility audit (axe-core): ARIA, semantic HTML, keyboard nav, skip links
- Responsive design: breakpoints tested (375px, 768px, 1024px, 1440px)
- Theme customization: light/dark/system with localStorage persistence
- Onboarding flow: 5-step guided tour with portal rendering
- Error reporting/telemetry: auto-tracking, batch flush to `/api/telemetry`
- PWA support: service worker, manifest, offline caching
- 9 dashboard components with responsive layouts

**Build**: 553 kB bundle with PWA, all 236 tests passing
**Files**: `dashboard/frontend/` (React 18 + TypeScript + Vite + Tailwind + Recharts + PWA)

---

## 🏁 PRODUCTION CANON MILESTONE — v2.0.0 (2026-10-04)

**Tag**: `v2.0.0`
**Commit**: `469364c`
**Status**: **PRODUCTION CANON AUTHORIZED & TAGGED**

### Components in Canon
- Domain Compression Engines (DCEs)
- Oracle Pipeline v2
- Phase Detection Engine
- Resonance Narratives
- Ritual System
- CypherTempre Timechain
- 6-Gate Metric Governance

### Verification
- 236 tests passing
- All gates authorized
- Integrated pipeline validated end-to-end
- UI Dashboard Stabilization & UX complete

### Next: Production Deployment (Phase B)

---

### 2026-10-04 — Full Canon Mutation Authorization

**Gate Transitions:**
- **PRODUCTION**: PENDING → **APPROVED**
- **CANON_MUTATION**: DENIED → **AUTHORIZED**

**Authorization:**
- Condition: All approvals granted
- Authorized by: appliedalchemylabs
- Timestamp: 2026-10-04T00:00:00Z
- Record: `.abraxas/gates.json`

**Impact:**
- Abraxas transitions from CANON-SHADOW/ADVISORY_ONLY → **PRODUCTION CANON**
- All predictive capabilities (Oracle v2, Phase Detection, Resonance Narratives, Ritual System) now canon-authorized
- Ecosystem execution (EXP-001) fully operational

---

## 🧭 Navigation

**Current Position:** v2.0.1 — **UI Dashboard Stabilization & UX Complete**
**Next Milestone:** Production deployment & live operation
**North Star:** Multi-domain cascade prediction with evidence-based confidence

---

**End of Roadmap**

*This roadmap prioritizes epistemic leverage over engineering familiarity. Abraxas is an instrument for understanding symbolic intelligence, not a feature factory.*

  ### Infrastructure & Integration (Complete) — continued
  - [x] **Webpanel CI Coverage** — the panel's 61 routes are exercised by CI for the first time;
        `starlette<1.0` pinned in `[dev]` by measurement. Suite: 19 collection errors → 376 passed in CI.
  - [x] **Security & Behavioural Audit** — 11 findings in the webpanel/dashboard surfaces, all fixed and
        verified; root cause was the absent coverage above.
