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
- [x] **Every CI gate audited by injecting a fault** — the "Dependency Metadata Check" was a CI step that
      **could not fail**: it detected real discrepancies (`manifest_only_count=1`) and still exited 0, so
      its findings were printed and ignored. It now fails on the three genuine invariants and stays
      informational for `declared_only` (9 harmless cases on this repo), with a control test so it cannot
      degrade into failing on everything. Boundary check, proof-check, registry-check and governance-lint
      were each driven to fail and are real gates.
- [x] Full detail in `docs/TEST_DEBT.md`.

- [x] **The doctrine arc's four open questions are all answered** — three were already resolved and
      recorded (the `--allow-simulated` gate deliberately admits `undeclared`; `claim_strength` is
      excluded from `packet_hash`; `derived` has no producer so its rank is unexercised). The fourth is
      the operator's to declare (which engine, if any, claims *technical* settlement) and the mechanism
      plus a corroborating survey now exist for it.
- [x] **A real gap found while checking them and closed:** `SourcePacket.claim_strength` was an
      unvalidated `Dict[str, Any]` while the validating `ClaimStrength` model had **no production
      caller** — the test performed by hand the validation production never did, so
      `{"formality": "vibes"}` was accepted. Now typed as the model: malformed input is rejected, the
      packet hash is unchanged, and it was done while no producer emits the field (free now, breaking
      later).
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

## Engine Completion Audit — session 2026-10-07

Requested view of how complete each engine is. **Engines live in their own repositories**, so completion
has **two axes** — and they disagree in a way that is itself the finding: `hyperlex` has a substantial repo
and is not yet an Abraxas provider, while `oracle` and `cypher` were `live` in Abraxas with **no repository
at all**.

> **CORRECTED — same session.** The first version of this table reported `noesis` and `semion` as having
> **no repository**. Both have public repositories with substantial history (131 and 121 files; 36 and 39
> commits) that had simply never been cloned to this machine: the audit listed directories under `$HOME` and
> treated absence there as absence anywhere. The method is fixed — see "How the repo ladder is measured" —
> and the two rows are rewritten below. The tell that the method was wrong is in the original table: two rows
> that were simultaneously complete inside Abraxas and empty everywhere obvious.
>
> Everything below is now measured against the remote (`gh repo list` + `git ls-remote`, then clone), never
> against a filesystem listing.

### How the numbers are computed (stated so anyone can recompute them)

**Integration ladder** — in Abraxas, 7 stages, equal weight, from `abraxas/engines/manifest.py` and
`scripts/survey_engine_settlements.py`:

1. declared in the canonical manifest
2. lifecycle derivable — `register_engine` accepts the name and derives status from the manifest
3. provider resolves — the declared `module:attribute` imports (survey `entry_point`)
4. conforms to `EvidenceProvider` (survey `conforms`)
5. every measured criterion passes — determinism, provenance, canonical_artifacts, replay plus the presence
   criteria → `satisfiable True`
6. registered in production with a REAL provider — `tests/test_production_engine_wiring.py` asserts the
   registry's names equal `live_engines()` and are disjoint from `planned_engines()`
7. a **corroborated** technical settlement claim — **claimed by all five live engines** as of 2026-10-07
   (`athanor`, `cypher`, `noesis`, `oracle`, `trutina`), each with its own cited evidence set; the survey
   corroborates every one of them and exits 0

**Repo ladder** — the engine's own repository, 5 stages, equal weight:

1. repository directory exists
2. under version control with at least one commit
3. template rendered — no `{{ }}` cookiecutter placeholders remain
4. implementation present — ≥5 source modules
5. tests present — ≥1 test module

`Combined` is the plain mean of the two ladders, included only to give one sort order. It is a presentation
choice, not a measurement — the two ladders are the measurements.

### Results

| engine | Abraxas status | own repo | src `.py` | test `.py` | commits | integration | repo | combined |
|---|---|---|---|---|---|---|---|---|
| `athanor` | live | yes | 19 | 21 | 221 | 86% (6/7) | 100% (5/5) | **93%** |
| `trutina` | live | yes | 9 | 10 | 66 | 86% (6/7) | 100% (5/5) | **93%** |
| `noesis` | live | yes | 46 | 29 | 36 | 86% (6/7) | 100% (5/5) | **93%** |
| `oracle` | live | yes ‡ | 3 | 1 | 1 | 86% (6/7) | 80% (4/5) | **83%** |
| `cypher` | live | yes ‡ | 3 | 1 | 1 | 86% (6/7) | 80% (4/5) | **83%** |
| `hyperlex` | planned | yes | 86 | 66 | 4 † | 29% (2/7) | 100% (5/5) | **65%** |
| `semion` | planned | yes | 5 | 4 | 39 | 29% (2/7) | 100% (5/5) | **65%** |
| `chronos` | planned | yes | 3 | 1 | 3 | 29% (2/7) | 80% (4/5) | **55%** |
| `resonance` | planned | yes | 3 | 1 | 2 | 29% (2/7) | 80% (4/5) | **55%** |
| `aether` | planned | yes | 3 | 1 | 1 | 29% (2/7) | 80% (4/5) § | **55%** |

† **`hyperlex`'s local clone is SHALLOW** (`.git/shallow` exists; `git rev-parse --is-shallow-repository` is
`true`), so its commit count and any "N commits behind main" figure computed from it are artifacts of the
shallow boundary, not measurements. The count is shown only because the column exists; do not read it as
history. Its branch question was settled by **content**, not by ancestry: the three commits on
`docs/pytrends-evidence-design` create exactly the two documents that already exist on `main`, and `main`
additionally carries the implementation (`src/hyperlex/intake/trends.py`, `tests/test_trends_evidence.py`). The
branch is superseded.

‡ **`oracle` and `cypher` had no repository at all** — `gh repo view scrimshawlife-ctrl/Oracle` and `…/Cypher`
both returned *"Could not resolve to a Repository"*. Both were created this session (private) and now carry
the engine spec, a `compat/abraxas/` bridge to the in-tree adapter, and boundary tests. Their repo ladder sits
at 4/5 rather than 5/5 because each has 3 source modules, below the ≥5 threshold — the threshold is the
ladder's, not a judgement about the work.

§ **`aether`'s repo score overstates it.** Stage 4 of the repo ladder asks whether an implementation is
present; `aether` has 3 modules, and every one of them refuses to produce evidence. The ladder cannot tell a
boundary from an engine, so read that 4/5 as "the repository is structurally complete" and never as "the
engine exists". Its own `SPEC.md` marks every component `Exists: no`.

**These counts are not comparable with the first version of this table.** That version measured a different
scope (it recorded 63 source modules for `athanor`, where this measures 19 `.py` files under `src/`). The
ladders are the measurements; the counts are orientation.

Every live engine sits at 6/7 on the integration ladder and is blocked only by stage 7, which is a **claim**
nobody has made, not a capability anybody lacks.

### Where each engine actually lives (in-tree footprint in Abraxas)

Added because the two ladders cannot explain an engine being `live` in Abraxas while its standalone repo
is an empty scaffold. Counted as TRACKED files whose path contains the engine name as a whole segment —
**a proxy, and a coarse one** (see the `oracle` caveat below):

| engine | in-tree files | where they concentrate |
|---|---|---|
| `oracle` | 227 | `abraxas/oracle/` (68), `tests/oracle/` (13), `core/oracle/` (11) |
| `resonance` | 18 | `tests/fixtures/` (5), `abraxas/renderers/` (4) |
| `hyperlex` | 8 | `abraxas/evidence/` (5) |
| `noesis` | 5 | `abraxas/evidence/` (4) |
| `trutina` | 5 | `abraxas/evidence/` (5) |
| `semion` | 4 | `abraxas/evidence/` (4) |
| `cypher` | 2 | `abraxas/evidence/` (1) |
| `athanor`, `chronos`, `aether` | 0 | nothing in-tree |

**The engines split into two homes.** `athanor`, `chronos` and `aether` have nothing in the Abraxas tree —
their work is (or would be) entirely in their own repo. The rest live in-tree, mostly as providers under
`abraxas/evidence/`. That explains **why `oracle` and `cypher` were `live` while their standalone
repositories had never been built**: the working implementation is the in-tree adapter
(`abraxas/evidence/adapters/`).

The engine repositories now mirror that rather than duplicating it. `Oracle` and `Cypher` hold the spec plus
a `compat/abraxas/` bridge that RESOLVES the canonical adapter, and their tests assert the wrapped provider's
**module path** is Abraxas's — so a second implementation cannot appear in the repo without failing a test.
The same rule holds in the other direction for `Resonance`, which had code in Abraxas but no adapter
anywhere: its repository composes the in-tree phase detectors, and its tests assert those factories'
module paths in turn.

**`oracle`'s number is not an engine count.** The 227 spans a whole in-tree *subsystem* — `abraxas/oracle/`
(the v2 collectors/renderers), plus tests, schemas and contracts — whereas the engine's provider is the thin
adapter `abraxas/evidence/adapters/oracle.py`. Read it as "there is a large oracle subsystem in the tree",
never as "the oracle engine has 227 implementation files". The same caution applies to every row: a name
match is not a component boundary.

### Findings

1. **Five of the ten engine repos were unrendered cookiecutter templates** — `Oracle`, `Cypher`, `Chronos`,
   `Resonance` and `Aether`, each holding the same 5 files and a byte-identical 42-line `SPEC.md`, their
   `src/<name>/__init__.py` still containing the raw placeholder:

   ```python
   from .compat.abraxas import {{ EngineName }}EvidenceProvider
   ```

   That is **not valid Python** — every one of those files fails `ast.parse` — and `.compat.abraxas` did
   not exist in the repo at all (the cookiecutter had created `src/<name>/compat/abraxas/` as an **empty
   directory**). Their `KANBAN.md` was the template's own placeholder ("Define future work items / Current
   sprint work"). These were not partial implementations; nothing had ever been rendered or built.
   **All five are now rendered, specified, implemented, tested and pushed** (`Chronos` a5d772a+8869225,
   `Resonance` 81ae30c, `Oracle` a9a3377, `Cypher` f21f622, `Aether` 9245248). `Resonance` was the worst
   damaged: its `pyproject.toml` carried *nested, doubly-substituted* description text and did not parse at
   all.
2. **CORRECTED: `noesis` and `semion` both have substantial repositories.** `Noesis` is 131 files / 36
   commits — 27 runtime slices implemented, 16 spec documents, 20 contract schemas, CI workflows, and
   accepted acceptance evidence from a pinned real-model run. `Semion` is 121 files / 39 commits — 66 spec
   documents, 4 contracts, a dual-use gate, a model card. Neither was ever cloned to this machine, which is
   the whole of the original error. Both are now cloned and in sync with their remotes.
3. **Most repos are real.** Beyond `athanor` (19 source / 21 test files), `trutina` (9 / 10) and `hyperlex`
   (86 / 66), add `noesis` (46 / 29) and `semion` (5 / 4). The counts for the five newly-rendered engines are
   small by design: each is a spec, a bridge to (or composition of) the machinery that lives in Abraxas, and
   boundary tests — not a reimplementation.
4. **Version control is now universal.** `Oracle` and `Cypher` were plain directories with no `.git` and no
   remote — `gh repo view` for both returned *"Could not resolve to a Repository"*. Both were created this
   session as private repositories on `main`. `Aether`'s repository existed but was **empty at both ends**
   (0 commits locally, and `git clone` reported an empty remote); it now carries its spec, a fail-closed
   provider and tests. `Chronos` had no `.gitignore` and had committed four `__pycache__` artifacts; they are
   untracked via `git rm --cached` and the file is committed.
5. **`athanor` still carries an unimportable tracked module.** `scripts/batch_jev_harvest.py:209` fails
   `ast.parse` (65 `.py` files examined, exactly 1 unparseable — measured, not inferred). The line is a
   mangled f-string that builds `pair_id`:

   ```python
   "pair_id": f"corr.{family}.{role}.{hashlib.sha256((family+"."+role+"."+atom.get("atom_id","")).encode()).hexdigest()[:6]}". + role + ...,
   ```

   quoted three ways over, the same corruption class as the mangled `pyproject.toml` headers in the
   scaffolds. **Left unfixed deliberately:** the plausible reconstruction
   (`f"corr.{family}.{role}.{sha256(…)[:6]}"`) is a guess about the intended `pair_id` format, and an id
   format is a data effect, not a cosmetic one — a wrong reconstruction silently changes harvest identity.
   The fix needs the harness owner. Athanor also has **10 untracked artifacts** (an execution receipt,
   RUN-001/002/003 reports, seals and preregistrations, two training configs, one `.clean` fixture) dated
   four days after its `STATUS.md`, whose README says *"Full receipts live in STATUS.md"* — so the sealed
   runs are unrecorded in the repo. Also left to its owner: the repo's anti-goals list a *"copyright
   dump"*, so whether the corpus fixture may be tracked at all is a policy question, not a cleanup.
6. **All five live engines remain `unsettled`.** Every measured criterion passes and no technical
   settlement is claimed. Capability is not a claim; declaring one is the operator's call, and the survey
   (`scripts/survey_engine_settlements.py`) will corroborate it when made.
7. **The five unresolved rune bindings are NOT engine-related.** All five are `ϟ_EVOLVE_*` with reason
   `MISSING_OPERATOR` in `abraxas/evolve/rune_adapter.py`. Stated because "5 unresolved bindings" reads as
   though it bears on the five live engines; it does not.

### What would move each tier

- **Live engines (6/7):** ~~declare a technical settlement with its evidence path, or deliberately record
  that none is claimed.~~ **DONE for all five** (2026-10-07): `oracle` first, alone, so the word "precedent"
  would mean something; then `athanor`, `noesis`, `trutina` and `cypher`, each independently corroborated by
  the survey and individually cited. **The evidence sets differ widely, and each manifest note says which
  it is** — `noesis` and `trutina` cite a spec, a Q1 suite and a qualification receipt; `oracle` cites its
  adapter, contract and governance record; `athanor` cites only its implementation and the conformance
  guard; `cypher` cites only its adapter and behavioural suite. Claiming the last two was the judgement
  call, and the notes state the thinness rather than implying a uniform base.
  **Empirical and economic remain `unsettled` on every engine, deliberately.** A `technical` settlement says
  the capability reliably meets its specification; it says nothing about usefulness or adoption, and those
  are the harder claims. Plan: `.hermes/plans/2026-10-07_031025-settlements-and-semion-decisions.md`.
- **`semion`'s DEC-004 cannot be closed from Abraxas's side, and that is the finding.** The register asks for
  the consumer action enum and the `SemiosisFrame.v1` schema, with closure evidence *"pinned schema and
  compatibility tests"* from the *"Abraxas consumer maintainer"*. Measured: **Abraxas has no
  `SemiosisFrame.v1` consumer at all.** The export exists (`semion/compat.py`, explicitly *"Export-only
  bridge"*), but nothing in this tree consumes it — so there is no consumer schema to conform to, and
  Semion's own `specs/contracts.md` already states the correct consequence: *"Unknown consumer schema:
  compatibility NOT_COMPUTABLE. A SemiosisFrame.v1 string alone proves no external schema conformance."*
  That is the honest answer, not a gap to fill by inventing a schema.

  **A name collision to know about before anyone wires it.** Abraxas *does* have an `action_type` field — in
  the evolution/self-build subsystem, with values like `param_override`, `implementation_ticket`,
  `HOLD_APPROVAL_FOR_REVIEW`. Semion's `action_type` means something else entirely (a closed enum of
  `STATE_UPDATE | ATTENTION_SHIFT | OUTPUT | NO_ACTION | NOT_COMPUTABLE`). Two vocabularies under one name,
  in a system where a name-based check cannot tell them apart: connecting them by field name would be a
  silent semantic error. Semion's own example export compounds it by carrying
  `"action_type": "STATE_UPDATE:alert"` — a value outside its own closed enum.
- **The five scaffolds:** ~~render the template, add the `compat/` package, then implement.~~
  **DONE this session** — all five rendered, specified, implemented and pushed, each with boundary tests.
  What remains for them is promotion, not construction: `chronos`, `resonance` and `aether` stay `planned`
  until Abraxas has an adapter for them (the engine repositories are not dependencies here, so no entry
  point resolves from this tree).
- **`noesis` / `semion`:** ~~decide whether they need standalone repos at all.~~ **Answered by the
  evidence: they already have them**, and substantial ones (`Noesis` 131 files / 36 commits; `Semion` 121 /
  39). `noesis`'s provider already lives in-tree (`abraxas/evidence/verifiers/latent.py`).

  `semion` now has the instrument the manifest said was missing — `abraxas/evidence/semion_instrument.py`,
  added this session. It **consumes** a `semion.sign.v1` frame and maps it to the canonical
  `EvidenceEnvelope`, refusing `semantic_truth` / `may_authorize` / `may_mutate_governing_state` frames and
  raising on promotion, mirroring `hyperlex_instrument`. It does **not** classify: the Semion repo's own docs
  declare the direction (*"Semion does not import Abraxas. Abraxas may consume this dict at
  RUNE.SEMIOSIS.CHAIN"*), so the classifier stays in that repository and a second one here would invert a
  declared dependency. `semion` remains `planned` for the same reason as `hyperlex` — an instrument is not a
  registered provider, and promotion is an authority decision, not a missing-code problem.

  **The stub it replaced is worth recording.** The test-only `SemionProvider` ignored its claim entirely and
  returned a hardcoded `answer="qualisign-rheme-icon"` at a fixed `confidence=0.85`: a rubber stamp that no
  downstream consumer could distinguish from evidence. Extracting *that* would have been the wrong
  completion, and the `planned` label was what held it back. Its two copies are still in
  `abraxas/evidence/test_semion_q1.py`; the instrument is the honest replacement, and the stub should be
  retired once Semion's own qualification gates are settled.
- **`oracle` / `cypher` / `aether`:** ~~put the directories under version control.~~ **DONE** — all three
  are now version-controlled with remotes, on `main`, with `.gitignore` and reviewed history.
- **`aether` (the only genuinely unfinished engine):** the manifest poses its own choice — *"Either build
  it or drop it from the architecture."* The repository is in the honest state for either branch. If
  **building**, the fusion policy comes before the encoders: encoders are mechanical, and the policy is
  where a laundered confidence would hide.
- **`athanor` (not Abraxas's to finish):** one unimportable tracked module, and 10 untracked sealed-run
  artifacts that its own convention says belong in `STATUS.md`. Both need its owner — see finding 5.
- **`hyperlex`:** the local `docs/pytrends-evidence-design` branch is superseded (its content is on
  `main`, which also carries the implementation). No PR needed; the branch can be deleted.
- **Every engine repo:** the defect class found in Abraxas is worth one guard in each tree — a
  parse-integrity test over tracked modules, so a file that cannot be imported cannot sit unnoticed. It was
  found in `abraxas/` and again in `athanor/`; two trees is a pattern, not a coincidence.

### Model-agnostic inference everywhere an engine needs a model (Complete) — session 2026-10-07

**Directive:** wherever an engine requires a model, it must go through a model-agnostic adapter; custom models
are a later capability and stay off the critical path. And: check whether the custom models actually work.

**Audit — which engines need a model.** Seven of ten need none, and each says why: `noesis` (consumes latent
captures handed to it), `trutina` (scores given forecasts), `cypher` (reads the memory layer), `chronos` and
`resonance` (rune and phase logic), `semion` (consumes a sign frame), `aether` (raises). Two do — `athanor`
and `oracle` — and now both resolve through `abraxas.evidence.adapters.model_agnostic`. Full table in
`docs/ENGINE_TOPOLOGY.md`.

**The custom models are absent, verified three independent ways:**

| Check | Result |
|---|---|
| weight files in any adapter dir on this machine | `0` |
| `git ls-files \| grep -c safetensors` in `~/Athanor` | `0` |
| `athanor.adapter_preflight` | `HOLD`, `weights_verified: false`, `training_authorized: false` |
| `... --model-dir t1_bias_corrected_adapter` | `INVALID` — "Missing, unsafe or oversized model config" |
| `specs/003-qwen-adapter/model-lock.json` | `"weight_downloaded": false` — `ENVIRONMENT_NOT_COMPUTABLE` |
| `EXECUTION-RECEIPT.md` | 2 of 7 artifacts present; **both weight files absent** |

`t1_bias_corrected_adapter/` is a freeze record, not a model: config + tokenizer, no weights, advertising
`"inference_mode": true`, naming a base (`Llama-3.1-Nemotron-Nano-8B-v1`) different from the spec beside it
(`Qwen3.8-27B`). Training ran on another host (`/home/delphi`, GB10). **"Broken" understates it: they were
never built.** The verdict is the repo's own, not an inference from a directory listing.

**Two defects fixed, same shape — a provenance field naming a model that produced nothing:**

- `_default_oracle_inference` (142 lines, deleted) built a `coherence_score` from word counts
  (`+= 0.1  # Sweet spot for coherence`) and published it as the envelope's **confidence**.
- Athanor reported `lora-out-transfer-001-t1/checkpoint-48`, and its default path **crashed**
  (`AttributeError: 'str' object has no attribute 'confidence'`) — the model-agnostic adapter had been wired in
  as the default and never executed, because every test injected a mock returning objects.
- `contract.py`'s default provenance named the same nonexistent checkpoint.
- The adapter's own callable announced `model-agnostic/unspecified` while stamping results
  `model-agnostic/offline-deterministic` — one state, two names.

**Rule now enforced:** a reading produced without a model carries `confidence=0.0` and
`provenance["inference"] == "offline-deterministic"`. The pair is the honest statement *here is a reading, and
nothing scored it*. An injected model keeps its own identity and confidences.

**Guards (both driven to fail before being trusted):** `tests/test_engines_name_no_model_they_do_not_have.py`
scans engine modules for checkpoint paths and hand-written model versions, with a counterfactual proving it
catches the exact strings removed here, plus an end-to-end check that unconfigured `oracle` and `athanor` both
report the offline path. `tests/test_console_declares_its_inference.py` holds the route and the console
template in agreement in both directions — a key the template reads that the route never sets renders as an
empty string, and an empty model identity reads as "no model", the exact ambiguity being ended.

**Also:** the operator console gained an Inference card, read live at render time, so it can no longer display
engine output while saying nothing about what produced it. `~/Oracle/SPEC.md` documented `oracle-model-v1`;
corrected. `~/Athanor`'s archived composition eval hardcoded `/home/delphi` paths and imported the model stack
first, so it died in `import torch` saying nothing about the adapter; it now checks for the artifacts and names
what is missing. Its `EXECUTION-RECEIPT.md` gained a verification note rather than an edit to its history.

**Ratchet:** 3768 passed, 0 failed, collected 3773 → **3779** (floor raised).

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