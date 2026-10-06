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

### Test Debt Remediation (Complete) — session 2026-10-06

- [x] **Test failures 134 → 3** — 131 of 134 closed, zero regressions, zero policy/threshold
      values moved. Passing 3,167 → 3,338. Detail and every diagnosis in `docs/TEST_DEBT.md`.
- [x] **Regression ratchet added** — `scripts/test_ratchet.sh`, `BASELINE_FAILURES=3`.
      The baseline may only decrease; raising it requires a written reason in the commit body.
- [x] **Collection-order dependence fixed at root** — the suite imported script files that
      purged `sys.modules` at import time. FIVE of eight root-level `test_*.py` files contained
      ZERO tests; moved to `scripts/smoke/`. Baseline claims now require BOTH collection orders.
- [x] **Yggdrasil ↔ ABX-Runes integration** — `YggdrasilEngineRegistry` (which declares itself
      "Source of Truth for Engine Registration") now actually loads the 117 rune bindings; it
      previously imported none of them and nothing imported it back.
- [x] **Rune capability convention unified** — all 117 capability ids migrated to the declared
      `RUNE.<PATH>` form (witness: `docs/runes/`, the Rune Specs Index). 67 files, 194 literals,
      zero regressions. Sigil-numeral `rune_id`s deliberately left alone: the sigils ARE the
      canon identity and the manifest enforces them.
- [x] **Production engine wiring** — `ProductionOrchestrator` registers real providers (athanor,
      cypher, noesis, oracle, trutina) instead of five inline mock types; mocks are opt-in only.
      Health can now report an unimplemented engine as unhealthy rather than HEALTHY.
- [x] **Model-agnostic inference adapter** — `abraxas/evidence/adapters/model_agnostic.py`;
      athanor is constructible without a bespoke model. UI carries a "custom inference coming
      soon" notice. Frontend build verified.
- [x] **Jev consulted five times; no threshold was ever moved** — `move_threshold` 0.000 and
      `lower_threshold` 0.000 on every occasion. Two of my own recommendations were retracted
      after reading the code, and one governance allowlist was reverted.

### Open Decisions (need an operator ruling)

- [ ] **Non-censorship scan patterns** — `tools/non_censor_scan.py` reports 244 violations,
      including `abraxas/synthesis/firewall.py` ITSELF (28) and its tests (76 + 68). The
      `BANNED_PATTERNS` are bare-word regexes (`firewall`, `sanitize`, `response_mode`, ...),
      so the repo's own synthesis-firewall subsystem cannot coexist with the guard as written.
      Needs patterns that match censorship INTENT, not vocabulary. Generated bundles
      (`dashboard/frontend/dist/assets/*.js`) should also be excluded.
- [ ] **EPP proposal gating scope** — `epp_builder._build_proposals` gates every branch on a
      single GLOBAL composite risk (`_risk_components(integrity_snapshot, osh_stats)`, built
      once, dataset-level by construction). `SIW_TIGHTEN_SOURCE` needs risk ≥ 0.6 and
      `SIW_LOOSEN_SOURCE` needs risk ≤ 0.3, so no single portfolio can produce both — yet
      `test_epp_builds_ranked_proposals` asserts both from one fixture. Needs a second,
      low-risk fixture.
- [ ] **`test_memetic_claim_runes::test_cluster_claims_deterministic` — recommended to STAY RED.**
      Token Jaccard scores 0.21 against an expected 0.42. Passing it means redesigning a
      similarity metric to hit a number, i.e. test-fitting. Jev's weakest ruling (0.73).

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