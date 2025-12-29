# Abraxas Development Roadmap

**Version:** 1.4.1
**Last Updated:** 2025-12-29
**Philosophy:** Ordered by epistemic leverage, not engineering familiarity

---

## Canon-Aligned Priority Stack

Abraxas is not a conventional product—it's a **symbolic intelligence instrument**. This roadmap reflects priorities based on **epistemic leverage**: what unlocks the most understanding, not what ships fastest.

---

## 🔥 NOW — Critical Path (Q1 2025)

### 1. Domain Compression Engines (DCEs)
**Formerly:** "Expanded Lexicons"
**Status:** In Progress → **PROMOTED TO CORE SPINE**

**Why Critical:**
- Lexicons are compression operators, not content
- Everything downstream (ASC, lifecycle forecasting, resonance, provenance) feeds on lexicons
- Without mature DCEs, every subsystem starves

**Deliverables:**
- [ ] Versioned, lineage-aware domain compression dictionaries
- [ ] Lifecycle-tracked lexicon evolution
- [ ] Compression operator framework (not just word lists)
- [ ] Domain-specific: politics, media, conspiracy, finance, technology
- [ ] Integration with existing STI/RDV/SCO pipeline

**Dependencies:** None (foundational)
**Blocks:** Oracle v2, Phase Detection, Multi-Domain Analysis

---

### 2. Oracle Pipeline v2 — Assembly & Synthesis
**Status:** 70% Complete (implicit) → **PULL FORWARD**

**Why Critical:**
- You've already implemented the core components:
  - Lifecycle forecasting (Patch 33)
  - Cross-domain resonance (Patch 29)
  - Provenance bundles (Patch 35)
  - Memetic weather with trajectories
- This is an **assembly task**, not R&D

**Reframe:**
```
Signal → Compression → Forecast → Narrative
(backed by artifacts, not vibes)
```

**Deliverables:**
- [ ] Unified Oracle v2 pipeline integrating existing subsystems
- [ ] Signal ingestion from multiple domains
- [ ] Compression via DCEs (dependency: #1)
- [ ] Forecast generation using lifecycle forecasting
- [ ] Narrative artifact output (provenance bundles)
- [ ] Governance integration (6-gate promotion for oracle metrics)

**Dependencies:** Domain Compression Engines (#1)
**Unlocks:** Phase Detection Engine (#3), Resonance Narratives (#4)

---

### 3. Phase Detection Engine
**Formerly:** "Event Correlation"
**Status:** Roadmap → **PROMOTED & REFRAMED**

**Reframe:**
This is **Cross-Domain Phase Alignment Detection**, not generic event correlation.

**What It Consumes:**
- Lifecycle transitions (Patch 33)
- Resonance spikes (Patch 29)
- Memetic weather fronts (Patch 26)
- Slang emergence patterns (Patch 27)
- Truth pollution signals (abx/truth_pollution.py)

**Deliverables:**
- [ ] Phase alignment detection across domains
- [ ] Synchronicity mapping (when does domain X enter same phase as domain Y?)
- [ ] Drift-resonance coupling detection
- [ ] Early warning system for phase transitions
- [ ] Integration with forecast accuracy tracking (WO-100)

**Dependencies:** Oracle Pipeline v2 (#2), DCEs (#1)
**This is where Abraxas becomes predictive, not descriptive.**

---

## 🚀 NEXT — High-Value Extensions (Q2 2025)

### 4. Resonance Narratives
**Status:** New (output layer)

**What:**
Human-readable narrative generation from resonance vectors, phase alignments, and forecast artifacts.

**Why:**
- Multi-Domain Analysis capability exists (via resonance vectors, domain maps, provenance bundles)
- What's missing is **presentation**, not capability
- This is an output layer, not core architecture

**Deliverables:**
- [ ] Narrative templates for phase transitions
- [ ] Resonance spike explanations (why did X and Y align?)
- [ ] Cascade trajectory summaries
- [ ] Evidence-grade artifact packaging for external consumption

**Dependencies:** Phase Detection Engine (#3), Oracle v2 (#2)

---

### 5. UI Dashboard (Thin, Artifact-Driven)
**Status:** In Progress → **DELAYED** (with good reason)

**Why Delayed:**
- UI calcifies architecture if introduced before epistemics settle
- Current priority: stabilize Oracle v2 artifacts first
- Dashboard should **display**, not drive, the system

**When to Resume:**
- After Oracle v2 artifacts are stable (#2)
- After Phase Detection Engine produces reliable signals (#3)

**Deliverables (when resumed):**
- [ ] Memetic weather visualization (fronts, pressure, drift)
- [ ] Phase alignment timeline
- [ ] Domain compression dashboards
- [ ] Forecast accuracy tracking (horizon bands)
- [ ] Real-time artifact streaming (read-only)

**Dependencies:** Oracle v2 (#2), Phase Detection (#3)

---

## ⏳ LATER — Infrastructure & Scale (Q3-Q4 2025)

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
**Status:** In Progress → **DEPRIORITIZED**

**Why Later:**
- Abraxas is **phase-based**, not tick-based
- Real-time streaming is seductive but premature
- Current batch/cycle processing is sufficient

**When to Resume:**
- After Phase Detection Engine exists (#3)
- When live phase transitions require <1min latency
- When UI Dashboard needs sub-second updates

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

## 📊 What We Just Shipped (v1.4.1 Recap)

**4 Major PRs Merged (2025-12-29):**

1. **PR #22** - 6-Gate Metric Governance (15k+ lines)
   - Anti-hallucination promotion framework
   - Simulation mapping layer (22 academic papers)
   - Hash-based provenance chain

2. **PR #28** - WO-100 Acquisition Infrastructure (40+ modules)
   - Anchor → URL resolution
   - Reupload storm detection
   - Forecast accuracy tracking
   - Manipulation front detection

3. **PR #20** - Kernel Phase System
   - 5-phase execution model (OPEN/ALIGN/ASCEND/CLEAR/SEAL)
   - Whitelisted ASCEND operations

4. **PR #36** - Documentation overhaul

**Total:** 120 files changed, 15,654 additions, 466 deletions

---

## 🧭 Navigation

**Current Position:** Post-v1.4.1 consolidation
**Next Milestone:** Domain Compression Engines (DCEs)
**North Star:** Predictive phase detection across symbolic domains

---

**End of Roadmap**

*This roadmap prioritizes epistemic leverage over engineering familiarity. Abraxas is an instrument for understanding symbolic intelligence, not a feature factory.*
