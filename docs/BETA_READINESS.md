# Beta readiness — Abraxas

**Assessment date**: 2026-10-08 · **Assessed at**: `main` @ `147893e2`
**Verdict**: **not beta-ready at the time of assessment** — but the gap was *release engineering and
claim integrity*, not the core system. The code was substantially stronger than its documentation
claimed; the release process was substantially weaker.

Every figure below is measured, with the command that produces it. Where a judgement is involved it
is marked **[JUDGEMENT]**.

---

## Scorecard

| # | Dimension | Status | Evidence |
|---|---|---|---|
| 1 | Test suite substance | 🟢 Strong | `3806` collected · `3797` passed · `9` xfailed · `0` failed · ratcheted floor `3779` local / `3850` CI |
| 2 | CI actually runs the tests | 🟠 **Young — 1 day** | Before `7a3a2abf` (2026-10-07) CI's pytest scope was `tests/evidence tests/integration tests/chaos webpanel`; **`tests/` (680 files) was never in it** and a full-suite command appeared in the workflow **zero** times |
| 3 | Coverage measured | 🟡 63%, was **ungated and unmeasured** | `74840` statements / `27849` missed. `[tool.coverage]` was fully configured and CI installed `pytest-cov`, but no workflow ever passed `--cov` |
| 4 | Security posture | 🟡 Fixed, **unreleased** | Strong fail-closed design (`659` `not_computable` refs, **0** bare `except:`); this week's real fixes all sit in CHANGELOG *Unreleased* |
| 5 | Release/version integrity | 🔴 → 🟢 **fixed** | **Five** disagreeing versions: pyproject `1.5.0` · canon `v2.0.1` · README badge `v2.0.1` · README module `v2.0.5` · `abx` `0.1.0-orin-spine`. No `abraxas.__version__` existed at all |
| 6 | Dependency reproducibility | 🔴 → 🟢 **fixed** | All **11** runtime deps were lower-bound-only; a pydantic/numpy/cryptography major could land on any install |
| 7 | Claims vs reality | 🔴 → 🟢 **fixed** | README declared "PRODUCTION READY — All systems operational" **twice, verbatim** while the package classifier said `Development Status :: 3 - Alpha`; claimed 3,548 tests vs measured 3,806 |
| 8 | Observability | 🟢 **Not a gap — measured** | 863 `print()` repo-wide, but the breakdown matters: `abraxas/cli` (322) and `abx` (217) are command-line surfaces where printing IS the output mechanism, and the served surfaces are clean (`abraxas/dashboard` 6, `webpanel` 0, `abraxas/api` 0). The two packages previously named as gaps are not: `abx`'s 217 prints are its CLI interface (87 of 90 files are argparse scripts) and `abraxas/zkp`'s 134 sit in code with no production importers |
| 9 | Deployment artifacts | 🟢 Adequate | `Dockerfile.dashboard-api` · `dashboard/frontend/dist` · `docs/runbooks/operational_procedures.md` · `.env.example` (17 vars) |
| 10 | Governance & self-diagnosis | 🟢 **Differentiator** | canon / runes / promotion gates / manifests / ratchets; `abx doctor`, `smoke`, `acceptance` all live |

## The estimate

| | Readiness |
|---|---|
| Core capability & tests | ~70% |
| Release engineering | ~30% → raised by this pass |
| Process assurance (CI history) | ~45% |
| Claim integrity (docs/metadata) | ~35% → raised by this pass |
| **Overall for a public beta** | **~50–55%, 2–3 focused weeks** **[JUDGEMENT]** |

## Blockers

### Resolved in the 2026-10-08 pass

1. **Version identity** — `pyproject.toml` now declares `2.0.1`, matching canon authority
   (`.abraxas/gates.json` → `gates.CANON_VERSION`), the README badge and the CHANGELOG milestone.
   `abraxas/__init__.py` gains `__version__`, read back from installed distribution metadata rather
   than a second hardcoded copy. `tests/test_version_single_source.py` fails if the four drift.
2. **README truth** — the duplicated "🚀 Production Status" block (two verbatim copies) is gone;
   "PRODUCTION READY" is replaced by the measured state and an explicit *"What is honestly not
   ready"*, cross-referencing the README's own maturity matrix.
3. **Coverage gate** — `fail_under = 60` in `[tool.coverage.report]`, and CI now runs the suite
   under `--cov` (it never did). Verified enforced by pytest-cov, not assumed: a 3-test subset
   reports 1.09% and exits 1 against the floor.
4. **Dependency bounds** — all 11 runtime deps carry an upper bound. Caps were chosen so the
   versions already installed and passing CI still satisfy them; an upper bound that forces a
   resolution change is a different, larger change.
5. **Packaging metadata** — added `license = {text = "MIT"}` (the file existed but packaging
   declared nothing) and `Programming Language :: Python :: 3.12`, which CI runs and which no
   classifier mentioned.

### Open

6. **Ship the security fixes.** They are written and verified — `0.0.0.0` bind → loopback, the
   **fail-open token comparison**, `eval` on generated content → `ast.literal_eval`, `xml.etree` →
   `defusedxml` — and they are all in CHANGELOG *Unreleased*. This is a release action, not a code
   action.
7. **Earn CI history.** The full suite has **one day** of genuine CI coverage. A green badge with no
   history is not assurance; keep it green across real merges before declaring beta.
8. **Observability — CORRECTED TWICE (2026-10-08).** The first version of this entry said "863
   `print()` calls on the served surface", which was wrong: the served surface has six. The second
   version named `abx` and `abraxas/zkp` as "the real gap", which is also wrong, and measured so:
   `abx/` is 217 prints across 90 files, and **87 of those 90 files are standalone CLI scripts**
   with `argparse` plus `main()`, so the prints *are* the operator interface. Converting them would
   make `abx kernel invoke <module>` harder to use and buy nothing. `abraxas/zkp/` is 134 prints in
   four files whose backend factory functions **have zero production importers**; the 28 prints on a
   library path are error handlers in code that production never reaches. There is also no
   repo-wide logging convention to align with (`abx/` uses a custom JSON logger at
   `abx/util/logging.py`, `abraxas/` uses stdlib `logging`), so a stdlib conversion inside `abx/`
   would add a third mechanism rather than settle on one.
   [JUDGEMENT] Not an observability gap. The only prints genuinely wrong by any standard are the
   ~28 `abraxas/zkp` error handlers, and they are unreachable. Revisit if production code ever
   imports a ZKP backend, at which point converting those three files becomes the correct fix.
   Five tests capture stdout from CLI entrypoints (`tests/test_sources_runtime.py:130,180,214`,
   `tests/test_tier3_path_containment.py:8`, `tests/test_shadow_promotion_pack_containment.py:10,19`)
   and would break under a conversion that touched the CLI contract.
9. **Stale tags — RESOLVED (2026-10-08).** `v4.0.0` and `v4.0.2` were dated 2026-10-03, **older
   commits with higher numbers** than `v2.0.0` (2026-10-04), from an abandoned numbering scheme.
   Local and remote tags deleted, after confirming nothing references them: the only consumer
   declaration in the repo is an unpinned git dependency that resolves to the default branch. The
   remote now carries `v2.0.0` and `v2.1.0` only, both on the canon line. `v2.0.0` was deliberately
   KEPT: it is the canon predecessor (`v2.0.0` -> canon `v2.0.1` -> `v2.1.0`), not stray.

### Found during the assessment, since resolved

All four were fixed in the reconciliation pass that followed this assessment:

- **`abraxas/__init__.py` monkeypatched `pathlib.Path.read_text` at import time**, shipping a
  mutated stdlib class to every consumer. Moved to `tests/conftest.py`, where it only affects the
  test session. `9b771feb`.
- **`replit.md`** described a different product. Archived to
  `docs/archive/replit-not-this-product.md`, as was `PR_DESCRIPTION.md`, which still reported a
  phase as "50% Complete". Both were checked for consumers first: nothing referenced either.
  `95fe2a1a`.
- **`ROADMAP.md`** sections were labelled Q1-Q4 2025 while the assessment date is Q4 2026. The
  labels are removed rather than replaced, because the true quarter is not something the
  repository states. `95fe2a1a`.
- **Test modules inside the source package** were distributed to consumers. Measured at 34 across
  three directories, not the 5 first estimated. **Ratcheted at 34, not fixed**: three mechanisms
  (a setuptools `exclude`, `include-package-data = false`, and deleting the stale `build/`
  directory) were each tested against a rebuilt wheel and none moved the count. Root cause is
  unresolved in setuptools internals and the value at stake is package bloat rather than
  breakage. `912161f4`.

### Still open, measured and deliberately declined

- **`out/` holds fixtures and run outputs in the same tree.** 178 tracked files, 120 of them dirty
  after a run, and **61 test files read tracked `out/` files as inputs**. Untracking the outputs
  would break those tests, and a "a run must not dirty tracked files" guard would fail forever
  because the files tests assert against are the ones runs rewrite. The real fix is separating
  fixtures from outputs structurally. Not a hygiene task.

## The decision that sets the date

**DECIDED 2026-10-08: beta means (A), the operator-supervised shadow beta.**

## Beta 1 scope declaration (2026-10-08)

**IN SCOPE:** the operator-supervised shadow beta. The system observes, forecasts and reports; it
does not autonomously act and does not mutate the canon. Release mechanics are done (`v2.1.0`
shipped). The remaining gate is CI history, which is wall-clock rather than work.

**EXPLICITLY OUT OF SCOPE for beta 1:** `empirical` and `economic` settlement on any engine.

Why this is a declaration and not merely a deferral. Both levels are *defined but unimplemented*.
The doctrine names their criteria (`docs/DOCTRINE.md:49-53`) and the dataclass carries their fields
(`abraxas/engines/settlement.py:28-41`), but no survey measures them, no harness evaluates them, no
test corroborates a claim about them, and nothing reads their evidence fields. `technical`
settlement, by contrast, is fully mechanized and guarded by a corroboration test that refuses any
claim the survey cannot measure. Declaring a level settled with no mechanism behind it is the exact
failure the technical-settlement infrastructure exists to prevent, so the honest position is to
leave both `unsettled` and say so out loud.

**WHO CLOSES IT:** the operator, by defining what evidence constitutes each level and who evaluates
it. That is a governance act, not an engineering task, and satisfying it means building a second
measurement pipeline of scope comparable to the technical one.

**WHAT BRINGS IT BACK IN SCOPE:** any beta that a party other than the operator relies on. The
shadow-only design mitigates the absence of empirical settlement for an operator-supervised beta. It
does not mitigate it for an unsupervised one.

This is not a maturity claim: the package classifier stays `Development Status :: 3 - Alpha` on
purpose, and the flip criterion is written in `pyproject.toml` next to the classifier.

**Guard:** `tests/test_beta_scope_declaration.py` fails if this declaration disappears, or if any
engine declares an `empirical` or `economic` settlement the pipeline cannot measure.

### Superseded: the earlier framing of this section

**[JUDGEMENT]** The blockers above are scope-independent. What is *not* is what "beta" means,
because the system is **shadow-only by design** — README: *"STILL NOT live autonomy… no live
autonomy, no Canon mutation"* — and **all ten engines remain deliberately `unsettled`** (5 live at
83–93%, 5 planned at 55–65%, per `KANBAN.md`'s Engine Completion Audit).

- **Operator-supervised shadow beta** → the resolved blockers were the bulk of the work; path to
  beta is days.
- **Public / live beta** → the gate is the engine settlements. That is a governance decision, not
  an engineering one, and it is the operator's to make.

**Correction to the figures above.** The engine scores read "5 live at 83-93%" when this
assessment was written. The KANBAN table was a stage behind its own survey: all five live engines
corroborate all seven integration criteria, so the true figures are **5 live at 90-100%**, 5
planned at 55-65%. Corrected in `3b47ca13`, and now guarded by
`tests/test_engine_table_matches_survey.py`.

## Method

Measurements were taken at `147893e2` on 2026-10-08. Coverage was produced by a full-suite
`pytest --cov` run (63%; 74,840 statements). CI facts come from the workflow files and from `gh run
view` on the relevant runs. Version facts come from `pyproject.toml`, `.abraxas/gates.json`,
`README.md`, `CHANGELOG.md` and `git tag`. Test counts come from the repo's own ratchet
(`scripts/test_ratchet.sh`) and from CI's `Verify test count` step.

Two claims in this document were corrected before publication, both by measurement rather than
review: the version-authority lookup in the new test initially read `CANON_VERSION` off the root of
`gates.json` (it is nested under `gates`), and the `v4.0.x` tags were initially assumed to point
outside `main`'s history (all three are ancestors).
