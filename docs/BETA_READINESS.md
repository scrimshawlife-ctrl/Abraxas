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
| 8 | Observability | 🔴 Weak | `863` bare `print()` vs `156` logging calls — no levels, no routing, no structured logs |
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
8. **Observability.** `863` `print()` calls on the served surface. [JUDGEMENT] Not a blocker for an
   operator-supervised shadow beta; a blocker for anything operated by someone else.
9. **Stale tags.** `v4.0.0` and `v4.0.2` are dated 2026-10-03 — **older commits with higher
   numbers** than `v2.0.0` (2026-10-04). All three are ancestors of `main`, so they are harmless but
   ambiguous. Retiring them is an operator action (published tags are history).

### Found during the assessment, outside the blocker list

- **`abraxas/__init__.py` monkeypatches `pathlib.Path.read_text` at import time** to fall back to
  repo-relative `tests/fixtures/` paths. A shipped library mutating a stdlib method for a test
  convenience affects every consumer, not just this repo. Should move to a test `conftest.py`.
- **`replit.md`** describes "a mystical trading application" that does not match this repository.
- **`ROADMAP.md`** sections are dated Q1–Q4 **2025** while the assessment date is Q4 2026.
- **`abraxas/evidence/test_hyperlex_q1.py`** is a test module living inside the source package.

## The decision that sets the date

**[JUDGEMENT]** The blockers above are scope-independent. What is *not* is what "beta" means,
because the system is **shadow-only by design** — README: *"STILL NOT live autonomy… no live
autonomy, no Canon mutation"* — and **all ten engines remain deliberately `unsettled`** (5 live at
83–93%, 5 planned at 55–65%, per `KANBAN.md`'s Engine Completion Audit).

- **Operator-supervised shadow beta** → the resolved blockers were the bulk of the work; path to
  beta is days.
- **Public / live beta** → the gate is the engine settlements. That is a governance decision, not
  an engineering one, and it is the operator's to make.

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
