# Test Debt Inventory

Baseline as of 2026-10-05 (after the Phase 1/2 remediation): **42 failed / 3250 passed /
4 skipped / 9 xfailed**.

This file is the human-readable companion to `scripts/test_ratchet.sh`. When a cluster is
resolved, lower `BASELINE_FAILURES` in that script and update the matching row here **in the
same commit**.

## Ruled by Jev, NOT YET APPLIED (behaviour-changing — needs a human go)

Jev answered all of these, but then returned `noul = 0.13` on *"is it safe for the agent to
apply these rulings autonomously, without further human review"*. So they are recorded and
parked, not executed. Applying any of them changes runtime behaviour.

| Cluster | Tests | Jev's ruling | Confidence |
|---|---|---|---|
| Reverse coupling | 1 | `delete_legacy_package` — `abraxas/evidence/legacy/` has no importers and is in no registry | 0.85 |
| Sandbox override maps | 1 | `override_else_evaluate` — treat an override as per-case, else evaluate normally | 0.85 |
| `SandboxResult` None floats | 1 | `make_optional` — make the score fields `Optional[float]` to match what producers emit | 0.88 |
| Analysis content | 7 | `trust_expected_values` — update the implementation to match recorded expectations | 0.73 |
| Governance / policy scans | 12 | `fix_artifacts` — keep every rule, correct the artifacts | 0.94 |

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

Session total: **134 → 42 failures, zero regressions.**

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
