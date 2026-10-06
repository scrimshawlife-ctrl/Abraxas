# Test Debt Inventory

Baseline as of 2026-10-05: **57 failed / 3244 passed / 4 skipped**.

This file is the human-readable companion to `scripts/test_ratchet.sh`. When a cluster is
resolved, lower `BASELINE_FAILURES` in that script and update the matching row here **in the
same commit**.

## Decision-gated (no code until a ruling lands)

| Cluster | Tests | Question | Evidence |
|---|---|---|---|
| Reverse coupling | 1 | Allowlist `abraxas/evidence/legacy/`, refactor it, or delete it? | 41 new `abraxas/* → abx.*` import violations, 40 of them in that one package. The *other* coupling test passes (34 actual vs an 81 ratchet) — do not conflate the two. |
| Firewall response mode | 8 | Are the 80%/50% reduction thresholds canonical, or are the transformations under-powered? | Modals 50% observed vs ≥80% expected; closure terms 0% vs ≥80% and 10% vs ≥50%; causality inversion 16.7% vs ≥80%; `DE_ESCALATE` yields `-0.0` (no reduction at all). |
| Governance / policy scans | 9 | Does the rule move, or does the artifact? | `metric_governance` (3), `oas_vbm_golden_gate` (3), `governance_lint_consolidated` (3), plus `non_censorship_invariant`, `see_vbm_drift_tagging`. Loosening any of these to go green is the most damaging available action — flag, do not fix. |
| Doc contracts | 2 | Restore the documented strings, or retire the tests? | Required strings (`make proof RUN_ID=<RUN_ID>`, `OperatorProjectionSummary.v1`) are absent from `README.md` at `origin/main` too — pre-existing drift, not a regression. |
| Analysis content | 6 | Which analysis is correct? | `numogram_retronic_ingest` (3), `memetic_claim_runes` (2), `sim_mappings_game` (1), `timesfm_shadow_lab` (1). |
| Unclassified singles | 22 | Characterise, then map to a cluster above | Collapse signatures: `python -m pytest tests/ -q --no-header --tb=line 2>&1 \| grep -E "^E " \| sed -E "s/'[^']*'/'X'/g" \| sort \| uniq -c \| sort -rn` |

## Already ruled by Jev — do not re-open without new evidence

| Cluster | Ruling | Confidence |
|---|---|---|
| `self_build_*` statefulness (8 tests) | leave as-is | 0.84 |
| Regenerated rune sigils | keep reverted | 0.94 |
| `evidence_completeness` 0.80 boundary | keep 0.80 | 0.93 |

## Recorded faults in the tests themselves

These are genuine defects **in the tests**, not in the runtime. They change no production
behaviour and are safe to fix without a ruling.

| Test | Defect |
|---|---|
| `tests/test_no_regress_guardrail.py:75,79` | `case.dict()` hands `yaml.safe_dump` a Pydantic v2 enum object → `RepresenterError`. Use `model_dump(mode="json")`. |
| `tests/test_sigils_determinism.py:168` | Frozen `== 21` count of rune definition files; 63 now exist. Should assert the canonical set as a floor. |
| `tests/test_score_aggregate_shape.py:58` | Exact `==` comparison of a computed mean → IEEE-754 noise. Use `pytest.approx`. |
| `tests/test_manifest_integrity.py` (`test_builder_check_passes`) | Red on builder-version sigil drift; Jev ruled `keep_reverted`. Marked `xfail(strict=True)`. |

## Resolved

| Date | Commit | Fix | Failures cleared |
|---|---|---|---|
| 2026-10-05 | `e5e69252` | Misplaced `from __future__`, `use_enum_values` `.value` bugs, shadow-detector contract, undeclared `RunState.ledger_events` | 62 |
| 2026-10-05 | `0ac8545a` | `MappingResult.input_params`, forecast provenance aliases, `DomainRegistryV1` defaults + method API | 10 |
| 2026-10-05 | `410addf9` | 4 non-UTF-8 files; corrupted rune IDs | 3 |
| 2026-10-05 | `4706e8b4` | MDA envelope coercion, canonical subdomain payload shape, no-domain-prior, wired `run_tvm_shadow_flow` | 2 |

Session total: **134 → 57 failures, zero regressions.**

## Rules

- Never move a behavioural threshold, policy constant, or scan rule to make a test green.
- Never hand-write a `NOT_COMPUTABLE` artifact (or any other state) to revive a stateful test.
- Never regenerate canon artifacts (sigils, manifests, generated operators) unilaterally.
- `out/`, `data/`, `.aal/`, `.abraxas/` are tracked but rewritten by every test run.
  **Never `git add` them.**
- Prove zero regressions after every batch by set-diffing failure lists.
