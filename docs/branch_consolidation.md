# Branch consolidation notes (repo cleanup)

This repo has accumulated a large number of long-lived remote branches. Most are **already merged into** `origin/main` and can be deleted safely.

## Current state (observed in this workspace)

- **Current branch**: `cursor/repository-cleanup-and-consolidation-9b7f`
- **HEAD commit**: matches `origin/main`
- **Local `main`**: stale (behind `origin/main`)

## Recommended consolidation workflow

1. Fetch + prune remote refs.
2. Delete **remote branches that are fully merged** into `origin/main`.
3. For **branches not merged** into `origin/main`, decide one of:
   - Merge via PR (if still desired)
   - Cherry-pick the relevant commits into a fresh branch/PR
   - Close/archive and delete (if superseded)

## Script

Use:

- `scripts/branch_cleanup.sh` (dry-run by default)
- Deletion requires `--apply` plus `ABRAXAS_BRANCH_CLEANUP_I_UNDERSTAND=1`

Example:

```bash
scripts/branch_cleanup.sh
ABRAXAS_BRANCH_CLEANUP_I_UNDERSTAND=1 scripts/branch_cleanup.sh --apply
```

## Branches merged into `origin/main` (safe-to-delete candidates)

Run `scripts/branch_cleanup.sh` to compute the up-to-date list.

In this workspace snapshot, the following remote branches were reported as merged into `origin/main`:

- `origin/claude/abraxas-kernel-phases-9pstC`
- `origin/claude/abraxas-update-agent-01FAnGu9i2fkfX43Lpb3gP85`
- `origin/claude/abraxas-v1-4-implementation-k7dXE`
- `origin/claude/abraxas-weather-engine-01YWYLe1669KCS16cZBNxNea`
- `origin/claude/add-abraxas-overlay-module-EmBu1`
- `origin/claude/add-ascend-operations-xW1oQ`
- `origin/claude/add-sig-kpi-metrics-nr89w`
- `origin/claude/emergent-metrics-shadow-kK1ZW`
- `origin/claude/find-claude-md-path-nEIIy`
- `origin/claude/lock-cambridge-metrics-oospI`
- `origin/claude/memory-governance-layer-01YaacBrXTedWkvpipmJJ2Ht`
- `origin/claude/merge-pull-requests-xCwWp`
- `origin/claude/oracle-runes-integration-Ndxzr`
- `origin/claude/patch-17-typed-inputs-YUkl2`
- `origin/claude/rent-enforcement-v0-1-jyl9I`
- `origin/claude/resolve-merge-conflicts-a9OJO`
- `origin/claude/shadow-detectors-lane-guard-kMgTZ`
- `origin/claude/slang-signal-schema-sAZ0H`
- `origin/codex/add-bell-constraint-canon-entry-and-abx-rune`
- `origin/codex/add-horizon-bands-and-forecasting-module`
- `origin/codex/align-abraxas-kernel-contract-and-artifacts`
- `origin/codex/enforce-non-censorship-invariant-in-codebase`
- `origin/codex/implement-canonical-daily-run-orchestrator`
- `origin/codex/implement-im.rfc-in-metric-registry`
- `origin/codex/refactor-code-for-improvements`
- `origin/cursor/artifact-dashboard-subsystem-3b9d`
- `origin/cursor/pull-request-conflict-resolution-5149`

## Branches NOT merged into `origin/main` (needs review)

These branches were reported as not merged into `origin/main` and appear to be **older divergence bases** with commits that may now be superseded by later work:

- `origin/claude/add-v2-stability-guard-LpFRP` (unique changes in `abraxas/oracle/v2/`)
- `origin/claude/cli-api-routes-yu5jS` (adds FastAPI + Postgres storage wiring)
- `origin/claude/deterministic-logging-compression-V4K0p` (adds `abx/log/*`)
- `origin/claude/integrate-oasis-slang-crcWI` (large OAS/TDD + casebooks)
- `origin/claude/lexicon-oracle-v1-H2GcG` (Postgres wiring + correlation engine)
- `origin/claude/resolve-merge-conflicts-Vg6qy` (merge-resolution branch; likely delete)
- `origin/claude/resonance-narratives-renderer-4N4Nj` (older resonance renderer)
- `origin/cursor/dashboard-artifact-viewer-99fe` (older dashboard lens viewer)

For each, prefer: extract the still-relevant bits into a new PR targeting current `origin/main`, rather than merging the entire branch history.
