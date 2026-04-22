# RUNE.CODE.REVIEW

## Scope
Repository-backed deterministic contract for code-review payload shape.

## Current lane
- Contract status: `candidate`
- Execution mode: `shape_only`
- Authority: non-promotive, non-analytical contract validation only.

## Input schema
- `schemas/CodeReviewInput.v1.json`
- Requires `code_input`, `context`, `include_patch_plan`.
- `context.rule_set_version` is fixed to `code_review_contract.v1`.

## Output schema
- `schemas/CodeReviewOutput.v1.json`
- `status`: `OK | NOT_COMPUTABLE`
- `issues[]` with deterministic severity enum:
  - `LOW`
  - `MEDIUM`
  - `HIGH`
  - `CRITICAL`
- `summary` with `issue_count` and `max_severity`
- Optional `patch_plan`
- `provenance` fixed to contract marker `RUNE.CODE.REVIEW.contract.v1`

## Non-claims
This contract does **not** assert live static analysis, semantic linting, or AI review execution.
