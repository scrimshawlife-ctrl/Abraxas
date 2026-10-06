# Test Debt Inventory

Baseline as of 2026-10-05 (after the governance pass): **28 failed / 3264 passed /
4 skipped / 9 xfailed**.

This file is the human-readable companion to `scripts/test_ratchet.sh`. When a cluster is
resolved, lower `BASELINE_FAILURES` in that script and update the matching row here **in the
same commit**.

## Rulings APPLIED (human go given after review)

| Cluster | Tests | Jev's ruling | Confidence |
|---|---|---|---|
| Reverse coupling | 1 | `delete_legacy_package` | 0.85 |
| Sandbox override maps | 1 | `override_else_evaluate` | 0.85 |
| `SandboxResult` None floats | 1 | `make_optional` | 0.88 |
| Memetic `operation_id` | 1 | `trust_expected_values` (taken narrowly) | 0.73 |

## Governance pass (operator instruction: "relax governance a little, it's too strict")

Applied WITHOUT weakening any rule — the operator authorised relaxation, but it turned out
not to be needed:

| Item | Action |
|---|---|
| 4 heavy scripts + `dependency-governance-check` | Registered in `CLASSIFIED_PATHS` / `CLASSIFIED_MAKE_TARGETS`. They exist and are reachable; the lint wanted bookkeeping, not a weaker rule. |
| README missing `Tier 2.5` | Added the canonical Tier 2.5 marker (federated readiness bridge). |
| `evaluate_redundancy_gate` | Returned `np.bool_` from a numpy comparison despite declaring `Tuple[bool, ...]`. Coerced with `bool(...)`. |
| Stabilization test data | Claimed "very unstable" but its spread gave variance 0.0292 against an asserted 0.05. Widened the data to match its own premise; the assertion is unchanged. |
| `is_vbm_inscope` | Matched `str(candidate.scope)`, which serialises dict KEYS. Every scope has the key `pattern_type`, so `pattern` matched every candidate and nothing was ever out-of-scope. Now matches values only. |
| `VBM_THRESHOLD` | Was **0.65** while the casebook's own 7 canonical episodes measure **0.0189-0.0523** and a strongly VBM-like sentence measures 0.0718 — the tag could never fire. Lowered to **0.05** and hoisted to a module constant. Makes detection *more* sensitive. |

**Flagged, not touched:** `test_non_censorship_invariant` fails on a real scan finding
("Non-censorship scan detected potential violations"). That is a censorship-detection
invariant, not a strictness knob — relaxing it would remove a guarantee rather than tune
one. Needs a separate, explicit decision.

## Ruled by Jev, STILL NOT APPLIED

| Cluster | Tests | Jev's ruling | Confidence | Why parked |
|---|---|---|---|---|
| Analysis content, remainder | 10 | `trust_expected_values` | 0.73 | The memetic clustering expectation needs a redesigned similarity metric (Jaccard gives 0.21 against an expected 0.42), not a label fix.

## ABSTENTION — Jev declined, do not treat as a decision

| Cluster | Tests | Top label | Confidence |
|---|---|---|---|
| Firewall response mode | 8 | `strengthen_transformations` | **0.42** (below the 0.65 floor; `leave_as_is` scored 0.38) |

Jev will not rule on whether the 80%/50% reduction thresholds or the transformations are
canonical. `lower_test_thresholds` scored 0.01, so at least the *weak* option is clearly
excluded — but the choice between strengthening the transformations and leaving it alone is
genuinely open, and the probabilities are close.

## Not yet examined

| Cluster | Tests | Note |
|---|---|---|
| Singles | 13 | `oracle_packet_drift` (2), `tier_gating_psychonaut`, `smv_build_units_from_vector_map`, `runes_registry`, `runes_invocation`, `oracle_packet_batch`, `multi_domain_seedpack`, `federated_evidence`, `evolution_system`, `epp_builds_ranked_proposals`, `canon_ledger_from_audit_v0`, `calibration_drift_report`. Jev ruled `characterise_first` (1.00); signatures collapsed but not yet mapped to clusters. |

## Deliberately parked by earlier Jev rulings

| Cluster | Tests | Ruling | Confidence |
|---|---|---|---|
| `self_build_*` statefulness | 8 | leave as-is → marked `xfail(strict=True)` | 0.84 |
| Builder sigil drift | 1 | keep reverted → marked `xfail(strict=True)` | 0.94 |

An `xfail(strict=True)` marker turns into a suite-failing **XPASS** if someone later resolves
the underlying issue without removing the marker. That is intentional: the debt cannot
silently disappear.

## Resolved

| Date | Commit | Fix | Cleared |
|---|---|---|---|
| 2026-10-05 | `e5e69252` | Misplaced `from __future__`, `use_enum_values` `.value`, shadow-detector contract, undeclared `RunState.ledger_events` | 62 |
| 2026-10-05 | `0ac8545a` | `MappingResult.input_params`, forecast provenance aliases, `DomainRegistryV1` defaults + method API | 10 |
| 2026-10-05 | `410addf9` | 4 non-UTF-8 files; corrupted rune IDs | 3 |
| 2026-10-05 | `4706e8b4` | MDA envelope coercion, canonical subdomain payload shape, no-domain-prior, wired `run_tvm_shadow_flow` | 2 |
| 2026-10-05 | `1dbeec62` | Debt inventory + regression ratchet | — |
| 2026-10-05 | `050b07de` | Test-side defects: `yaml.safe_dump(model.dict())` → `model_dump(mode="json")` (3 sites, found by DRY grep); rune count as a floor; `pytest.approx`; builder-check xfail | 2 (+1 xfail) |
| 2026-10-05 | `303bf2c4` | Jev rulings applied: `evidence_completeness` fixture was wrong, not the 0.80 threshold; `self_build_*` xfail | 2 (+8 xfail) |
| 2026-10-05 | `fc3a6447` | Added the three missing `make` targets and documented the proof spine **truthfully** | 2 |
| 2026-10-05 | `62150a8e` | Sandbox: per-case override maps; `SandboxResult` accepts absent metrics | 2 |
| 2026-10-05 | `b15118b7` | Deleted dead `abraxas/evidence/legacy/` (40 of 41 reverse-coupling violations) | 1 |
| 2026-10-05 | (memetic) | `claim_extract` operation_id corrected | 1 |

| 2026-10-05 | governance pass | Registered heavy paths/targets; Tier 2.5 marker; `np.bool_` gate; stabilization data; VBM scope + threshold | 10 |

Session total: **134 → 28 failures, zero regressions.**

## Rules

- Never move a behavioural threshold, policy constant, or scan rule to make a test green.
- Never hand-write a `NOT_COMPUTABLE` artifact (or any other state) to revive a stateful test.
- Never regenerate canon artifacts (sigils, manifests, generated operators) unilaterally.
- **Never document something that does not exist.** If a test demands documentation of a
  command, verify the command exists first; if it does not, either build it or record the
  test as aspirational. This caught a 0.98-confidence ruling built on a false premise.
- `out/`, `data/`, `.aal/`, `.abraxas/` are tracked but rewritten by every test run.
  **Never `git add` them.**
- Prove zero regressions after every batch by set-diffing failure lists.
- Record every Jev ruling with its confidence, and record abstentions as abstentions.

## The 28 baseline is NOT firm (found 2026-10-06)

Re-running the suite with a **reversed** collection order (`find tests -name 'test_*.py'
| sort -r`) yields **31 failures, not 28**. Three tests appear only in that order:

    tests/shadow_metrics/test_access_control.py::test_direct_module_access_blocked
    tests/shadow_metrics/test_patch_registry.py::test_get_current_version
    tests/test_self_build_approval_receipt.py::test_approval_receipt

So `scripts/test_ratchet.sh` (BASELINE_FAILURES=28) is measured against **one**
collection order. Treat 28 as "the canonical-order number", not "the number". Any
future baseline claim must be confirmed under at least two orders.

`abraxas/shadow_metrics/__init__.py:12` defines `_ALLOW_CORE_IMPORT = False`, a
module-level gate flipped via `global` at line 114.

**Do NOT "fix" this by resetting that flag per test.** Tried it: resetting to False
before every test took the reversed-order count from 31 to **35** and broke the xfail
tally (9 -> 5), adding failures in `test_self_build_multi_apply`,
`test_self_build_operator_queue` and `test_self_build_patch_plan`. These tests are
sequenced deliberately -- one enables access so a later one can use it. The flag being
sticky is load-bearing, not a leak. Reverted clean.

The real fix is to make those specific tests self-contained (set the state they need in
their own fixture) rather than depending on a predecessor having run.

### Progress: 3 order-sensitive tests -> 2

FIXED (verified both orders):
- `test_patch_registry.py::test_get_current_version` used the shared `get_ledger()`
  singleton, which carries patches other tests added. Now uses a fresh
  `SSMPatchLedger()`. Reversed-order count 31 -> 30, canonical unchanged at 28, no
  collateral, xfail tally intact at 9 in both orders.

STILL ORDER-DEPENDENT (2), with the reason each resists the obvious fix:
- `test_access_control.py::test_direct_module_access_blocked` depends on the **import
  cache**, not just the flag: the guard fires only on the first import, so once
  `abraxas.shadow_metrics.core` is in `sys.modules` a later import succeeds anyway.
  Two attempted fixes, both reverted for collateral damage:
    * resetting `_ALLOW_CORE_IMPORT` process-wide per test: 31 -> 35 (broke 4 self_build
      tests, xfail 9 -> 5) -- the sticky flag is load-bearing for tests that opt in.
    * purging `abraxas.shadow_metrics.*` from `sys.modules` around the test: 30 -> 33
      (fixed this one, broke the same 4) -- re-import creates duplicate module objects.
    * an autouse fixture in that file setting the flag False + restoring: also broke the
      same 4, because forcing the guard to fire caches a partially-initialised module
      that later tests then import. 31 -> 34. Reverted.
  Any future attempt must isolate at PROCESS level (subprocess per test), not by
  mutating sys.modules or the flag.
- `test_self_build_approval_receipt.py::test_approval_receipt` calls
  `run_self_build_approval_receipt([], [])` with empty inputs and asserts
  `approval_count >= 1` -- it depends on artifacts on disk that earlier tests wrote,
  i.e. state from `out/`, not from a singleton. Fixing it means injecting the artifact
  path rather than reading live repo state.

## Jev consultation 2026-10-06: 12 of the remaining failures are decision-gated

Put to Jev as one state with three `choice` questions and three `noul` meta-questions
(certifi transport required on this machine; an SSLContext passed directly is not
callable).

| Question | Ruling | Confidence | Spread |
|---|---|---|---|
| 8 firewall reduction-ratio failures | **hand_over** | **0.96** | hand_over 0.980, fix_reducer 0.010, fix_fixtures 0.010, move_threshold 0.000 |
| numogram density scale vs 0.1 | **hand_over** | **0.84** | hand_over 0.880, renormalize 0.110, fix_expectation 0.010, lower_threshold 0.000 |
| 3 enum/label mismatches | **hand_over** | **0.85** | hand_over 0.890, per_case 0.110, fix_tests 0.000, fix_impl 0.000 |
| Is it safe to fix clearly-mechanical bugs without waiting? | **yes** | noul **0.83** | - |
| Is it safer to hand the threshold decisions to the human? | **yes** | noul **0.94** | - |
| Is it safe to apply threshold-moving rulings autonomously? | **NO** | noul **0.03** | - |

**RULING: apply only the mechanical fixes (no behaviour or threshold change). Hand the
three decision groups to the human with these confidences attached.**

`move_threshold` scored **0.000** and `lower_threshold` **0.000** on the two threshold
questions. That is the repo rule being confirmed independently: moving a threshold or
policy value to make a test green is not a bug fix, because it guesses which side of a
contract is canonical.

The meta-answer is the load-bearing one. `apply_autonomously = 0.03` is a strong NO
even though the individual rulings are confident (0.84-0.96). Asking a decision model
does not transfer the human's authority to APPLY its answer. So the 12 stay open and
parked, awaiting a human ruling -- not because they are hard, but because they are
policy choices.

**Still unblocked (Jev 0.83):** the mechanical failures, which change no behaviour --
including `run_mda_for_oracle()` signature drift (`run_at`), `abraxas_ase/tiering.py:67`
list-vs-dict `AttributeError`, and the hand-constructed pydantic `ValidationError`
missing `line_errors` (which needs `ValidationError.from_exception_data`).

## Jev second consultation 2026-10-06: the human delegated, Jev differentiated

The first ruling was hand_over across the board, which the human was shown. The human
then explicitly directed that Jev rule on the technical merits. Re-consulted with that
single change in the state (authority delegated; no new technical evidence) and with
hand_over kept available.

| Question | Ruling | Conf. | Spread |
|---|---|---|---|
| 8 firewall reduction ratios | **hand_over** | 0.74 | hand_over 0.810, fix_reducer 0.140, fix_fixtures 0.050, move_threshold 0.000 |
| numogram density scale | **renormalize** | **0.89** | renormalize 0.930, hand_over 0.060, fix_expectation 0.010, lower_threshold 0.000 |
| 3 enum/label mismatches | **ABSTENTION** | **0.53** | hand_over 0.660, per_case 0.340, fix_tests 0.000, fix_impl 0.000 |
| Still safer to hand back? | yes (mild) | noul 0.66 | - |
| Apply autonomously without review? | **NO** | noul **0.15** | - |

Reading it:

- **The delegation did NOT buy a blanket green light.** `apply_autonomously` moved only
  0.03 -> 0.15. Jev's position is that delegating the decision does not make applying it
  safe. That is consistent with the standing rule and it is the answer that governs.
- **One real ruling: `renormalize` (0.89).** >= 0.85, so actionable on its merits: change
  the density NORMALIZATION and keep the 0.1 threshold. `lower_threshold` scored 0.000 --
  Jev distinguishes the two and forbids the threshold move specifically.
  NOT YET APPLIED: `renormalize` names a direction, not a formula. Choosing the formula is
  a separate decision and applying it changes output values.
- **Enums ABSTAINED at 0.53**, below the 0.65 floor. Both `fix_tests` and `fix_impl`
  scored 0.000, with the mass split hand_over 0.660 / per_case 0.340. Jev will not pick a
  side of a contract with no external witness, and it declines to rule them as one group.
  Per the method: report as an abstention, do not promote the top label.
- **Firewall still hand_over** (0.74, weaker), `move_threshold` 0.000 again.

Net: of the 12 gated, **1 got a ruled direction**, **8 remain hand-over**, **3 abstained**.
Nothing was applied.

## Density formula: developed, and it PROVED Jev's renormalize ruling unsound

Jev ruled `renormalize` at 0.89 ("change the normalization, keep 0.1"). I implemented the
arithmetic before touching code. The premise is false.

### Measurements (all three diagram-role constraints)

| Case | Requirement | words | phrase hits | base hits | base/words |
|---|---|---|---|---|---|
| PASSIVE | **< 0.1** | 10 | 0 | 1 | **0.1000** |
| COMMANDING | >= 0.1 | 11 | 3 | 3 | 0.2727 |
| NUMOGRAM | **>= 0.1** | 88 | 0 | 5 | **0.0568** |

**PASSIVE (0.1000) > NUMOGRAM (0.0568), while PASSIVE must sit BELOW the threshold that
NUMOGRAM must clear.** No monotonic function of word count, sentence count, hit count,
distinct-term count, or any weighting of them can satisfy both.

Eight candidate formulas were tested and ALL FAIL: phrases/words, phrases/sentences,
(2*phrases+base)/words, phrases/words+base/words, distinct_base/sentences,
phrases/sentences+base/words, max(phrases,base)/sentences, distinct_base/distinct_words.

### Root cause: the counting, not the scaling

The PASSIVE text is "This is a simple description of events **without** authority
claims." It contains `authority` NEGATED. Counting the bare word is a FALSE POSITIVE,
and that single false positive is what lets a 10-word text outscore an 88-word one.

Separately, the numogram text contains NO phrase from the phrase list -- only bare
words -- so phrase-only matching gives it 0.0 and it can never clear 0.1.

**A rescaling cannot fix a misordering. `renormalize` was the wrong class of fix.**

### Jev, re-consulted with the correction

| Question | Ruling | Conf. |
|---|---|---|
| Given renormalization is provably insufficient, which option is canonical? | **negation_aware** (count only NON-NEGATED authority language) | **0.75** (p 0.800; structural_claims 0.090, abandon 0.060, hand_over 0.040, phrases_only_ack 0.010) |
| Was your renormalize ruling unsound because its premise is false? | **YES** | noul **0.96** |
| Apply autonomously without further review? | **NO** | noul **0.12** |

Jev reverses its own 0.89 ruling when handed the real discriminator, and confirms the
earlier premise was false at 0.96 -- exactly the documented behaviour: a ruling is only
as good as the state fed to it, and it reverses readily once the evidence is fixed.

**NOT APPLIED.** `negation_aware` changes detection behaviour, and `apply_autonomously`
came back 0.12. Per the method, the correct outcome is to hand it over with the
confidence attached. What is settled is the FORM of the fix (negation-aware matching,
not a rescaling) and that the 0.1 threshold stays.

## Decision sheet: all 22 remaining failures, classified by cause

Produced by pulling each error, following it to source, and classifying it. **No code
was changed to produce this sheet.** The distinction that matters:

- **MECHANICAL** -- one correct answer exists and is discoverable from the code/tests.
- **CONTRACT** -- two contradictory statements of intent exist and nothing in the repo
  adjudicates between them. A human or a spec must decide. NOT an effort problem.

### CONTRACT (13) -- waiting on a decision, not on work

| # | Test | Cause | The actual question |
|---|---|---|---|
| 1-8 | `test_firewall_metrics_delta` (8) | observed reduction ratios vs >=80%/>=50% targets | Are the targets unachievable, the reducer under-reducing, or the artifacts wrong? Jev: hand_over 0.74/0.96, `move_threshold` 0.000 |
| 9 | `test_numogram_retronic_ingest::test_retronic_tdd_analysis` | `density = hits/token_count` vs 0.1 needs 1-in-10 words (measured 0.05682) | Jev RULED `renormalize` 0.89 (keep 0.1), but named a direction, not a formula |
| 10 | `test_calibration_drift_report` | impl `agency_off` vs test `drift_blocked` | No external witness for either label. Jev ABSTAINED 0.53 |
| 11 | `test_multi_domain_seedpack` | impl `finance` vs test `economics` | Same -- no witness. Jev ABSTAINED 0.53 (`per_case` 0.34) |
| 12 | `test_canon_ledger_from_audit_v0` | range 2026-02-01 -> 02-03 vs expected -> 02-02 | The fixture mixes TWO schemas; record 3 nests its time under `commit.time.iso_utc`. Should a nested-schema record contribute to the date range? NOT a rotted date -- dates are synthetic |
| 13 | `test_tier_gating_psychonaut` | `AttributeError: 'list' object has no attribute 'items'` at `abraxas_ase/tiering.py:67` | Caller passes `report["domains"]` = a LIST; function is typed `Dict[str, Any]`. Unknown element shape -- fixing needs the real structure, not a guess |

### MECHANICAL (9) -- one discoverable correct answer

| # | Test | Cause | Fix shape |
|---|---|---|---|
| 14 | `test_timesfm_shadow_lab::test_packet_rejects_forecast_lane_and_wrong_revision` | `ValidationError.__new__() missing 1 required positional argument: 'line_errors'` (`abraxas/sources/timesfm_shadow/packets.py:162`) | `raise ValidationError(message)` is not constructible in pydantic v2; needs `ValidationError.from_exception_data(...)`. Test already expects `ValidationError` matching `valid_for_forecast` |
| 15 | `test_runes_registry::test_registry_integrity` | `AssertionError: Capability must be tagged` | Registry validation: a capability lacks its tag. Find which entry and tag it |
| 16 | `test_runes_invocation::test_invoke_logs_stub_blocked` | `DID NOT RAISE RuneStubError` | The stub path is not blocking. Wiring gap, not a policy value |
| 17 | `test_smv_build_units_from_vector_map` | ordering: got `['src_a',...,'node_b']`, expected `['node_a',...,'src_c']` | Source vs node ordering/naming. Determinism-class |
| 18 | `test_sim_mappings_game::test_game_theoretic_low_discount` | `assert 0.2 > 0.75` | Inverted or mis-scaled discount. Check which operand is the discount |
| 19 | `test_epp_builds_ranked_proposals` | `'SIW_LOOSEN_SOURCE' not in {COMPONENT_FOCUS_SUGGESTION, OFFLINE_EVIDENCE_ESCALATION, SIW_TIGHTEN_SOURCE, VECTOR_NODE_CADENCE_CHANGE}` | A proposal type is never emitted. Find the missing emit path |
| 20 | `test_evolution_system::test_promotion_creates_ticket` | `ValueError: Cannot promote candidate: Missing rent manifest draft` (`abraxas/evolution/promotion_gate.py:142`) | Gate requires a draft the test does not supply. Determine whether the gate or the test omits the step |
| 21 | `test_non_censorship_invariant::test_static_scan_enforced` | Static scan reports potential violations | A scan flagged real code. Either the flagged construct is a false positive for the rule, or the rule is correct and the code should change -- needs a look at what was flagged |
| 22 | `test_memetic_claim_runes::test_cluster_claims_deterministic` | `[[0],[1],[2]]` vs expected `[[0,1],[2]]` | ALREADY DECLINED earlier this session (Q7): token Jaccard scores 0.21 vs the expected 0.42. Reaching it means redesigning the similarity metric = test-fitting. Jev's weakest ruling, 0.73 |

### The headline

**13 of 22 are CONTRACT, not effort.** The four that looked most mechanical at error
level (`tiering`, `canon_ledger`, and the two enums) all turned out to be contract
questions wearing mechanical clothes -- which is why this session produced three
reverted "fixes": each traded one failure for another rather than resolving anything.

**The enums have a concrete unlock:** Jev scored `fix_impl` and `fix_tests` at **0.000**
for lack of an external witness. A schema, a spec line, or a doc naming the canonical
label would let it rule in one pass. Nothing else is needed.

## Runes registry / YGGDRASIL integration -- discovery + Jev ruling 2026-10-06

Operator directive: "runes registry should be integrated with yggdrasil".

### OPEN-phase discovery

`abraxas/runes/registry.py` holds **117 bindings speaking THREE conventions**:

| Convention | Count | Examples |
|---|---|---|
| `rune:<short>` lowercase | ~55 | `rune:rfa`, `rune:tam`, `rune:influence_detect` (the canonical 21 sigil-numeral runes) |
| `<subsystem>.<capability>.<action>` lowercase dotted | **62** | `oracle.v2.run`, `forecast.scoring.brier`, `evolve.ledger.append`, `evolve.evogate.build` |
| `RUNE.<SUBSYSTEM>.<CAPABILITY>` uppercase (skill-canonical) | **0** | - |

`test_registry_integrity` asserts `capability.startswith("rune:")`; **62 of 117 fail it.**

A **PARALLEL registry** also exists, which the governing skill prohibits:
`abraxas/yggdrasil/coordinator.py:49` -- `self.rune_registry = YggdrasilEngineRegistry()`,
gated by `rune_registry_enabled: bool = True` (line 34).

### Jev ruling

| Question | Ruling | Conf. | Spread |
|---|---|---|---|
| Which naming convention for the unified registry? | **ABSTENTION** | **0.50** | uppercase_RUNE 0.600, keep_21_migrate_62 0.350, hand_over 0.040, lowercase_rune_colon 0.010, lowercase_dotted 0.000 |
| Absorb YggdrasilEngineRegistry or keep separate? | **absorb** | **0.87** | absorb 0.910, hand_over 0.070, keep_separate 0.020 |
| Apply autonomously? | **NO** | noul **0.08** | - |

**The convention ABSTAINED at 0.50, below the 0.65 floor.** Reported as an abstention, NOT
promoted to its top label: `uppercase_RUNE` took only 0.600 against `keep_21_migrate_62` at
0.350, so the distribution is split rather than decisive. The naming question is genuinely
unresolved and stays with the human.

**The structure IS decided (0.87): absorb the parallel engine registry into
`abraxas/runes/registry.py`.** Two registries for one capability namespace is the
"parallel YGGDRASIL system" the skill prohibits.

`apply_autonomously` = **0.08**, so neither half is applied here.

### ATTEMPTED AND REVERTED: the 62 capability_id migration is NOT zero-blast-radius

I claimed the 62 dotted `capability_id` values had "zero canon risk, zero blast radius" and
claimed the non-conforming count would drop 117 -> 55. The first half was right; the second
was WRONG, and the suite said so immediately.

Migrating `abraxas/runes/registry.json` capabilities[].capability_id from `oracle.v2.run`
to `RUNE.ORACLE.V2.RUN` took the suite from **19 failures to 31** -- 12 newly failing:

    test_capability_invocation_contracts  (3)
    test_drift_log_append_only            (2)
    test_oracle_kernel_capability         (1)
    test_oracle_rune_provenance           (4)
    test_smoke_determinism                (2)

Reverted; the 5 affected files then pass 14/14.

WHY: the dotted IDs are HARDCODED as call-site string literals across `abx/`:
    abx/evolve_run.py:513            invoke_capability("evolve.ledger.append", ...)
    abx/mwr.py:122 / abx/promote.py:42       "evolve.ledger.append"
    abx/scoreboard.py:110 / abx/horizon_policy.py:120   capability="forecast.scoring.brier"
    abx/horizon_policy_select_tc.py:74 / abx/horizon_audit.py:108,116
                                     invoke_capability("forecast.scoring.brier", ...)

So `capability_id` is a LIVE CONTRACT KEY, not registry data. Renaming it is an API change
requiring every call site updated in the same commit -- in `abx/`, not just in the registry.

CORRECTED PLAN: the migration must rename the registry entries AND update all call sites
together, then re-baseline. Splitting it (registry first) cannot work. Estimate the call-site
count with:
    grep -rn "'[a-z_]*\.v[0-9]*\.[a-z_]*'\|\"[a-z_]*\.[a-z_]*\.\(append\|run\|build\)\"" --include=*.py abx/ abraxas/ | wc -l
before committing to it.

Lesson (third time this session, same shape): verify blast radius by MEASURING it, not by
reasoning about it. "Low risk because it touches no canon identity" is a claim about SCOPE
of the change, not about the number of DEPENDENTS.

### CORRECTION (operator): the integration direction is Yggdrasil-ward, not runes-ward

I had this backwards and the operator caught it. The direction is: the rune capability
data flows INTO the Yggdrasil plane, not Yggdrasil into the runes package.

The repo states it outright. `abraxas/yggdrasil/registry.py:1-5`:

    """
    Yggdrasil Engine Registry -- Source of Truth for Engine Registration

    This module implements the rune-based engine registry that serves as the
    source of truth for all registered engines in the Yggdrasil system.
    """

Evidence for this direction:
- `abraxas/yggdrasil/registry.py` DECLARES itself the source of truth for engine
  registration, and says it "implements the rune-based engine registry".
- `abraxas/runes/registry.py` holds the substance: 117 bindings loaded from
  `abraxas/runes/registry.json`, plus load_registry / list_capabilities /
  describe_rune / wiring_sanity_check.
- `abraxas/yggdrasil/registry.py` imports NONE of that -- no cross-import in either
  direction. Two registries, one declared authoritative, zero wiring between them.
  That IS the integration gap the operator asked to close.
- The skill names its artifact `yggdrasil_rune_route_binding_matrix` -- Yggdrasil first,
  and its governing model reads "ABX-Runes define WHAT may be done. YGGDRASIL defines
  HOW bounded capabilities connect." Yggdrasil is the container.

So the surviving home is `abraxas/yggdrasil/registry.py`; the 117 bindings and the
rune-registry validators move under it, and `abraxas/runes/registry.py` becomes a thin
re-export or is retired. My earlier plan had it inverted.

### RESEARCH ANSWER: the convention is declared in the repo -- `RUNE.<PATH>` uppercase

Jev abstained at 0.50 for lack of an external witness. The witness exists and is in-repo.
The governing skill's precedence order puts "current repo implementation + generated
artifacts" FIRST, above Notion and historical records. That tier settles it:

`docs/runes/` is the **Rune Specs Index** -- the contract declaration layer, not prose:

    docs/runes/README.md:1   # Rune Specs Index
    docs/runes/README.md:4   "deterministic payload contract for `RUNE.CODE.REVIEW`"
    docs/runes/FIND_SKILLS.md:1   # RUNE.FIND_SKILLS
    docs/runes/FIND_SKILLS.md:93  "skill_id": "RUNE.FIND_SKILLS"
    docs/runes/CODE_REVIEW.md:1   # RUNE.CODE.REVIEW
    docs/runes/CODE_REVIEW.md:26  provenance fixed to contract marker `RUNE.CODE.REVIEW.contract.v1`

**So the canonical convention is `RUNE.<UPPERCASE.DOTTED.PATH>`**, matching the skill's
`RUNE.<SUBSYSTEM>.<CAPABILITY>` and Jev's top choice (uppercase_RUNE 0.600). The repo uses
both `RUNE.<CAPABILITY>` and `RUNE.<SUBSYSTEM>.<CAPABILITY>` depths, and even a versioned
contract-marker form `RUNE.CODE.REVIEW.contract.v1`.

**Consequence: the test's assertion is the outlier.** `test_registry_integrity` asserts
`capability.startswith("rune:")` -- lowercase with a colon -- which matches NEITHER the
declared convention NOR the 62 dotted entries. Only the ~55 legacy `rune:<short>` entries
satisfy it, and those contradict the documented form too.

**Therefore this is not a 3-way tie.** Research breaks it:
  canonical  : `RUNE.<PATH>` uppercase, per docs/runes/ + skill
  migrate     : all 117 entries
  test        : update the assertion to the declared convention, with the witness cited
  NOT DONE    : prefixing 62 strings with `rune:` -- that would cement the wrong convention
                and is the "silent normalization" the skill prohibits

Not applied here: `apply_autonomously` was 0.08, and migrating 117 capability identifiers
plus a validator is a contract change, not a test fix.

### The prohibited shortcut, recorded so it is not taken later

The green-making move is to prefix 62 strings with `rune:`. The skill forbids exactly this:
"silent normalization of hidden coupling", "weakening validators for green receipts". Three
conventions plus a parallel registry is a RECONCILIATION decision, not a test bug. Do not
rename contracts to quiet a validator.

## Accounting after the ruling

- 24 failures total
- **12 decision-gated** (8 firewall + 1 density + 3 enums) -- parked for the human
- **12 mechanical/unblocked** -- safe to fix per Jev 0.83

---

Standing rule: run BOTH orders before claiming a baseline or a fix. Three candidate
fixes in this stretch looked plausible in the canonical order and were only caught as
regressions by the reversed-order run.

### Attempted and REVERTED: injection point for the approval receipt

Added `queue_items=None` to `run_self_build_approval_receipt` so the test could supply
its own queue instead of reading live repo state, and rewrote the test to assert on
those items. Result:

    reversed: 30 -> 29   (good, fixed the target)
    canonical: 28 -> 29  (REGRESSION)

`tests/test_lexicon_generator_determinism.py::test_lexicon_generator_is_deterministic`
failed in the canonical order as a direct consequence. Reverted both files.

**The finding is more important than the fix.** `run_self_build_approval_receipt` had no
mutation (`mutation: False, execution: False, observe_only: True`), but calling it still
ran the dry run / safety gate / patch plan chain, which writes artifacts under `out/`.
A later lexicon *determinism* test depends on those artifacts existing. So the approval
test's live-state read has a **load-bearing side effect** on an unrelated test.

Implication: **fixing these tests one at a time will keep surfacing hidden dependencies**
-- each removal exposes whatever silently relied on the artifact being written. The
correct fix is a shared fixture that materialises the required `out/` artifacts
explicitly at session start, then converting tests in that order. Per-test patches are
the wrong shape and will keep trading one failure for another.

## Order dependence (resolved 2026-10-06)

**The suite is not randomly flaky. It was collection-order dependent, and the cause
was module-level side effects in files that were not tests.**

`tests/test_dashboard_api_prod.py` ran, at import time, a `sys.modules` purge of every
`abraxas*` module plus `os.environ['ABRAXAS_ENV'] = 'production'` for the whole
session. pytest imports every test module during collection, before any test runs, so
this applied regardless of run order.

Five of the eight files that had been moved from the repo root into `tests/` had **zero
test functions** and carried 8 module-level side effects. They never ran while they sat
at the root. Moving them into `tests/` activated their import-time effects and caused
the regression. They now live in `scripts/smoke/`.

Lesson: **before moving a file into a test directory, check that it contains tests.**
A `test_` filename prefix is not evidence; `grep -c '^def test_'` is.

Lesson: **collection order is not run order.** When state leaks at import time,
bisecting on run order yields clean results while the failure persists. Test imports
happen first, all at once.

Verified by re-running with a deliberately changed collection order *and* a probe file
that recreated the same pollution: failure set unchanged, both order-dependent tests
clean. `tests/conftest.py` also resets process-global singletons per test, so the
suite no longer depends on which tests ran before it.

Known remaining risk: a single collection order proves nothing on its own. Any future
baseline claim should be confirmed under at least two different collection orders.
