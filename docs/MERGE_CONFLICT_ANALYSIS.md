# Merge Conflict Analysis Report

**Generated:** 2026-01-25
**Analyzed by:** Claude (Automated)
**Total Remote Branches:** 61
**Branches with Conflicts:** 16

---

## Executive Summary

This report analyzes all remote branches in the Abraxas repository for merge conflicts with main. The analysis identified 16 branches with active conflicts requiring resolution.

### Quick Stats

| Category | Count |
|----------|-------|
| Total branches | 61 |
| Branches with conflicts | 16 |
| Already merged (0 ahead) | ~45 |
| Simple conflicts (1-3 files) | 4 |
| Complex conflicts (>10 files) | 5 |
| Stale branches (>200 behind) | 3 |

---

## Resolution Status

### ✅ Resolved and Pushed

| Original Branch | Resolution Branch | Conflicts | Resolution |
|-----------------|-------------------|-----------|------------|
| `codex/integrate-ase-into-existing-anagram-subsystem-axpecm` | `claude/resolve-ase-integration-Lx7pV` | README.md | Kept Table of Contents from main |
| `codex/continue-implementation-according-to-claude.md` | `claude/resolve-codex-impl-Lx7pV` | horizon_policy_select.py (3) | Kept `stats_ctx` parameter naming |

**Ready for PR:** Both resolution branches are pushed and ready to create PRs to main.

### ⚠️ Complex - Needs Author Rebase

| Branch | Conflicts | Recommendation |
|--------|-----------|----------------|
| `claude/continue-work-ILQQS` | 19 files | Original author should rebase; contains significant ABX-Runes coupling work |
| `claude/continue-todo-list-tCX95` | 27 files | Original author should rebase; forecast capabilities branch |

### 📦 Duplicate/Superseded Branches

The following branches appear to be duplicates or have been superseded:

| Branch Group | Count | Recommendation |
|--------------|-------|----------------|
| `codex/integrate-ase-*` | 3 branches | Keep `axpecm` (has cleanup commit), close others |
| `cursor/mda-*` | 5 branches | MDA content already in main; review for unique features then close |

---

## Detailed Conflict Analysis

### Priority 1: Recent & Close to Main

These branches have minimal divergence and should be resolved first:

| Branch | Ahead | Behind | Files Changed | Conflict Files |
|--------|-------|--------|---------------|----------------|
| `codex/integrate-ase-into-existing-anagram-subsystem` | 1 | 4 | 79 | README.md, CHANGELOG.md, Makefile |
| `codex/integrate-ase-into-existing-anagram-subsystem-axpecm` | 1 | 4 | 79 | README.md (RESOLVED) |
| `codex/integrate-ase-into-existing-anagram-subsystem-kg1iir` | 1 | 4 | 79 | README.md, CHANGELOG.md, Makefile |

**Feature:** Chronoscope time-series and watchlist tooling for Anagram Sweep Engine (ASE)

### Priority 2: Active Development

| Branch | Ahead | Behind | Conflicts | Key Changes |
|--------|-------|--------|-----------|-------------|
| `codex/continue-implementation-according-to-claude.md` | 1 | 48 | 1 | horizon_policy_select.py (RESOLVED) |
| `claude/continue-work-ILQQS` | 7 | 76 | 19 | ABX-Runes coupling elimination, fn_exports move |
| `claude/continue-todo-list-tCX95` | 11 | 120 | 27 | Forecast capabilities, policy candidates |
| `cursor/claude-md-review-and-next-steps-17c4` | 3 | 124 | ~10 | Forecast runes integration |

### Priority 3: MDA Feature Branches

All 5 branches are from 2026-01-02 and 177 commits behind. MDA content is **already in main** with 16+ Python files.

| Branch | Feature | Unique Content |
|--------|---------|----------------|
| `cursor/golden-hash-pinning-and-drift-8ddc` | MDA practice rig | drift_classifier.py, ledger.py |
| `cursor/mda-run-ledger-replay-0582` | Deterministic execution | adapters/base.py, replay.py, budget.py |
| `cursor/mda-sandbox-enhancements-6899` | Sandbox package | None (already in main) |
| `cursor/mda-v1-1-sandbox-runner-eae8` | Types and init | None (already in main) |
| `cursor/oracle-batch-packet-runner-06ef` | Oracle batch processing | None (already in main) |

**Recommendation:** Review `mda-run-ledger-replay-0582` for replay.py, budget.py, toggles.py features. Close other MDA branches.

### Priority 4: Stale Branches (>200 Behind)

These branches are significantly behind main and their features may need to be re-implemented:

| Branch | Behind | Ahead | Last Activity | Status |
|--------|--------|-------|---------------|--------|
| `claude/deterministic-logging-compression-V4K0p` | 387 | 1 | 2025-12-17 | Consider closing |
| `claude/add-v2-stability-guard-LpFRP` | 282 | 1 | 2025-12-28 | Consider closing |
| `claude/resonance-narratives-renderer-4N4Nj` | 199 | 1 | 2025-12-30 | Review for roadmap feature |

---

## Recommended Actions

### Immediate (Do Now)

1. **Merge resolved branches:**
   - `resolve-ase-conflicts` (local) → PR to main
   - `resolve-codex-impl` (local) → PR to main

2. **Close duplicate ASE branches:**
   - Close `codex/integrate-ase-into-existing-anagram-subsystem`
   - Close `codex/integrate-ase-into-existing-anagram-subsystem-kg1iir`

### Short-term (This Week)

3. **Author rebase required:**
   - Contact author of `claude/continue-work-ILQQS` for rebase
   - Contact author of `claude/continue-todo-list-tCX95` for rebase

4. **Review and close MDA branches:**
   - Extract unique features from `mda-run-ledger-replay-0582` if valuable
   - Close all 5 cursor/mda-* branches

### Medium-term (This Sprint)

5. **Evaluate stale branches:**
   - `claude/resonance-narratives-renderer-4N4Nj` - Check against roadmap
   - `claude/deterministic-logging-compression-V4K0p` - Re-implement if needed
   - `claude/add-v2-stability-guard-LpFRP` - Re-implement if needed

---

## Branch Cleanup Commands

```bash
# Close duplicate ASE branches (after merging axpecm)
git push origin --delete codex/integrate-ase-into-existing-anagram-subsystem
git push origin --delete codex/integrate-ase-into-existing-anagram-subsystem-kg1iir

# Close superseded MDA branches
git push origin --delete cursor/mda-sandbox-enhancements-6899
git push origin --delete cursor/mda-v1-1-sandbox-runner-eae8
git push origin --delete cursor/oracle-batch-packet-runner-06ef

# After review, optionally close:
git push origin --delete cursor/golden-hash-pinning-and-drift-8ddc
git push origin --delete cursor/mda-run-ledger-replay-0582
```

---

## Files Requiring Manual Review

The following files have complex conflicts in multiple branches:

| File | Branches with Conflicts |
|------|------------------------|
| `abraxas/runes/registry.json` | continue-work-ILQQS, continue-todo-list-tCX95 |
| `abx/horizon_policy_select.py` | continue-implementation, continue-todo-list-tCX95 |
| `CLAUDE.md` | continue-todo-list-tCX95 |
| `README.md` | integrate-ase-*, continue-todo-list-tCX95 |

---

## Methodology

This analysis was performed by:

1. Fetching all remote branches
2. Using `git merge-tree` to detect conflicts without modifying working tree
3. Counting commits ahead/behind using `git rev-list`
4. Examining conflict patterns in priority branches
5. Creating local resolution branches for simple conflicts

---

**Last Updated:** 2026-01-25T03:30:00Z
