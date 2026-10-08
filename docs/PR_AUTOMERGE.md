# PR automerge (docs only)

Fail-closed. This is not blanket merge automation.

## What it does

Workflow `.github/workflows/pr-automerge-docs.yml` enables GitHub **squash auto-merge** when all of the following hold. The job does not check out the repo; `gh` is pinned with `GH_REPO` / `--repo` so a missing `.git` directory cannot fail the skip path.

- PR targets `main`
- PR is not a draft and is not from a fork
- Labels `docs` **and** `automerge` are present
- Every changed path is on the allowlist
- GitHub auto-merge is allowed in repo Settings → Pull Requests

Required checks still have to pass. Auto-merge waits. It does not skip CI.

## Allowlist

- `docs/**`
- `README.md`
- `CHANGELOG.md`
- `LICENSE`
- `MEMORIES.md` / `PLANS.md` / `STATUS.md` / `QUICKSTART.md` if present

## Blocked (never auto-merged)

`.abraxas/`, `abx/`, `abraxas/`, `core/`, `contracts/`, `scripts/`, `tests/`, `.github/`, runtime/UI trees, schemas.

A PR that adds this workflow cannot auto-merge itself.

## Operator setup (once per repo)

1. Settings → General → Pull Requests → **Allow auto-merge**
2. Prefer squash merge for `main`
3. Create labels `docs` and `automerge`
4. Put required status checks on `main` if they are not already required

### Setup status (2026-10-08)

Steps 1 and 3 were outstanding and are now DONE; steps 2 and 4 were already in place.

- **Step 1 — auto-merge: ENABLED.** `allow_auto_merge` was `false`, so `gh pr merge --auto`
  in the workflow could never complete: GitHub rejects it outright with auto-merge disabled.
  The workflow was therefore inert even on a correctly labelled, allowlisted PR.
  Verified: `gh api repos/<owner>/<repo> -q .allow_auto_merge` → `true`.
- **Step 3 — labels: CREATED.** Neither `docs` nor `automerge` existed (the repo carried only
  the GitHub defaults plus `codex`). The workflow's gate requires both literal names, so
  **no PR could ever satisfy it** — the job always took the `skip: missing label docs` path.
  Both labels now exist with descriptions naming their purpose.

Worth stating plainly, because it is the same failure mode twice: a workflow can be
registered, "active", and permanently incapable of doing its job — first because a required
repo setting was off, and again because its gate keys on labels that were never created.
Neither shows up as a failure; both look like a skip.

## Known interaction: an auto-merged PR does NOT run `auto-move`

Measured 2026-10-08, and it is a GitHub rule rather than a bug in either workflow:

> Events triggered by the repository's `GITHUB_TOKEN` do not create new workflow runs.

Auto-merge is performed **by `GITHUB_TOKEN`** (the merge on #266 is attributed to
`app/github-actions`). So when this workflow merges a docs PR, the `pull_request: closed`
and `push` events it produces are suppressed, and `auto-move.yml` **never fires**. Neither
does `ci.yml`, `abraxas-repo-guardrails.yml` or `abx_familiar_canary.yml`.

Evidence, same repository, same day:

- PR #266 — merged by `app/github-actions` via auto-merge → merge commit `59e09f63` has
  **zero** workflow runs of any kind.
- Main commit `8f933489` — pushed by a personal access token → `CI`,
  `abraxas-repo-guardrails` and `abx-familiar canary` all ran.
- PR #265 — **closed** (not merged) by a PAT → `auto-move` did fire (and correctly skipped,
  because `merged == true` was false).

Two consequences worth deciding on deliberately:

1. **`auto-move` and docs auto-merge cannot both apply to the same PR.** A PR merged by the
   docs gate will not be added to the Kanban board.
2. **The merge commit on `main` gets no verification run.** The PR's required checks passed
   before merging, so the gate held; but the commit that actually lands is not itself
   re-tested. With `strict: false` on `main` that is accepted today.

If chaining is wanted, the merge must be performed by a non-`GITHUB_TOKEN` actor — i.e. arm
auto-merge with a PAT secret instead of `secrets.GITHUB_TOKEN`. That is a credential change
and a decision, not a fix to apply silently.

## Sibling automation: `auto-move.yml` (Projects v2)

`.github/workflows/auto-move.yml` adds a **merged** PR to the GitHub Projects v2 board
**Kanban** (owner `scrimshawlife-ctrl`, project number 7) and sets its Status to `Done`.
It is unrelated to the docs-merge gate above; it fires on any PR merged to `main`.

It previously drove GitHub **Projects (classic)** through
`alex-page/github-project-automation-plus`, targeting a project named "Kanban" with
To Do / In Progress / Done columns. Projects classic is retired (the REST endpoint now
returns 404) and no such project existed, so it had never succeeded. It was rewritten
against Projects v2 and the board was created.

**Token requirement — this is a hard constraint, not a preference.** The job uses
`secrets.PROJECT_TOKEN || secrets.ABRAXAS_PAT`, because `GITHUB_TOKEN` is scoped to the
repository and cannot read or write the Projects v2 API at all. For **user-owned** projects
— and this owner is a user, not an organization — the only supported credential is a
**classic** personal access token with the **`project`** scope; fine-grained tokens do not
support user-owned projects. If neither secret carries that scope, the job fails with a
message naming the required scope rather than a cryptic `Could not resolve to a ProjectV2`.

## Usage

Label a docs-only PR `docs` + `automerge`. If the path gate passes, the workflow arms squash auto-merge. Remove either label to disarm.

Runtime, rune, contract, and governance PRs stay manual.
