# Kanban Board for Abraxas

![CI](https://github.com/scrimshawlife-ctrl/Abraxas/actions/workflows/ci.yml/badge.svg)
![Auto-move](https://github.com/scrimshawlife-ctrl/Abraxas/actions/workflows/auto-move.yml/badge.svg)
![WIP Limits](https://github.com/scrimshawlife-ctrl/Abraxas/actions/workflows/wip-limits.yml/badge.svg)

## To Do (Backlog - Deprioritized/Deferred)
- [ ] **PostgreSQL Migration** — Deprioritized until artifact volume exceeds SQLite comfort (~100k bundles)
- [ ] **Mobile UI** — Deferred until field deployment requires mobile access
- [ ] **Ritual System Extensions** — Custom protocols, integration with live Oracle/Phase engines
- [ ] **Multi-domain cascade prediction with live data** — Production deployment & live operation

## In Progress
- [ ] **Production deployment preparation** — Config, monitoring, health checks for live operation
- [ ] **Canon mutation execution** — Formal transition from CANON-SHADOW to production canon

## Done ✅

### Q1 2025 Critical Path (Complete)
- [x] **Domain Compression Engines (DCEs)** — Versioned lexicons, lineage tracking, domain operators
- [x] **Oracle Pipeline v2** — Signal → Compression → Forecast → Narrative with 6-gate governance
- [x] **Phase Detection Engine** — Cross-domain alignment, synchronicity mapping, early warning, drift-resonance coupling
- [x] **Resonance Narratives** — Human-readable output layer with diff mode, constraints, evidence gating
- [x] **UI Dashboard** — Thin, artifact-driven dashboard (Oracle v2 stable, Phase Detection reliable)
- [x] **UI Dashboard Stabilization & UX** — Error boundaries, skeletons, WebSocket, accessibility, theme, PWA, telemetry

### Q1 2025 Qualification Gates (Complete)
- [x] **HYPERLEX-Q1** — Hyperlex Instrument qualification
- [x] **SEMION-Q1** — Peircean Sign Relation qualification
- [x] **NOESIS-Q1** — Latent Structure/Noesis qualification
- [x] **TRUTINA-Q1** — Brier Calibration qualification
- [x] **ABRAXAS-Q1** — Governance/Arbitration qualification

### Infrastructure & Integration (Complete)
- [x] **Technical Debt Resolution** — datetime.utcnow deprecation, JSON serialization, evidence/__init__.py recovery
- [x] **CypherTempre Timechain Integration** — Immutable record storage with PoW, file fallback
- [x] **Ritual System (N5)** — Symbolic modulation layer with 7 protocols, effect tracking
- [x] **Integrated Pipeline Test** — Phase Detection + Oracle v2 + Resonance Narratives + Ritual System

### Gates & Authorization (Complete)
- [x] **AC-EIC-G1 = ACCEPT** — Operator acceptance gate passed
- [x] **EXP-001: ACTIVE** — Ecosystem execution enabled
- [x] **N5: COMPLETE** — Ritual System delivered
- [x] **PRODUCTION: APPROVED** — Production deployment authorized
- [x] **CANON_MUTATION: AUTHORIZED** — Canon mutation authorized
- [x] **RITUAL_SYSTEM: UNLOCKED** — Dependencies met

---

## Column Definitions & Automation

| Column | Meaning | Automation |
|--------|---------|------------|
| **To Do** | Backlog items - explicitly deprioritized/deferred per roadmap | — |
| **In Progress** | Active work items currently being executed | WIP limit: max 3 PRs per author, 10 total |
| **Done** | Completed canonical actions with tests passing | Auto-move on PR merge |

### CI/CD Automation
- **CI** (`.github/workflows/ci.yml`): Tests, health checks, config validation, pipeline dry-run on every push/PR
- **Auto-move** (`.github/workflows/auto-move.yml`): Moves merged PRs to "Done" column (requires GitHub Project "Kanban")
- **WIP Limits** (`.github/workflows/wip-limits.yml`): Enforces max 3 PRs/author, 10 total PRs, 20 issues

### Badges
![CI](https://github.com/scrimshawlife-ctrl/Abraxas/actions/workflows/ci.yml/badge.svg)
![Auto-move](https://github.com/scrimshawlife-ctrl/Abraxas/actions/workflows/auto-move.yml/badge.svg)
![WIP Limits](https://github.com/scrimshawlife-ctrl/Abraxas/actions/workflows/wip-limits.yml/badge.svg)