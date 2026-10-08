# Re-key the dependency manifest by (file, symbol) so a line shift stops invalidating it

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`,
and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository carries its own plan surface at `/Users/appliedalchemylabs/Abraxas/PLANS.md`
("AAL-Core Active Plan Surface"), an append-first execution queue. This ExecPlan must be registered
there as an active-queue entry, and that entry moved to `Completed` with a closure note when this work
finishes. This document is maintained in accordance with the ExecPlan methodology in the `execplan`
skill (`references/PLANS.md`, the Codex ExecPlan methodology), which is distinct from this repository's
own `PLANS.md`.

## Purpose / Big Picture

The file `.aal/dependency_manifest.v0.yaml` is the repository's record of **where** each
governance-relevant third-party dependency is used. For every dependency it lists one entry per import
statement, under `import_locations:`, and each entry carries four fields: the file `path`, the `line`
number, whether it is `top_level` (imported at module scope), and the `symbol` imported. A guard test,
`tests/test_dependency_import_locations.py`, keeps that record honest by comparing what the manifest
declares against what a fresh scan of the tree finds, in both directions.

The problem is the comparison key. The guard compares entries by **(file path, line number)**. That means
any edit that moves an import up or down — adding a docstring, a comment, or another import above it —
makes the record look wrong even though nothing about which dependency is used where has changed. This
is not hypothetical: on 2026-10-08 the guard failed because two imports had shifted down by exactly two
lines. `fastapi` was declared at `webpanel/panel_context.py:8` while the real import sat at `:10`, and
at `webpanel/routes/operator_routes.py:7` against a real `:9`. Nothing was undeclared; the numbers had
moved. A record that goes stale on every unrelated edit is a record people stop trusting, and a guard
that fires for the wrong reason is a guard people learn to ignore.

After this change the record is keyed on **(file path, symbol)** instead. Both parts survive a line
shift: the path never moves, and the symbol is derived from the text of the import statement, not its
position. A genuinely new import still shows up (its symbol is not declared), and a removed one still
shows up (its symbol is declared but no longer found). A line shift no longer shows up at all.

You can see it working with one experiment. Before this change, inserting two blank lines above the
`import fastapi` line in `webpanel/panel_context.py` makes the guard fail. After this change, the same
two blank lines leave it passing — while adding a real `import fastapi` to a file that does not declare
it still makes it fail.

## Progress

This section must always reflect the actual state of the work. Timestamps are UTC.

- [x] (2026-10-08 06:40Z) Phase 0 — baseline reproduced. The guard's comparison key was
      `(path, line)` in both `_sites_by_dependency()` and `_declared_sites()`; the fixer wrote and
      sorted by `line`. The declared `fastapi` entries for `webpanel/panel_context.py` were read from
      the manifest: `line 9, symbol HTTPException` and `line 10, symbol Jinja2Templates`. Scanner
      conventions confirmed (`_symbol_for`, `render_entries`).
- [x] (2026-10-08 06:55Z) Phase 1 — the guard is re-keyed to `(path, symbol)`, its `_sites_by_dependency`
      docstring now states the new rule and the residual limit, and the two failure messages print path
      and symbol. No manifest edit was needed: the declared symbols already matched the scan, so the
      stricter key exposed no pre-existing drift (`4 passed` immediately after the change).
- [x] (2026-10-08 06:55Z) Phase 2 — `render_entries()` sorts by `(path, symbol)`, with a comment
      recording why so it is not "simplified" back to `(path, line)`.
- [x] (2026-10-08 07:10Z) Phase 3 — validated, both directions. Counterfactual: two blank lines inserted
      above source line 9 (file sha `e2c31e9da901` -> `60e71b77eaa2`; the fastapi import moved to line
      11) gives OLD key `2 failed, 2 passed` and NEW key `4 passed`. Drift still fires both ways: an
      undeclared `import fastapi` appended to `abraxas/core/provenance.py` fails
      `test_every_import_site_is_declared`, and deleting the declared `from fastapi import ...` line from
      `webpanel/panel_context.py` fails `test_every_declared_site_still_uses_its_dependency`. Tree
      restored to `4 passed`.
- [x] (2026-10-08 07:20Z) Phase 4a — registered in `PLANS.md` and this ExecPlan committed and pushed as
      `baf45e77` (with the guard and fixer changes).
- [x] (2026-10-08 07:35Z) Phase 4b — CI proved the defect in production: run `37739497321` on
      `f69d3951` went red on this guard alone (`2 failed, 3879 passed`) because a sibling `except`
      narrowing in `abraxas/storage/compress.py` shifted the `zstandard` imports by seven lines. The
      re-key is the fix. While confirming that, the fixer's own `DRIFT` label was found to be a false
      alarm on position-only changes; it now uses the same `(path, symbol)` key as the guard, and the
      stale descriptive line numbers were refreshed with `--write` (the `(path, symbol)` sets verified
      byte-identical before and after).
- [ ] Phase 4c — awaiting confirmation: CI green on `baf45e77`, and `scripts/test_ratchet.sh` green.

## Surprises & Discoveries

- Observation: `symbol` is a representative symbol, not a unique site identifier. The scanner
  normalises every import statement to a single symbol: `import x as y` becomes `y`, `import x` becomes
  `x`, and `from m import a, b` becomes `a` (the first name only). So two imports in one file that
  normalise to the same symbol collapse to one entry, and adding a second name to an existing
  `from m import a` line is invisible to the key.
  Evidence: `_symbol_for()` in `scripts/reconcile_dependency_import_locations.py` returns
  `alias.asname or alias.name` for `ast.Import` and `node.names[0].name` for `ast.ImportFrom`, and the
  module docstring states the convention: "One entry per import STATEMENT, not per imported name."

- Observation: the fixer is not the thing that broke. The guard compares declared against scanned
  entries; the fixer regenerates entries from a scan. The fixer *writing* a line number is harmless —
  the defect is the guard treating that number as identity. This is why the minimal fix touches the
  guard's key, not the manifest's schema.
  Evidence: `render_entries()` and `declared_entries()` both emit a `line:` field; the assertions in
  `tests/test_dependency_import_locations.py` are what compare `{(path, line)}` sets.

- Observation: because the fixer sorts rendered entries by `(path, line)`, running it after a pure
  line shift would reorder entries as well as renumber them, making the diff noisier than the change
  warrants.
  Evidence: `render_entries()` sorts with `key=lambda s: (s[0], s[1])`, i.e. `(path, line)`.

- Observation: the first attempt at the DRIFT B negative control was a **no-op that looked like a
  pass**. The probe replaced the literal text `import fastapi`, but the real site in
  `webpanel/panel_context.py:9` is `from fastapi import HTTPException, Request` -- the substring
  `import fastapi` does not occur there. The file was therefore unmodified and
  `test_every_declared_site_still_uses_its_dependency` passed, which reads as "the guard failed to
  notice a stale declaration". It had noticed nothing because nothing had changed. Re-run against the
  real line (delete `from fastapi import ...`), the test fails as required.
  Evidence: first run `1 passed`; after targeting the real line, `1 failed` at
  `tests/test_dependency_import_locations.py:135`.

- Observation: the counterfactual's own insertion helper had the same defect shape and reported a
  blank line number while still working by accident of a broader match. It was re-done by asserting
  on `lines[8].startswith('from fastapi import')` and inserting by index, with the file sha printed
  before and after, so the shift is proved rather than assumed.
  Evidence: sha `e2c31e9da901` -> `60e71b77eaa2`, `from fastapi import` moved from line 9 to line 11.

- Observation: the first ratchet run reported `failures=3` with three collection `ERROR`s
  (`test_acquisition_perf_ledger.py`, `test_manifest_discovery.py`, `test_manifest_parse.py`) that
  look exactly like a regression introduced by this change and are not one. All three fail with
  `ModuleNotFoundError: No module named 'defusedxml'` -- a dependency the repo *declares* in its `dev`
  extra (`pyproject.toml:100`) but which was absent from the interpreter the ratchet runs under
  (`~/.hermes/tools/python-3.14.7.../bin/python`). Running the same three files under the scratch venv
  gives `10 passed`. The interpreter gap, not the code, was the cause; installing `defusedxml` into the
  tools interpreter returned the ratchet to `failures=0`.
  Evidence: tools interpreter -> `3 errors`; scratch venv -> `10 passed`; after
  `python -m pip install defusedxml`, ratchet green.

- Observation: the ratchet's preflight (`scripts/test_ratchet.sh:47`) checks only that `core` resolves to
  this repository -- it does not check that the declared dependencies are installed. So a wrong-package
  environment passes preflight and then presents as collection errors, which is the same shape as the
  bug this plan fixes: an instrument reporting an outcome ("a regression") it has not actually
  established.
  Evidence: preflight passed and the run still produced 3 errors, all one missing import.

- Observation: the brittleness this plan exists to remove was then **demonstrated by CI, not
  constructed**. Commit `f69d3951` (a sibling change narrowing a broad `except` in
  `abraxas/storage/compress.py`) expanded one handler into a four-tuple with an explanatory comment,
  shifting the two `zstandard` imports in that same file down by seven lines. CI run `37739497321`
  went red with `2 failed, 3879 passed` -- both failures were this guard, reporting
  `zstandard: abraxas/storage/compress.py:137 is declared but does not use it` against a real `:144`,
  and `:176` against a real `:183`. Nothing about which dependency is used where had changed; a
  comment had grown. The preceding commit `8604bf41` passed CI, so the red run is attributable to that
  one edit. This is the identical failure shape as the 2026-10-08 `fastapi` off-by-two, produced by a
  different author-in-the-loop within the hour, which is the strongest argument available that the key
  -- not the occasional carelessness -- was the defect.
  Evidence: `gh run view 37739497321 --log-failed`; the re-key commit `baf45e77` returns the guard to
  green with no manifest change.

- Observation: the fixer's own report was misleading in the same way, and fixing the guard exposed it.
  With the guard re-keyed, `python scripts/reconcile_dependency_import_locations.py` still announced
  `DRIFT in 4 dependenc(ies)` while printing `cryptography: 4 declared -> 4 actual`,
  `fastapi: 46 declared -> 46 actual` -- equal counts, so the SET of sites was unchanged and only the
  line numbers had moved. "DRIFT" there asserts a discrepancy the number underneath it contradicts.
  The fixer now compares the same `(path, symbol)` key the guard uses: a set change is `DRIFT` and
  exits 1; a position-only change is reported as stale descriptive data and exits 0.
  Evidence: before -> `DRIFT in 4 dependenc(ies)` with equal counts; after -> `4 dependenc(ies) with
  stale line numbers (descriptive only)`, exit 0, and a real added site still reports
  `DRIFT in 1 dependenc(ies) -- the SET of sites changed` with exit 1.

## Decision Log

- Decision: the comparison key becomes `(path, symbol)` rather than `path` alone.
  Rationale: `path` alone is maximally robust to edits but loses per-import sensitivity — a new import
  added to a file that is already declared for that dependency would not be noticed at all. `(path,
  symbol)` keeps that sensitivity, because a genuinely new import contributes a symbol the manifest
  does not carry, while remaining immune to the line shift that caused the false failures. The whole
  point of the record is to notice a surface that exists; dropping to `path` alone would weaken the
  instrument to fix a presentation problem.
  Date/Author: 2026-10-08, Bob Vajeen.

- Decision: keep the `line:` field in the manifest as descriptive metadata, and stop comparing it.
  Rationale: the line number is genuinely useful to a human who wants to jump to the site, and it is
  cheap to keep. The defect was never that the number exists; it was that the guard treated it as part
  of the site's identity. Deleting it would lose a real affordance to buy no additional safety, since
  the guard is the thing that enforces the record.
  Date/Author: 2026-10-08, Bob Vajeen.

- Decision: change the fixer's rendered-entry sort key from `(path, line)` to `(path, symbol)`.
  Rationale: this makes the generated block stable in order, so when the fixer does run, a line shift
  cannot reorder entries and the diff shows only the numbers that actually changed. It is a
  two-character change with no behavioural risk to the surgical splice, which keys off the
  `import_locations:` header and the `      ` indent, not the sort order.
  Date/Author: 2026-10-08, Bob Vajeen.

- Decision: accept and document the residual limitation rather than engineering around it.
  Rationale: `(path, symbol)` cannot see a second name added to an existing `from m import a, b` line,
  because the scanner reports one symbol per statement. Closing that would mean keying on the full
  imported-name set per statement, which changes the manifest's documented convention
  ("one entry per import STATEMENT") and is a larger schema change than the defect warrants. The honest
  move is to record the limit in this plan and in the guard's docstring, not to imply the key is exact.
  Date/Author: 2026-10-08, Bob Vajeen.

## Outcomes & Retrospective

**Outcome, against the Purpose.** A line shift no longer invalidates the dependency record. The guard
now keys on `(path, symbol)`, and the identical tree that the old key rejected (`2 failed`) the new key
accepts (`4 passed`). Both drift directions still fire: an undeclared site fails
`test_every_import_site_is_declared`, and a removed declared site fails
`test_every_declared_site_still_uses_its_dependency`. So the instrument is now strict about what it is
for (which dependency is used where) and silent about what it is not for (where on the page that
import happens to sit). No manifest entry changed — the symbols were already correct; only the key
that compares them was wrong.

**What remains, stated honestly.** The residual limit in the Decision Log is real: the key cannot see a
second name added to an existing `from m import a, b` line, because the shared scanner attributes one
symbol per statement. That is the honest boundary of a static scan keyed on a representative symbol, and
it is documented in the guard's docstring rather than left for a future reader to discover.

**Lessons, each earned by a specific failure in this plan.**

*A key is a claim about identity, and it must be chosen for what is invariant.* The bug was not that
line numbers exist — it is that they were treated as identity. The fix was to ask which properties of a
site survive the edits that happen constantly (path, symbol) and which do not (line), and to key on the
former while keeping the latter as description.

*A negative control that edits nothing reads exactly like a guard that notices nothing.* The first
DRIFT B probe replaced `import fastapi`, a string that does not occur in the file, so the file was
untouched and the test passed — indistinguishable, in the output, from a guard that had failed to catch
a real stale declaration. Only re-running against the real line, and printing the file's hash before and
after, separated the two. Both probe failures here were the same shape as the bug being fixed: something
reporting an outcome it had not actually produced.

## Context and Orientation

This repository is a Python project rooted at `/Users/appliedalchemylabs/Abraxas`.

The **manifest** is `.aal/dependency_manifest.v0.yaml`. It is YAML. Its top level has a `dependencies:`
mapping; each key is a dependency's import name (for example `fastapi`), and each value has a `class`
(one of `CORE_REQUIRED`, `ENTRYPOINT_REQUIRED`, `OPTIONAL_ADAPTER`, `DEV_TEST_ONLY`, `LEGACY_DEPRECATED`)
and a list of **import sites** under `import_locations:`. One site looks like this:

    - path: webpanel/panel_context.py
      line: 10
      top_level: true
      symbol: fastapi

A **governance-relevant dependency** is one whose `class` is in
`("CORE_REQUIRED", "ENTRYPOINT_REQUIRED", "OPTIONAL_ADAPTER")` — the tuple `GOVERNANCE_CLASSES` in the
fixer. `DEV_TEST_ONLY` is deliberately excluded because `pytest` alone appears in hundreds of files.

The **guard** is `tests/test_dependency_import_locations.py`. It has four tests. Two are instrument-health
checks (the scan finds sites at all; the scan sees string-based `require_optional_dependency("x")`
guards). The two that matter here are the drift assertions:

    test_every_import_site_is_declared                 # scanned - declared is empty
    test_every_declared_site_still_uses_its_dependency # declared - scanned is empty

Both build sets through two helpers, `_sites_by_dependency()` (from the scan) and `_declared_sites(dep)`
(from the manifest), and these are the only lines that need to change. The file header explains why the
scanner is imported from the fixer rather than reimplemented: two definitions of "an import site" would
drift apart, and the fixer and its guard would then disagree about the very thing being guarded.

The **fixer** is `scripts/reconcile_dependency_import_locations.py`. Running it without `--write` reports
drift and exits 1; with `--write` it rewrites only the entry lines under each dependency's
`import_locations:`, preserving every other byte. Its `scan_import_sites()` returns
`{import_root: [(path, line, top_level, symbol), ...]}`.

Terms used in this plan, defined plainly: an **import site** is one import statement, or one literal
`require_optional_dependency("x", ...)` / `import_module("x")` call. A **symbol** is the single name the
scanner attributes to a statement. A **line shift** is any edit above an import that changes that
import's line number without changing what it imports.

## Plan of Work

Phase 1 changes two helper functions in `tests/test_dependency_import_locations.py` and their
docstrings. `_sites_by_dependency()` currently returns `{dep: {(path, line)}}`; it must return
`{dep: {(path, symbol)}}`, which means unpacking the symbol that `scan_import_sites()` already provides
instead of the line. `_declared_sites(dep)` currently returns `{(str(entry["path"]), int(entry["line"]))}`;
it must return `{(str(entry["path"]), str(entry.get("symbol", "")))}`. The docstring on
`_sites_by_dependency()` currently says the site is compared "by path and line ... never the declared
symbol, which is descriptive" — that sentence is now exactly backwards and must be replaced with the new
rule and the reason: the symbol is compared because it survives a line shift; the line is descriptive
because it does not. The two failure messages interpolate `{path}:{line}`; they must keep showing a
location a human can use, so they should print the path and symbol (and the line where the manifest has
one) rather than a bare pair.

Phase 2 changes one line in `scripts/reconcile_dependency_import_locations.py`: the sort key inside
`render_entries()` goes from `(s[0], s[1])` (path, line) to path-then-symbol. A one-line comment records
why, so the next reader does not "simplify" it back.

No change is made to the manifest's schema, to `scan_import_sites()`, to the surgical splice, or to the
manifest file itself. The four-field entry stays as it is.

## Concrete Steps

All commands run from `/Users/appliedalchemylabs/Abraxas`.

The interpreter matters in this environment. A bare `python3` can resolve a foreign checkout through a
stale editable install. Select the toolchain interpreter explicitly:

    PY=$(ls -d /Users/appliedalchemylabs/.hermes/tools/python-3.14*/bin/python3 | head -1)
    "$PY" -V

Expected: `Python 3.14.7`.

Run the guard on its own while developing:

    "$PY" -m pytest tests/test_dependency_import_locations.py -q --no-header

Expected after the change: `4 passed`.

Never use `git add -A` or `git add .` in this repository: `out/`, `data/`, `.aal/`, and `.abraxas/` are
tracked but rewritten by every test run, so a blanket add stages hundreds of generated files. Stage
explicit paths only, and verify with
`git diff --cached --name-only | grep -cE '^(out/|data/|\.abraxas/|\.aal/)'` returning `0`.

A `git push` in this repository has hung and been killed at its timeout, leaving the commit local while
the remote stayed behind. Push in the background, then verify by comparing `git rev-parse HEAD` against
`git ls-remote origin main`; do not conclude a push landed merely because the command returned.

## Validation and Acceptance

Acceptance is behaviour a human can check at a terminal, in three parts.

**One — the false failure is gone (the counterfactual).** Reproduce the line shift that caused the
original failure, and confirm the guard now tolerates it:

    cp webpanel/panel_context.py /tmp/pc.bak
    # insert two blank lines immediately above the `import fastapi` line
    "$PY" -m pytest tests/test_dependency_import_locations.py -q --no-header
    cp /tmp/pc.bak webpanel/panel_context.py

Before this change, that edit makes `test_every_import_site_is_declared` and
`test_every_declared_site_still_uses_its_dependency` fail with the "off by two lines" message. After the
change, both pass. This must be observed in both directions — fail with the old key, pass with the new
one — or the change has not been shown to do anything.

**Two — both drift directions still fire.** Weakening a guard is worse than not having one, so the new
key must still catch real drift:

    # undeclared: add `import fastapi` (a new symbol) to a file the manifest does not list
    # stale:      remove an import that the manifest does list for that dependency

In each case the corresponding test must fail. If neither fails, the key is too weak and the change
must be reconsidered.

**Three — the suite is green.** Run the repository's ratchet, which enforces both a failure floor and a
collected-test floor:

    bash scripts/test_ratchet.sh

Expected final lines:

    failures=0 baseline=0  collected=N floor=N
    OK: within baseline
    RATCHET_EXIT=0

## Idempotence and Recovery

This is a comparison-key change with no data migration, so every step is safe to repeat. The manifest
file itself is untouched. The only risk is a half-applied edit across the two files; recovery is
`git checkout -- tests/test_dependency_import_locations.py scripts/reconcile_dependency_import_locations.py`
and re-applying. Do not modify source to satisfy a checker: if a guard fails, fix the guard or fix the
code the guard is complaining about, never the wording of the code the guard reads.

## Artifacts and Notes

The original failure this plan exists to remove, as reported by the guard before the re-key (declared
line first, real line second):

    fastapi: webpanel/panel_context.py:8  is declared but does not use it
    fastapi: webpanel/panel_context.py:10 uses it but is not declared
    fastapi: webpanel/routes/operator_routes.py:7  is declared but does not use it
    fastapi: webpanel/routes/operator_routes.py:9 uses it but is not declared

The scanner's symbol convention, verbatim from the fixer's module docstring:

    - One entry per import STATEMENT, not per imported name.
    - `symbol` follows the existing convention: `import x as y` -> `y`, `import x` -> `x`,
      `from m import a, b` -> `a` (the first name).

## Interfaces and Dependencies

No new third-party dependency is introduced. The change stays inside two existing files.

At the end of Phase 1, in `tests/test_dependency_import_locations.py`, the helpers must have these
shapes:

    def _sites_by_dependency() -> dict[str, set[tuple[str, str]]]:
        """{dependency: {(path, symbol)}} -- one scan, shared by every assertion below."""

    def _declared_sites(dep: str) -> set[tuple[str, str]]:
        """{(path, symbol)} declared for `dep` in the manifest."""

At the end of Phase 2, in `scripts/reconcile_dependency_import_locations.py`, `render_entries()` must
sort its input by `(path, symbol)`:

    for path, line, top_level, symbol in sorted(sites, key=lambda s: (s[0], s[3])):

---

*Change note (2026-10-08).* This plan was created after the defect was diagnosed during the
open-issues remediation, so Phases 0-3 were implemented and validated in the same pass and carry
measured evidence rather than intentions; Phase 4 (the ratchet confirmation and the `PLANS.md`
registration) is the only part left open at the time of writing. The decision to keep the `line:` field
as descriptive metadata instead of deleting it — and the residual limit that the key cannot see a second
name added to an existing `from m import a, b` line — are recorded in the Decision Log and the Outcomes
section rather than left implicit.
