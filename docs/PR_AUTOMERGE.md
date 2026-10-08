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

## Board movement is GitHub's built-in automation — there is no workflow for it

`.github/workflows/auto-move.yml` was **DELETED** on 2026-10-08. GitHub Projects v2 automates
this server-side, with no Actions workflow, no `GITHUB_TOKEN`, and no PAT.

Two of the board's built-in workflows do all of it (both enabled on Kanban, project 7):

- **Auto-add to project** — filter `is:issue,pr is:open`. Adds matching issues and PRs to the
  board as they are opened or updated.
- **Pull request merged** — action `Set value: Status: Done`. Moves the item to Done when its
  pull request is merged. (`Item closed` does the same for closed issues.)

### Why the workflow went away

It existed because the board did not, and it had never once succeeded:

- It drove GitHub **Projects (classic)** through `alex-page/github-project-automation-plus`,
  targeting a project named "Kanban" with To Do / In Progress / Done columns. Projects classic
  is retired — the REST endpoint returns 404 — and no such project existed.
- Rewritten against Projects v2 it then failed on the **token**: `GITHUB_TOKEN` is
  repository-scoped and cannot reach the Projects v2 API at all, and for a **user-owned**
  project the only supported credential is a **classic** PAT with the `project` scope
  (fine-grained tokens do not support user-owned projects). The `ABRAXAS_PAT` fallback was
  present but insufficient — measured: `gh project item-add` failed with `unknown owner type`.

Requiring a long-lived PAT on a personal account to move a card was the wrong trade, so the
built-in workflows were enabled instead. Note there is **no API path to do that**: the GraphQL
schema exposes only `deleteProjectV2Workflow` — no create or enable mutation — so it is a UI
action (project → ⋯ → Workflows → Auto-add to project → Edit → Save and turn on workflow).

Net effect: one fewer workflow, no secret, and no red run on every merge.

## Usage

Label a docs-only PR `docs` + `automerge`. If the path gate passes, the workflow arms squash auto-merge. Remove either label to disarm.

Runtime, rune, contract, and governance PRs stay manual.
