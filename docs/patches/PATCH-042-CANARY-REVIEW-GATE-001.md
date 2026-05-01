# PATCH-042 — CANARY-REVIEW-GATE-001

## purpose
Convert canary overlay simulation outputs into deterministic review recommendations for activation review gating.

## authority boundary
Review-only surface. This patch does not activate overlays, mutate baselines, write runtime config, modify ledger statuses, promote entities, execute strategies, or start schedulers.

## threshold logic
- `min_scores_used = 3`
- `min_improvement_delta = -0.01`
- `max_worsening_delta = 0.01`

Decision path:
- simulation not computed => `not_computable`
- insufficient scores => `recommend_hold`
- delta <= improvement threshold => `recommend_approve_for_activation_review`
- delta > worsening threshold => `recommend_reject`
- otherwise => `recommend_hold`

## recommendation states
- `recommend_approve_for_activation_review`
- `recommend_hold`
- `recommend_reject`
- `not_computable`

## lineage behavior
Each recommendation carries lineage to overlay id, simulation hash, optional ledger entry hash, and optional proposal id.
Missing overlay forces `not_computable` with `missing_overlay`.
Missing ledger entry preserves computed status but appends `|missing_ledger_entry`.

## no activation rule
`recommend_approve_for_activation_review` means review eligibility only; it is never an activation action.

## next patch
PATCH-043 CANARY-ACTIVATION-PACKET-001
