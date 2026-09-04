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

## Usage

Label a docs-only PR `docs` + `automerge`. If the path gate passes, the workflow arms squash auto-merge. Remove either label to disarm.

Runtime, rune, contract, and governance PRs stay manual.
