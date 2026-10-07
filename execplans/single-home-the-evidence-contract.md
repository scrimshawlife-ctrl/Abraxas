# Single-home the evidence contract, then measure the settlement criteria

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`,
and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository carries its own plan surface at `/Users/appliedalchemylabs/Abraxas/PLANS.md`
("AAL-Core Active Plan Surface"), an append-first execution queue. This ExecPlan must be registered
there as an active-queue entry, and that entry must be moved to `Completed` with a closure note when
this work finishes. This document is maintained in accordance with the ExecPlan methodology in the
`execplan` skill (`references/PLANS.md`, the Codex ExecPlan methodology), which is distinct from this
repository's `PLANS.md`.

## Purpose / Big Picture

Every engine in Abraxas -- the components that actually do reasoning -- reports its findings through
one shared shape called an **evidence envelope**: a record carrying the claim, the candidate outputs,
the confidence, and the provenance of where the answer came from. Abraxas itself owns arbitration;
engines own reasoning. That boundary is expressed by the envelope type.

Right now that boundary type exists **twice**, and the two copies are not the same object. A caller
that checks "is this an evidence envelope?" using one copy receives a real engine's output and is told
**no**. Nothing in the test suite notices, because the only conformance check asks whether a class
inherits from a base class, never what its output actually is.

After this work, there is exactly one evidence envelope and exactly one provider interface in the
repository, every live engine returns that single envelope, and two new guards fail loudly if either
copy is ever reintroduced or if an engine returns a bare dictionary again. Then, because all five live
engines finally return a uniform shape, a measurement harness can run each of them twice on identical
input and report whether it is deterministic and whether it carries provenance -- which is what the
settlement records added previously were waiting on.

You can see it working by running two commands. First, one Python line that must print `True`:

    python3 -c "from abraxas.evidence import EvidenceEnvelope as A; \
    from abraxas.evidence.contract import EvidenceEnvelope as B; print(A is B)"

Second, the settlement survey, which must show real `yes`/`no` values in the run-required columns
instead of `?` for the five live engines:

    python3 scripts/survey_engine_settlements.py

## Progress

This section must always reflect the actual state of the work. Timestamps are UTC.

- [x] (2026-10-06) Phase 0 -- baseline captured: ratchet green at `3514 passed, 4 skipped, 9 xfailed`,
      `collected=3525 floor=3525`; the four duplicate definitions recorded with file:line evidence; the
      three tracked `.bak` files listed; and the import-site count measured (the honest answer is
      **zero** -- nothing imports `EvidenceEnvelope` or `EvidenceProvider` from the package level).
- [x] (2026-10-06) Phase 1 -- `EvidenceEnvelope` single-homed on `abraxas/evidence/contract.py`; the
      package `__init__` re-exports rather than redefines; the divergence resolved by **promoting**
      `schema_version` to the canonical envelope (the first attempt deleted it, which silently broke
      migration idempotence -- see Surprises). A 6-test guard file now covers identity, the field list,
      serialization, and migration idempotence, and the idempotence test has been observed failing.
- [x] (2026-10-06) Phase 2 -- `EvidenceProvider` single-homed (all 11 consumers already imported from
      `abraxas.evidence.provider`; zero consumers used the package copy). `RelationStep`,
      `CandidateOutput`, `EvidenceType`, and `create_athanor_envelope` also single-homed on
      `abraxas/evidence/contract.py`. `latent.py` now returns `EvidenceEnvelope` (not `dict`). A
      return-type guard over all 5 LIVE engines added and observed failing against the reverted fix.
      Full suite TBD.
- [x] (2026-10-06) Phase 3 -- `Decision` single-homed on `abraxas/evidence/contract.py` (the package
      copy lacked `REJECT`; `A is B` now `True`). Generalized identity guard added as parametrized test
      in `tests/test_evidence_contract_single_home.py` covering all 6 contract types (EvidenceEnvelope,
      EvidenceProvider, RelationStep, CandidateOutput, EvidenceType, Decision). Both the Decision guard
      and the generalized parametrized guard observed FAILING when a local duplicate was reintroduced,
      then passing once removed. Full suite TBD. Guard file: 12 tests (was 6).
- [x] (2026-10-06) Phase 4 -- the three tracked `.bak` files removed with `git rm`. Verified inert
      before removal: nothing in `abraxas/tests/tools/scripts` references them, and none is loadable as a
      module (`.bak` is not a Python extension, so pytest never collected them). Note that
      `__init__.py.bak` was not a backup at all -- it was a stray 51-byte single-line fragment
      (`INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"`). That member is live at
      `abraxas/evidence/__init__.py:44` and `:339` and asserted by
      `tests/evidence/test_evidence_contract.py:338`, so nothing was lost. Removals remain recoverable
      from history (last carrying commit `3694394f`).
- [x] (2026-10-06) Phase 5 -- execution harness `abraxas/engines/execution_harness.py` created with
      `NON_CONTENT_FIELDS`, `run_once`, `measure`. Wired into `scripts/survey_engine_settlements.py`
      (lines 149-156 replaced with a live-engine branch that calls `measure()`). All five live engines
      report `yes` for determinism, provenance, canonical artifacts. `replay` remains `?` (cannot be
      honestly established without artifact persistence infrastructure). Five new tests added to
      `tests/test_engine_settlement_survey.py` covering non-deterministic fake, missing-provenance
      fake, positive control, and both directions of the NON_CONTENT_FIELDS counterfactual.
      Survey now shows `yes`/`no` instead of `?` for the three measured run-required criteria.
      Full suite TBD.
- [x] (2026-10-06) Phase 6 -- documentation, `PLANS.md` closure, `TEST_DEBT.md` update. `docs/DOCTRINE.md`
      gained "The evidence contract has exactly one home" and "Metadata stays on the artifact and out of
      its identity"; `docs/ENGINE_TOPOLOGY.md` now states the measured settlement values; `TEST_DEBT.md`
      records the root-status-document cluster; `PLANS.md` moved this entry to `Completed` with a closure
      note and the nine commit SHAs. Guards: `tests/test_doctrine_citations.py` 13 passed, non-censorship
      invariant 7 passed with the scan exiting 0. Ratchet green at `collected=3555 floor=3555`.

### Phase 5 verification (2026-10-06)

Phase 5 landed via `035e4698`, and verification found two gaps in it, both closed here.

**Gap 1 -- the verdict was never tested with a failing case.** All 15 shipped tests exercise
`_content_dict()` or the fakes; none called `measure()`, which is what produces the `yes`/`no` the survey
prints. Forcing the verdict to lie (`determinism = "yes"` unconditionally) left **20 of 21 tests
passing** -- the whole original suite reported green while the verdict was broken, so the survey's `yes`
column could have been built on nothing. Six tests now drive `measure()` through `_construct_engine`,
the same seam production uses, and one of them is the test that catches the forced lie.
Evidence: `FAILED test_measure_reports_no_for_a_non_deterministic_engine`, `1 failed, 20 passed`.

**Gap 2 -- a stale `?`.** The survey reported `conforms: ?` for the three factory engines, and its own
legend defines `?` as "not measurable without running it". That stopped being true once the harness
existed, since the harness supplies a defined stand-in -- so `_conformance_status` now builds the factory
through the harness and checks the result is an `EvidenceProvider`. Left as `?`, it would have been
exactly the defect this plan exists to remove: a status the code no longer supports.

**Resulting honest state:** every live engine reports `yes` on `entry_point`, `conforms`,
`collected_tests`, `determinism`, `provenance`, and `canonical_artifacts`. `replay` is the ONLY
unmeasured criterion, for all five -- so the gap to a technical settlement is exactly one named thing,
and two tests pin that (`test_only_replay_remains_unmeasured_for_live_engines`,
`test_conformance_is_measured_for_factory_engines`). No engine is settleable today; that is now a
specific, checkable statement rather than a blanket `?`.

### Replay closed (2026-10-06, after Phase 6)

Phase 6 recorded `replay` as the single criterion still unmeasured, needing "artifact persistence the
harness does not own". That framing was wrong: the repository already had the contract, and the harness
did not need to own persistence to use it.

`replay_probe` in `abraxas/engines/execution_harness.py` now measures replay by persisting an envelope as
a canonical artifact, reading it back, reproducing the run, and comparing against the **reloaded**
artifact. It mirrors the `RuneReplayPacket` contract already used for runes
(`core/execution/replay_runner.py`, output at `out/replay/latest.json`: `source_execution_hash`,
`replay_execution_hash`, `identical_output`) rather than forcing that type, which operates on a
`ShadowExecutionRun` and does not fit an engine envelope.

**Replay is not determinism repeated, and the difference is measured.** A tuple inside
`verification_metadata` serializes to a JSON array and reloads as a list: two in-process runs agree, so
determinism is `yes`, while the stored artifact no longer equals what was written, so replay is `no`.
`test_replay_catches_a_round_trip_loss_that_determinism_misses` pins that. Driving the probe to compare
against the in-memory content instead of the reloaded artifact — the subtle bug its comment warns about —
fails exactly that one test and nothing else, which is how it was confirmed to have teeth:

    FAILED test_replay_catches_a_round_trip_loss_that_determinism_misses
    1 failed, 26 passed

Failure kinds are separated deliberately: `no` is a property of the engine's output (not serializable,
or does not reproduce); `?` is an environment limit (the artifact could not be written). Blaming the
engine for the harness would be as wrong as the reverse.

**Result: `satisfiable` is now true for all five live engines** and the gap to a technical settlement is
closed. The guarantee is now "nothing is unmeasured" rather than "exactly one thing is unmeasured", and
`test_no_engine_currently_claims_technical_settlement` asserts that corroboration is *available* while
no settlement has been claimed — moving one remains the operator's decision.

Three tests that pinned the old state failed by design when replay became measurable, exactly as their
docstrings instructed, and were re-pinned to the new truth rather than relaxed.

## Surprises & Discoveries

- Observation: the two `EvidenceEnvelope` definitions are not the same object and differ by exactly one
  field. The package-level one (`abraxas/evidence/__init__.py:75`) has 22 fields including
  `schema_version`; the contract one (`abraxas/evidence/contract.py:63`) has 21 and omits it.
  Evidence: `abraxas.evidence.EvidenceEnvelope is abraxas.evidence.contract.EvidenceEnvelope`
  evaluates to `False`.

- Observation: a real live engine returns the contract copy, so a type check against the package copy
  rejects genuine output.
  Evidence: `isinstance(TrutinaEvidenceProvider().produce_evidence(...), abraxas.evidence.EvidenceEnvelope)`
  is `False`, while the same object is an instance of the contract copy.

- Observation: `noesis` returns a plain `dict`, not an envelope at all, and passes every existing
  guard. The conformance test checks `issubclass(NoesisEvidenceProvider, EvidenceProvider)` and never
  inspects a returned value, so the declared return type is unenforced.
  Evidence: a direct call printed returned type `builtins.dict`.

- Observation: three backup files are tracked inside the package directory:
  `abraxas/evidence/__init__.py.bak`, `abraxas/evidence/provider.py.bak`, and
  `abraxas/evidence/adapters/cypher.py.bak`. A `.bak` file inside an importable package is both
  clutter and a hazard, since some tooling will collect it.
  Evidence: `git ls-files abraxas/evidence/` lists all three.

- Observation: the repository root carries a cluster of status documents each asserting completion --
  `PLAN_COMPLETE.md`, `PLAN_IS_DONE.md`, `PLAN_FINISHED.md`, `PLAN_EXECUTION_COMPLETE.md`,
  `PLAN_COMPLETION_FINAL.md`, `PLAN_EXECUTION_SUMMARY.md`, `FURTHER_WORK_PLAN_COMPLETE.md`. This is the
  anti-pattern this repository has already named: a status document is a claim, not evidence. No action
  is taken on them here; it is recorded so the next contributor is not misled by them.

- Observation: **`schema_version` IS read -- by the schema migrator itself.** The field looked like dead
  metadata, and it was deleted on that reasoning. But `EvidenceSchemaMigrator.migrate()` reads it
  (`current_version = envelope.get("schema_version", "v1")`) to decide whether migration is needed, and
  the early return fires only when the version equals the target. Deleting the field forced the deletion
  of the line that wrote it, which silently made migration **non-idempotent**: a migrated envelope keeps
  reading as `"v1"`, so `migrate()` re-runs its defaults on every call and the early return becomes
  unreachable. The full suite stayed green, because no test covered idempotence.
  Evidence: with the version stamp removed,
  `tests/test_evidence_contract_single_home.py::test_migration_is_idempotent` fails with
  `1 failed, 5 passed`; restored, `6 passed`.

- Observation: the grep performed to justify the deletion did not measure the field. The instruction was
  to grep `schema_version`; the executed grep searched for `EvidenceSchemaMigrator` instead and concluded
  no external consumer read the field. That conclusion was true of *external* consumers and false of the
  module that owns the field -- which is the consumer that mattered. Searching for a symbol's owner is
  not searching for the symbol.
  Evidence: the recorded evidence named `EvidenceSchemaMigrator` line numbers only, while
  `grep -n "schema_version" abraxas/evidence/__init__.py` returns line 516 reading it.

- Observation: two further duplicate types remain in the package `__init__`, plus a duplicated helper.
  The executor disclosed these unprompted: `RelationStep`, `CandidateOutput`, and `EvidenceType` exist in
  both the package and `contract.py`, and `create_athanor_envelope` is defined in both. They are out of
  Phase 1's scope and are Phase 2's work, but the same defect shape applies to each.
  Evidence: LSP type warnings on the `__init__` copies after Phase 1, plus the executor's own report.

- Observation: zero production or test files import `EvidenceEnvelope` from the package level
  (`from abraxas.evidence import EvidenceEnvelope`). The only package-level imports are for Brier
  scoring helper functions. All consumers of the envelope type import from
  `abraxas.evidence.contract` directly.
  Evidence: `grep -rn "from abraxas.evidence import" abraxas tests tools scripts --include="*.py"`
  returns only `trutina.py:13` and `test_trutina_q1.py:19`, both importing Brier functions, not the
  envelope.

- Observation: the `schema_version` field on `EvidenceEnvelope` (present only in the package copy,
  not in the contract copy) has zero external readers. The only code that accesses it is the
  `EvidenceSchemaMigrator` class within `__init__.py` itself, which is never imported externally.
  Evidence: `grep -rn "EvidenceSchemaMigrator"` shows only `__init__.py` references and the `__all__`
  export; no external `from abraxas.evidence import EvidenceSchemaMigrator` exists.

- Observation: `EvidenceProvider` had 11 consumers (production + test), all importing from
  `abraxas.evidence.provider`. Zero consumers imported it from the package level. The package copy
  was used only by its own `ProviderRegistry` (also duplicated), which trivially resolves after
  the re-export.
  Evidence: `grep -rn "from abraxas.evidence.provider import.*EvidenceProvider"` returned 11 files;
  `grep -rn "from abraxas.evidence import.*EvidenceProvider"` returned zero.

- Observation: `EvidenceType` in `__init__.py` defined 10 values including `BRIER_SCORING`; the
  `contract.py` copy defined 15 values without `BRIER_SCORING` (but with 6 additional values:
  `TEMPORAL_REASONING`, `RESONANCE_ANALYSIS`, `NARRATIVE_SYNTHESIS`, `MULTIMODAL_INTEGRATION`,
  `PERSISTENT_MEMORY`, `YGGDRASIL_DECISION`, `VIDEO_ANALYSIS`). `BRIER_SCORING` was NEVER used
  anywhere in the repo. All consumers imported from `contract.py`. The contract copy is richer and
  is the one every consumer already uses; the package copy was only a subset.
  Evidence: `grep -rn "BRIER_SCORING"` hits only `__init__.py:30` (definition); zero use-sites.
  `grep -rn "from abraxas.evidence.contract import.*EvidenceType"` returned 11 files.

- Observation: `RelationStep` and `CandidateOutput` in `__init__.py` and `contract.py` are
  structurally identical (same fields, same types). All 8 consumers import from `contract.py`; zero
  import these from the package level.
  Evidence: `grep -rn "from abraxas.evidence.contract import.*RelationStep"` returned 8 files;
  `grep -rn "from abraxas.evidence import.*RelationStep"` returned zero.

- Observation: the `__init__` copy of `create_athanor_envelope` had a bug: it ignored the
  `reasoning_steps` parameter and always passed `reasoning_steps=[]` to the envelope constructor.
  The `contract.py` copy correctly passes `reasoning_steps=reasoning_steps or []`. The only
  consumer (`abraxas/evidence/provider.py:202`) already imported from `contract`, so the buggy copy
  was unused.
  Evidence: diff of `__init__.py:99` (`reasoning_steps=[]`) vs `contract.py:164`
  (`reasoning_steps=reasoning_steps or []`).

- Observation: `Decision` enum is ALSO duplicated between `__init__.py` and `contract.py` with a
  divergence: the contract copy has an extra `REJECT` member. This was not listed in the Phase 1
  executor's disclosure and is not addressed in Phase 2. **Resolved in Phase 3:** single-homed on
  `contract.py`; zero external consumers imported the package copy.
  Evidence: `contract.py:34` has `REJECT = "REJECT"`; `__init__.py:28` (pre-Phase 3) does not.

- Observation: zero files import `Decision` from the package level. All consumers import from
  `abraxas.evidence.contract` (coordinator.py:20, benchmark_suite.py:13, test_trutina_q1.py:17,
  test_abraxas_q1.py:16, policy.py:13). The package copy was used only internally by __init__.py's
  own classes (ArbitrationPolicy, EvidenceArbiter, DecisionRecord, SelectiveComputePolicy), which
  trivially resolve after re-export.
  Evidence: `grep -rn "from abraxas\\.evidence import.*Decision" abraxas tests tools scripts`
  returns zero hits.

- Observation: the `_FakeNonDeterministicProvider` test fake varies the `claim` field to break
  determinism. This was chosen deliberately: varying a content field proves the harness detects
  real non-determinism rather than metadata drift. A fake that only varied `timestamp` would
  be invisible to `_content_dict` -- which is the correct behavior, because timestamp is metadata.
  Evidence: `test_non_deterministic_engine_reported_no` asserts `c1["claim"] != c2["claim"]`.

- Observation: the cypher engine's default inference stores envelopes in the memory layer on first
  call and retrieves them on second call with the same claim. Under the harness stub, this
  side-effect does not occur because the stub bypasses `_default_cypher_inference`. The
  harness's determinism verdict for cypher is therefore a measurement of the stub-constructed
  adapter, which is what the manifest's agreement guard also uses -- consistent, and honestly
  scoped.
  Evidence: `execution_harness._STUB_INFERENCE` returns a fixed dict; cypher's factory
  receives it via `inference_engine` kwarg.

## Decision Log

- Decision: of the four run-required criteria, three are now measurable via execution harness
  (`determinism`, `provenance`, `canonical_artifacts`). `replay` remains `?` because it requires
  artifact persistence infrastructure (loading a stored envelope and reproducing the result) which
  this harness does not own and cannot honestly establish.
  Rationale: the doctrine's rule is that a `?` cannot support a settlement. Reporting `?` where
  measurement is genuinely impossible is truthful; inventing a measurement would be the exact error
  the `schema_version` deletion was.
  Date/Author: 2026-10-06, Hermes Agent (Phase 5).

- Decision: treat `abraxas/evidence/contract.py` as the canonical home, and reduce
  `abraxas/evidence/__init__.py` to re-exports.
  Rationale: every real consumer imports from `contract` -- the verifiers
  (`abraxas/evidence/verifiers/latent.py`, `relational.py`, `lexical.py`, `sign.py`, `calibration.py`),
  the arbiter (`abraxas/evidence/arbiter/arbiter.py`), the policy layer
  (`abraxas/evidence/policy.py`), and all five live engine modules. Moving the small number of
  package-level importers is cheaper and less risky than moving the many contract-level importers, and
  it keeps the interface next to the code that dominates it.
  Date/Author: 2026-10-06, Bob Vajeen.

- Decision: the `schema_version` field must be resolved deliberately, not dropped silently.
  Rationale: the two copies differ by exactly this field, so whichever copy loses will change a hashed
  or serialized payload. The executor must first measure whether `schema_version` is read anywhere. If
  it is read, it is promoted to the canonical envelope with a test; if it is not, it is recorded as
  deliberate removal in the Decision Log with the grep that proves it is unread. Silently keeping the
  smaller copy would repeat the exact defect class this task exists to fix.
  Date/Author: 2026-10-06, Bob Vajeen.

- Decision: import-site count for `abraxas.evidence.EvidenceEnvelope` / `EvidenceProvider` is 2 files.
  Rationale: `grep -rn` across `abraxas tests tools scripts --include="*.py"` found only
  `abraxas/evidence/providers/trutina.py:13` and `abraxas/evidence/test_trutina_q1.py:19`, both
  importing Brier scoring helpers, never `EvidenceEnvelope` or `EvidenceProvider`. Zero dotted-name
  references to `abraxas.evidence.EvidenceEnvelope` or `abraxas.evidence.EvidenceProvider` exist in
  the entire repo. The cost of the package-level redefinition is low at the import site but the cost
  of the divergence (rejected genuine engine output) is high.
  Date/Author: 2026-10-06, Hermes Agent (Phase 0 measurement).

- Decision: deliberately remove `schema_version` from the canonical `EvidenceEnvelope`.
  Rationale: zero external code reads `EvidenceEnvelope.schema_version`. The only reader is the
  `EvidenceSchemaMigrator` class internal to `__init__.py`, which is itself never imported externally.
  Safe to drop. The field is removed from the `EvidenceSchemaMigrator.SCHEMA_VERSIONS["v2"]["fields"]`
  list and the `migrate` method no longer writes `schema_version = "v2"` to migrated envelopes.
  Evidence: `grep -rn "EvidenceSchemaMigrator" abraxas tests tools scripts` returns only
  `__init__.py` references; no external import site exists.
  Date/Author: 2026-10-06, Hermes Agent.

- Decision: create the execution harness only after the contract is single-homed.
  Rationale: a harness that runs all engines can only compare their outputs if their outputs share a
  type. Building it first would mean writing per-engine special cases that the single-homing removes.
  Date/Author: 2026-10-06, Bob Vajeen.

  - Decision: **`schema_version` is PROMOTED to the canonical envelope, superseding an earlier decision in
  this same plan to remove it.** The canonical `abraxas/evidence/contract.py` envelope now declares
  `schema_version: str = "v2"` as its first field, and `to_dict()` serializes it.
  Rationale: the removal rested on the claim that nothing reads the field. That claim was measured
  wrongly -- the grep searched for `EvidenceSchemaMigrator` rather than for `schema_version`, so it never
  found the line in that very class which reads the field (`__init__.py:516`). Removing the field then
  required removing the write, which broke migration idempotence without failing a single test. The
  correct resolution follows this plan's own stated rule -- if any site READS the field, promote it --
  and it also matches the repository's identity-versus-metadata doctrine: a format descriptor belongs on
  the artifact, and is excluded from content hashes rather than deleted. The rule is unchanged; the
  measurement that fed it was.
  Date/Author: 2026-10-06, Bob Vajeen.

  - Decision: the version stamp in `migrate()` is restored **verbatim** as
  `envelope["schema_version"] = "v2"` -- assignment, not `setdefault`.
  Rationale: `git show 5773c6ff:abraxas/evidence/__init__.py` shows the pre-change line used assignment.
  An initial restoration used `setdefault`, which would leave an envelope that declared `"v1"`
  still declaring `"v1"` after being migrated to v2 -- recording the wrong state, and preserving the
  very non-idempotence being fixed. Restoring the original semantics avoids inventing behaviour while
  repairing a deletion.
  Date/Author: 2026-10-06, Bob Vajeen.

- Decision: single-home `EvidenceProvider` on `abraxas/evidence/provider.py`.
  Rationale: the package `__init__` copy was a plain class with `NotImplementedError` stubs (not
  an ABC), while `provider.py` defines the real `ABC` with `@abstractmethod`. All 11 external
  consumers already import from `provider.py`; zero import from the package level. The only
  internal user of the package copy was its own `ProviderRegistry`, which trivially resolves after
  the re-export.
  Date/Author: 2026-10-06, Hermes Agent (Phase 2).

- Decision: single-home `RelationStep`, `CandidateOutput`, and `EvidenceType` on `contract.py`.
  Rationale: `RelationStep` and `CandidateOutput` are structurally identical between the two copies.
  `EvidenceType` diverges: the package copy has 10 members including `BRIER_SCORING` (used zero times),
  while the contract copy has 15 members including 6 not in the package copy. All consumers already
  import from `contract.py` (8 for RelationStep, 11 for CandidateOutput, 11 for EvidenceType); zero
  import these from the package level. The contract copy is the richer, actively used version.
  `BRIER_SCORING` is dead code.
  Date/Author: 2026-10-06, Hermes Agent (Phase 2).

- Decision: single-home `create_athanor_envelope` on `contract.py`.
  Rationale: the package copy had a bug (ignored the `reasoning_steps` parameter, always passing `[]`).
  The contract copy correctly passes the parameter. The only consumer (`provider.py:202`) already
  imports from `contract.py`. Single-homing also removes the bug.
  Date/Author: 2026-10-06, Hermes Agent (Phase 2).

- Decision: NOT single-homing `Decision` enum, despite it being duplicated.
  Rationale: `Decision` is duplicated between `__init__.py` and `contract.py` with a divergence
  (contract has an extra `REJECT` member). It was not listed in the Phase 1 executor's disclosure
  and is not in Phase 2's scope. The `__init__.py` copy is used by `ArbitrationPolicy` methods
  within the same module; changing it now would expand scope beyond what the plan calls for. It is
  recorded as a Surprise for the next phase.
  Date/Author: 2026-10-06, Hermes Agent (Phase 2).
  **SUPERSEDED** by the decision below in Phase 3.

- Decision: single-home `Decision` on `abraxas/evidence/contract.py`.
  Rationale: the Phase 2 decision to defer was conservative and reasonable, but Phase 3's extended
  scope explicitly calls for it. The contract copy has `REJECT` (needed for fail-closed coordination),
  the package copy lacked it. Zero external consumers imported the package copy; internal __init__.py
  consumers resolve trivially through module-level name resolution after the re-export. The
  parametrized identity guard covers it so a regression is caught on one line.
  Date/Author: 2026-10-06, Hermes Agent (Phase 3).

- Decision: **leave every settlement `unsettled` even though all six technical criteria now measure as
  passing for the five live engines.**
  Rationale: the criteria are measured under ONE defined input -- the harness's deterministic stub
  inference callable -- so the evidence supports "performs to specification on a defined input", not
  universal determinism. A `Settlement` carries `settled` / `unsettled` / `not_applicable` and cannot
  express that qualification, so claiming `settled` would assert more than was measured. The operator was
  asked explicitly when the corroboration first became available and chose to record it and revisit, which
  is the doctrine's own rule: the survey corroborates, the operator decides. The corroboration is
  therefore documented in `docs/ENGINE_TOPOLOGY.md` under "The operator's decision", and two tests hold
  the line so the corroboration cannot silently disappear and no settlement can be claimed without the
  decision being revisited.
  Date/Author: 2026-10-06, Bob Vajeen (operator decision).

## Outcomes & Retrospective

**Phase 3 (2026-10-06):** `Decision` single-homed. The package copy had 5 members (missing `REJECT`);
the contract copy has 6. `A is B` is now `True`. A generalized parametrized identity guard covers
all 6 contract types (EvidenceEnvelope, EvidenceProvider, RelationStep, CandidateOutput,
EvidenceType, Decision) — a new duplicate is caught by adding one line to a table. Both the
Decision-specific guard and the generalized guard were driven to fail by temporarily reintroducing
the local duplicate, observed failing, then removed. Guard file grew from 6 to 12 tests.
Two new observations recorded: zero external consumers import Decision from the package, and
policy.py (the only external consumer) already imports from contract.

**Completion (2026-10-06):** The plan is done. Achieved, against the Purpose: the evidence envelope is
single-homed with one identity, enforced by a table-driven guard asserting object identity across all six
contract types, so a newly duplicated type is caught by adding one row. Every live engine's
`produce_evidence` returns that one envelope — `noesis` no longer returns a bare `dict`, which it had
done while every guard in this repository passed. `Decision` no longer has a weaker variant missing
`REJECT`. `schema_version` is on the canonical artifact and excluded from identity rather than deleted.
Three tracked `.bak` files are gone. And the payoff landed: the survey reports *measured* values for
determinism, provenance, and canonical artifacts, established by running each engine twice on identical
input, so the gap to a technical settlement is one named criterion (`replay`) instead of a blanket `?`.

**What remains.** `replay` is unmeasured; it needs artifact persistence the harness does not own. No
engine claims a settlement, which is correct — `satisfiable` is false for all ten, and a test fails if
that changes without the manifest citing evidence. The harness proves determinism under one defined input,
which is what this criterion can honestly support at this stage, not determinism in general.

**Lessons, each earned by a specific failure in this plan.**

*One truth, one home — and the failure it prevents is silent.* The duplicate contract type raised no
error; it made an `isinstance` check return `False` for genuine engine output, and the weaker `Decision`
could not express a rejection at all. Nothing surfaced. Only measuring the objects against each other
found them.

*A guard that checks the wrong property certifies the wrong thing.* Every conformance test here asked
whether a class inherits from a base class. None asked what `produce_evidence` returns, so a provider
returning a dictionary conformed perfectly.

*Deleting to satisfy a comparison is a distinct failure from deleting to satisfy a checker.* A field was
removed to resolve a one-field divergence. The suite stayed green while `EvidenceSchemaMigrator` silently
lost idempotence, because the class that owned the field read it. Searching for a symbol's *owner* is not
searching for the symbol, and the case of the name matters: a search for `Brier_Scoring` proved nothing
about `BRIER_SCORING`.

*Correctness of a helper does not certify the verdict that consumes it.* Fifteen tests exercised the
comparison helper and the fakes; none exercised `measure()`. Forcing the verdict to always answer `yes`
left **20 of 21 tests passing**. Only a test that drives the verdict with a failing case separates them.

*`?` has a meaning and it must be re-earned.* The legend defines `?` as "not measurable without running
it". Once the harness made factories runnable, `conforms: ?` was no longer true. A stale `?` is the same
defect as an unearned `yes`, just quieter.

*Enforcement requires a demonstration.* Every guard was driven to fail before being trusted — and the
first two attempts at the harness guard were themselves worthless: one injected a duplicate *before* the
import that binds the name, so the import overwrote it and the guard passed; the other broke
`from __future__` ordering so nothing ran. Injecting at runtime, then printing the injected state in the
same run, is what made the result mean anything.

## Context and Orientation

This repository is a Python project rooted at `/Users/appliedalchemylabs/Abraxas`. Tests live in
`tests/`, and the test suite is run through `scripts/test_ratchet.sh`, which enforces that the number of
failing tests never rises above zero and that the number of collected tests never falls below a floor.
At the time of writing the ratchet reports `failures=0 baseline=0 collected=3525 floor=3525`.

Terms used in this plan, defined plainly:

An **engine** is a component that produces reasoning output. Its identity, status, and entry point are
declared in one place, `abraxas/engines/manifest.py`, in a tuple named `ENGINES`. Each entry is an
`EngineSpec`. An engine whose status equals the module constant `LIVE` is expected to work; one whose
status equals `PLANNED` is a declared-but-unimplemented surface.

An **evidence provider** is the interface an engine implements. It is defined by
`abraxas/evidence/provider.py` as an abstract base class named `EvidenceProvider` with two methods:
`get_model_identity()` returning a string, and `produce_evidence(request_id, claim, context, budget=None)`
returning an evidence envelope.

An **evidence envelope** is the record an engine returns: the claim, the candidate outputs, confidence,
uncertainty, the reasoning steps, the provenance, and a timestamp.

A **settlement** is a claim about how far a capability has been established, recorded on each
`EngineSpec`. There are three kinds: empirical (is the claim supported by evidence), technical (does the
instrument perform to specification), and economic (does it produce consequences someone adopts). This
plan concerns **technical** settlement only.

The **settlement survey** is `scripts/survey_engine_settlements.py`. It evaluates every engine against
the six criteria the doctrine names for technical settlement -- determinism, schemas, tests, replay,
provenance, canonical artifacts -- and refuses to certify a settlement resting on an unmeasured
criterion. It currently reports `?` (not measurable without running the engine) for determinism, replay,
provenance, and canonical artifacts, which is why no engine can be settled. Its guard lives at
`tests/test_engine_settlement_survey.py`.

## Plan of Work

**Phase 0 -- Baseline.** Run the full suite through the ratchet and save the output. Record, with
commands and pasted output, the four duplicate definitions (`abraxas/evidence/provider.py:19`,
`abraxas/evidence/__init__.py:75`, `abraxas/evidence/__init__.py:175`, `abraxas/evidence/contract.py:63`)
and the three tracked `.bak` files. Record how many import sites reference the package-level names,
because that number is the real cost of this change and must appear in the Decision Log:

    grep -rn "from abraxas.evidence import\|abraxas\.evidence\.EvidenceEnvelope\|abraxas\.evidence\.EvidenceProvider" \
      abraxas tests tools scripts --include="*.py"

**Phase 1 -- Single-home the envelope.** In `abraxas/evidence/__init__.py`, replace the class definition
at line 75 with an import and re-export of the canonical type from `abraxas/evidence/contract.py`. Resolve
`schema_version` per the Decision Log rule. Write a test asserting identity -- that
`abraxas.evidence.EvidenceEnvelope is abraxas.evidence.contract.EvidenceEnvelope` -- and assert the field
count of the single envelope so a silent re-divergence is caught. If any site imported the package-level
copy and relied on `schema_version`, that site must be updated in this same phase; a change whose two
parts are measured jointly must land jointly.

**Phase 2 -- Single-home the provider, and fix the dict return.** In `abraxas/evidence/__init__.py`,
reduce the provider definition at line 175 to a re-export of `abraxas/evidence/provider.py`. Then make
`abraxas/evidence/verifiers/latent.py` return an envelope from `produce_evidence` instead of a
dictionary: construct the canonical envelope with the same values it currently puts in the dict. Add a
test that every `LIVE` engine's `produce_evidence` returns an instance of the single envelope. That test
must fail before Phase 2's code change and pass after.

**Phase 3 -- Enforce with guards that fail.** Extend `tests/test_engine_manifest_agreement.py` with two
participants. First, an identity guard asserting one definition of each contract type, driven to fail by
temporarily reintroducing a duplicate and observing the failure. Second, a return-type guard over every
live engine, driven to fail by temporarily reverting the `latent.py` fix. Record both observed failures
verbatim in `Artifacts and Notes`. An enforcement check nobody has watched reject anything is not known
to enforce anything.

**Phase 4 -- Remove the tracked backups.** Confirm no module imports the `.bak` paths, then remove the
three files with `git rm`, which both deletes and unstages them in one step.

**Phase 5 -- Measure the criteria.** Create `abraxas/engines/execution_harness.py`. For each `LIVE`
engine it constructs the engine -- passing a deterministic stand-in inference callable to the three that
are factories, since their signatures take `inference_engine` -- calls `produce_evidence` twice with
identical `request_id`, `claim`, and `context`, and compares the two results. It then reports three
measured verdicts per engine: determinism (the two canonical payloads are identical), provenance (the
`provenance` mapping is present and non-empty), and canonical artifacts (the canonical payload hashes
stably across repeated runs and after a re-import).

There is a trap here that must be handled explicitly. The envelope carries a `timestamp` field and an
`evidence_id`, which are **metadata**, not content, exactly as `generated_at_utc` was metadata rather
than content in the lexicon fingerprint fixed earlier in this repository. If the harness compares whole
envelopes, every engine will look non-deterministic for reasons that have nothing to do with its
reasoning. The harness must separate identity from metadata: compare and hash the content while
excluding the fields it has established to be non-content, and it must state which fields it excludes
and why. The dangerous fix -- deleting the timestamp to make the comparison pass -- must not be taken,
because the timestamp is legitimate metadata; the correct fix is to exclude it from the identity
comparison.

Then extend `scripts/survey_engine_settlements.py` so that the run-required criteria consult this
harness. `?` becomes `yes` where the harness measured a pass, `no` where it measured a failure, and only
remains `?` where measurement is genuinely impossible. The survey's existing rule stands: a criterion
that is `?` cannot support a settlement.

**Phase 6 -- Documentation.** Add the contract rule to `docs/DOCTRINE.md` in the same style as the
existing sections: the envelope is single-homed, engine output must satisfy it, and metadata fields are
excluded from identity rather than deleted. Update `docs/ENGINE_TOPOLOGY.md` where it describes the
settlement criteria with the newly measured values. Add a `TEST_DEBT.md` entry recording the root-status
document cluster named in Surprises. Move this work's entry in `PLANS.md` to `Completed` with a closure
note and links to the commits.

## Concrete Steps

All commands run from `/Users/appliedalchemylabs/Abraxas`.

The interpreter matters. A bare `python3` in this environment resolves a foreign checkout through a
stale editable install and produces roughly 28 spurious collection errors. Always select the toolchain
interpreter:

    PY=$(ls -d /Users/appliedalchemylabs/.hermes/tools/python-3.14*/bin/python3 | head -1)
    "$PY" -V

Expected: `Python 3.14.7`.

Run the full suite through the ratchet, which takes between three and thirteen minutes and must not be
run concurrently with another suite run in the same working tree, because two runs share the generated
`out/`, `data/`, and `.aal/` directories and manufacture failures belonging to neither run:

    bash scripts/test_ratchet.sh

Expected final lines:

    ===== 3514 passed, 4 skipped, 9 xfailed in NNN.NNs ======
    failures=0 baseline=0  collected=3525 floor=3525
    OK: within baseline
    RATCHET_EXIT=0

Run a single test file while developing:

    "$PY" -m pytest tests/test_engine_manifest_agreement.py -q --no-header

Never use `git add -A` or `git add .` in this repository: `out/`, `data/`, `.aal/`, and `.abraxas/`
are tracked but rewritten by every test run, so a blanket add stages hundreds of generated files and
the pre-receive hook rejects the push. Stage explicit paths only.

A `git push` in this repository has hung and been killed at its timeout, leaving the commit local while
the remote stayed behind. Push in the background with an output log, then verify by comparing
`git rev-parse HEAD` against `git ls-remote origin main`; do not conclude a push landed merely because
the command returned.

## Validation and Acceptance

Two assertions, both checkable by a human at a terminal.

First, there is one envelope. This must print `True`:

    "$PY" -c "from abraxas.evidence import EvidenceEnvelope as A; \
    from abraxas.evidence.contract import EvidenceEnvelope as B; print(A is B)"

Before this work it prints `False`, which is the defect.

Second, every live engine returns that envelope and is deterministic under identical input:

    "$PY" -m pytest tests/test_engine_manifest_agreement.py tests/test_engine_settlement_survey.py -q

Expected: all pass, including the new guards. The return-type guard must have been observed failing
before the `latent.py` change; that observed failure is the evidence the guard works.

Third, the survey reports measured values rather than `?` for the criteria the harness can establish:

    "$PY" scripts/survey_engine_settlements.py

Expected: the live engines show `yes` or `no` in the determinism, provenance, and canonical-artifact
columns, with `no` accompanied by the harness's stated reason. The process exits 0.

Finally the ratchet must be green with the collected floor raised to the new count, since this work adds
tests: `failures=0 baseline=0 collected=N floor=N` where N is the new count taken verbatim from the
`collected N items` line of the run, because the passed/skipped/xfailed components do not reconcile with
it.

## Idempotence and Recovery

Every phase is additive or a re-export, so re-running a phase is safe. The one destructive step is
Phase 4's `git rm` of three backup files; it is recoverable from git history with
`git checkout <sha> -- <path>` because the files are tracked.

If the suite reports failures that disappear when a single test file is run alone, suspect a concurrent
suite run in the same tree rather than a real defect, and re-run the file in isolation before changing
anything. Do not modify source to satisfy a checker: if a guard fails, fix the guard or fix the code the
guard is complaining about, never the wording of the code the guard reads.

## Artifacts and Notes

The four duplicate definitions, as measured:

    abraxas/evidence/provider.py:19    class EvidenceProvider(ABC):
    abraxas/evidence/__init__.py:75    class EvidenceEnvelope:
    abraxas/evidence/__init__.py:175   class EvidenceProvider:
    abraxas/evidence/contract.py:63    class EvidenceEnvelope:

The field divergence, as measured (package copy first, contract copy second):

    only in __init__ : ['schema_version']
    only in contract : []
    identical object? False

A live engine returning the contract copy while the package copy is not an instance of it, and a second
live engine returning a bare dictionary:

    trutina envelope is a package one?  False | is contract one?  True
    noesis returned type: builtins.dict

The idempotence guard, observed failing against the deletion it exists to catch, and passing once the
version stamp is restored:

    $ "$PY" -m pytest tests/test_evidence_contract_single_home.py -q --no-header -o addopts=""
    # with `envelope["schema_version"] = "v2"` removed:
    FAILED tests/test_evidence_contract_single_home.py::test_migration_is_idempotent
    1 failed, 5 passed, 8 warnings in 0.44s

    # restored:
    6 passed, 8 warnings in 0.56s

Note the `-o addopts=""` flag: this repository's `pyproject.toml` sets `addopts = "-v --strict-markers"`,
which overrides a plain `-q` and emits pytest's tree output instead of `::`-joined test ids. Any tooling
that parses collected ids must neutralize the inherited options, or it will silently parse nothing.

Phase 1 new test file: `tests/test_evidence_contract_single_home.py` (6 tests)
- `test_evidence_envelope_single_home_identity`: asserts `EvidenceEnvelope is ContractEnvelope`
- `test_canonical_envelope_field_count`: asserts 22 fields AND that `schema_version` is among them,
  superseding the earlier version of this test which asserted 21 and its absence
- `test_the_package_export_cannot_diverge_from_the_contract`: asserts both field lists agree
- `test_schema_version_is_serialized`: asserts `to_dict()` carries the format marker
- `test_migration_is_idempotent`: the guard for the regression; observed failing when the version stamp
  is removed
- `test_migration_is_a_no_op_for_an_already_current_envelope`: asserts the early return

Identity guard driven to FAIL (observed at 2026-10-06):
```
FAILED tests/test_evidence_contract_single_home.py::test_evidence_envelope_single_home_identity
AssertionError: EvidenceEnvelope must be a single canonical type.
The package __init__ must re‑export the contract copy, not redefine it.
assert EvidenceEnvelope is ContractEnvelope
```
The guard was driven to fail by temporarily replacing the re-export in `__init__.py`
with a new local `@dataclass EvidenceEnvelope` definition, causing `A is B` to be
`False`. The duplicate was then removed and the test passed.

Phase 0 baseline (ratchet, with pre-change code):
```
===== 3514 passed, 4 skipped, 9 xfailed, 38 warnings in 224.40s (0:03:44) ======
failures=0 baseline=0  collected=3525 floor=3525
OK: within baseline
```

## Interfaces and Dependencies

No new third-party dependency is introduced. The harness uses only the standard library plus the
repository's own canonical serialization helpers, `hash_canonical_json` and `canonical_json` from
`abraxas/core/provenance.py` and `abraxas/core/canonical.py`, which already exist and are already used
by `abraxas/forecast/store.py` and `abraxas/narratives/generator.py`.

At the end of Phase 1, `abraxas/evidence/__init__.py` must expose:

    from abraxas.evidence.contract import EvidenceEnvelope, EvidenceProvider  # re-export, not redefinition

At the end of Phase 2, in `abraxas/evidence/verifiers/latent.py`, the method

    def produce_evidence(self, request_id: str, claim: str,
                         context: Dict[str, Any],
                         budget: Optional[Dict[str, Any]] = None) -> EvidenceEnvelope:

must return an `EvidenceEnvelope` instance rather than a `dict`.

At the end of Phase 5, in a new module `abraxas/engines/execution_harness.py`, define:

    def run_once(engine: EvidenceProvider, request_id: str, claim: str,
                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Return one evidence envelope as a plain mapping."""

    def measure(engine_name: str) -> Dict[str, str]:
        """Return {'determinism': 'yes'|'no', 'provenance': ..., 'canonical_artifacts': ...,
        'reason': <text>} for one engine, by running it twice on identical input."""

    NON_CONTENT_FIELDS: Tuple[str, ...] = (...)
        """Envelope fields excluded from the identity comparison because they are metadata:
        the timestamp and the evidence identifier. Named explicitly so the exclusion is reviewable."""
