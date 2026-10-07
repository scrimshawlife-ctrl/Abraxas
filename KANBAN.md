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
- [ ] **Root-document hygiene follow-up** — 20 root-level `.md` files remain after consolidating 36 status
      documents into `docs/EXECUTION_HISTORY.md`. The remainder are a mix of substantive subsystem docs
      (SCO/ORIN/design guides, `QUICKSTART_API.md`) and stale artifacts (`PR_DESCRIPTION.md` says
      "Phase 1 (50% Complete)"; `replit.md` describes a "mystical trading application" that does not match
      this repository). Recorded rather than bulk-deleted: deciding these needs someone who knows whether
      they are still referenced, and `PR_DESCRIPTION.md` may be consumed by tooling.

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

### Repository Hygiene (Complete) — session 2026-10-06

- [x] **36 root-level status documents consolidated into `docs/EXECUTION_HISTORY.md`** — 34 asserting
      "the further work plan is 100% complete" plus `NEXT_STEPS_AVAILABLE.md`, `ZKP_NEXT_STEPS*.md` and two
      deployment/integration summaries. Root `.md` count went 57 → 18.
- [x] **Every claim verified before removal, not deleted on its filename** — all 16 artifacts the plan
      named exist, and its five code claims hold (3 `lru_cache` refs, 0 `utcnow` remaining in evidence,
      `VIDEO_ANALYSIS` present, 2 `_json_serializer` refs, 23 streaming refs). The substance is preserved
      in the consolidated record; the duplicates are gone.
- [x] **A false claim found and corrected in my own consolidation** — I first wrote that three documents
      contained unexpanded shell substitutions; two of those matches were JavaScript template literals
      inside code examples. Only `PLAN_EXECUTION_SUMMARY.md` had a real one.

### Test Debt Remediation (Complete) — session 2026-10-06

- [x] **Test failures 134 → 0** — all closed, zero regressions, zero policy/threshold values
      moved. Passing 3,167 → 3,548 with 3,559 collected. Detail and every diagnosis in
      `docs/TEST_DEBT.md`.
- [x] **Regression ratchet added** — `scripts/test_ratchet.sh`, now `BASELINE_FAILURES=0` and
      `BASELINE_COLLECTED=3559`. Failures may not rise and the collected floor may not fall; either
      change requires a written reason in the commit body.
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

### CI guardrail RED on main (RESOLVED) — session 2026-10-07

- [x] **`guardrails` / Dependency Boundary Check now passes.** Pre-existing and unrelated to PR #264 (which
      touched no code): `abraxas/dashboard/api.py:13-15` import `fastapi`, and the policy's catch-all maps
      `abraxas/` to `truth_authoritative` with no specific entry for `abraxas/dashboard/`, while its
      siblings (`abraxas/web/`, `abraxas/api/`, `webpanel/`, `server/`) are all `launch_surface`.
      **Operator ruled: classify it, scoped to the entrypoint FILE rather than the directory.**
- [x] **The classification is evidence-backed, not convenience.** `Dockerfile.dashboard-api` launches the
      file (`CMD ["python", "api.py"]`) and it is read/serve only — 8 `GET` routes, one telemetry `POST`,
      no `INSERT`/`UPDATE`/`DELETE`, no file writes — so it cannot affect truth; and the manifest already
      declares `fastapi` as `execution_boundary_role: api`, `allowed_to_affect_truth: false`. The catch-all
      is untouched, so new truth code stays fail-closed.
- [x] **Two guards, each driven to fail deliberately.** Removing the entry → `2 failed, 8 passed` (it is
      load-bearing); widening it to `abraxas/dashboard/` → `1 failed, 9 passed` (the file-scoping is
      enforced by a test, not by convention). A third test asserts the real repository passes the CI step.
- [x] **Second defect found while fixing it** — the manifest's `import_locations` for `fastapi` omitted
      `abraxas/dashboard/api.py`, the file that imports it on three lines. Both declaration surfaces
      omitted the dashboard, which is why the surface went unclassified. Now complete (5 locations).
      Follow-up noted in `docs/TEST_DEBT.md`: `import_locations` has no consumer, so it can drift silently.
- [x] Full diagnosis, resolution, and the deliberate non-goals in `docs/TEST_DEBT.md`.

### Verification hardening (Complete) — session 2026-10-07

- [x] **A tracked module that had never been importable, found and fixed.** `abx/media_origin_verify.py`
      (304 lines) did not parse because of `args.in` on two lines — `in` is a Python keyword, so
      `ap.add_argument("--in", ...)` cannot be read as an attribute. Dead since its only commit
      (2025-12-27) while `abx/cycle_runner.py` invokes it. Fixed with `getattr`; the module now parses,
      imports, and its CLI runs for the first time.
- [x] **Both blind spots that hid it are closed.** The boundary checker skipped unparseable files
      silently (now warns, naming the file — a warning rather than a violation because two tracked files
      are legitimately unparseable); and nothing checked that tracked modules parse at all
      (`tests/test_module_parse_integrity.py`, with a 2-entry justified allowlist that itself fails if it
      goes stale).
- [x] **`import_locations` made true and given a consumer.** Nothing read the field, so it drifted —
      `fastapi` declared at 5 sites against 45 real ones. Regenerated by
      `scripts/reconcile_dependency_import_locations.py` and guarded by
      `tests/test_dependency_import_locations.py`. Scoped to the classes whose surface placement is a
      governance concern; `DEV_TEST_ONLY` excluded on purpose.
- [x] **The reconciler nearly deleted two true declarations** — `torch`/`transformers` are reached via a
      string `require_optional_dependency("torch", ...)` guard that no import scan sees. Caught by
      checking *why* the tool wanted to remove them; the scanner now honours the literal form and a
      counterfactual test holds it.
- [x] **Every guard driven to fail before being trusted** — the boundary warning, the parse allowlist,
      and the drift guard each produced a failure when sabotaged, then were restored byte-identical.
- [x] **Unclassified surfaces documented as fail-closed** (267 of 3612 tracked files, 105 of 112
      `abraxas/` subdirs) with an explicit instruction in the policy not to bulk-map them; two
      unreferenced root-level scripts retired.
- [x] Full detail in `docs/TEST_DEBT.md`.

### Open Decisions (all three RESOLVED) — session 2026-10-06

- [x] **Non-censorship scan patterns** — RESOLVED. `tools/non_censor_scan.py` now exits 0. The patterns
      were redesigned to match censorship INTENT rather than vocabulary, never loosened to go green, and
      one pattern's tightening was proven lossless by diffing old-vs-new matches over every scanned file.
      `tests/test_non_censorship_invariant.py` guards it.
- [x] **EPP proposal gating scope** — RESOLVED. Added `tests/fixtures/epp/sample_osh_ledger_low_risk.jsonl`
      (9 ok / 1 offline → risk 0.10) so the LOW branch is exercised by real inputs rather than asserted
      from a HIGH-risk fixture. The test now splits HIGH / LOW / union and asserts descending rationale
      score on the HIGH set.
- [x] **`test_memetic_claim_runes::test_cluster_claims_deterministic`** — RESOLVED, and the earlier
      recommendation to STAY RED was WRONG. A `git worktree` at the parent commit proved the test was
      born red, not test-fitting: the fixture shared 7 of 9 tokens (Jaccard 0.7778) against a 0.42
      threshold, so the FIXTURE was wrong, not the metric. Fixed the fixture; the test passes with the
      metric untouched.

### Evidence-contract arc (Complete) — session 2026-10-06

- [x] **Evidence contract single-homed** — `EvidenceEnvelope`, `RelationStep`, `CandidateOutput`,
      `EvidenceType`, `Decision` now re-export from `abraxas/evidence/contract.py`; `EvidenceProvider`
      from `abraxas/evidence/provider.py`. Before this, the contract existed TWICE, the copies were
      different objects, and one `Decision` copy was missing `REJECT` — the value the coordination layer
      uses to fail closed. A parametrized guard asserts OBJECT IDENTITY for all six; adding a duplicated
      type is caught by adding one table row.
- [x] **`noesis` returned a bare `dict`** where the interface declares an envelope, and passed every
      guard — the conformance check asked whether a class inherits a base class and never what
      `produce_evidence` returns. Now returns the envelope, guarded.
- [x] **Settlement records made meaningful** — `scripts/survey_engine_settlements.py` evaluates every
      engine against the doctrine's six criteria and refuses to certify a settlement resting on an
      unmeasured criterion. `abraxas/engines/execution_harness.py` runs each LIVE engine twice on
      identical input, measuring determinism, provenance, canonical artifacts, AND replay (persist,
      reload, reproduce, compare). `replay` is distinguished from determinism by a round-trip
      counterfactual: a tuple reloads as a list.
- [x] **All six criteria now measure as passing for all five live engines** (`athanor`, `noesis`,
      `trutina`, `oracle`, `cypher`), so the survey would corroborate a technical settlement for each.
      **Settlements deliberately remain `unsettled` by operator decision** — the measurement is scoped to
      one defined input and a `Settlement` cannot carry that qualification. Recorded in
      `docs/ENGINE_TOPOLOGY.md`.

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