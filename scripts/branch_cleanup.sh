#!/usr/bin/env bash
set -euo pipefail

REMOTE="origin"
BASE_REF="origin/main"
APPLY="false"

usage() {
  cat <<'EOF'
Branch cleanup + consolidation helper for Abraxas.

What it does:
- Fetches and prunes remote refs
- Lists remote branches that are already merged into origin/main (safe-to-delete candidates)
- Lists remote branches that are NOT merged (need review/merge/close)

By default this is DRY-RUN (prints what it would delete).

Usage:
  scripts/branch_cleanup.sh [--remote origin] [--base origin/main] [--apply]

Safety:
  To actually delete remote branches you MUST:
    - pass --apply
    - set ABRAXAS_BRANCH_CLEANUP_I_UNDERSTAND=1

Examples:
  scripts/branch_cleanup.sh
  scripts/branch_cleanup.sh --remote origin --base origin/main
  ABRAXAS_BRANCH_CLEANUP_I_UNDERSTAND=1 scripts/branch_cleanup.sh --apply
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote)
      REMOTE="${2:-}"; shift 2 ;;
    --base)
      BASE_REF="${2:-}"; shift 2 ;;
    --apply)
      APPLY="true"; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$repo_root" ]]; then
  echo "Error: not in a git repository." >&2
  exit 1
fi

echo "[branch-cleanup] repo: $repo_root"
echo "[branch-cleanup] remote: $REMOTE"
echo "[branch-cleanup] base: $BASE_REF"

echo "[branch-cleanup] fetching + pruning..."
git fetch --prune "$REMOTE" >/dev/null

if ! git rev-parse --verify "$BASE_REF" >/dev/null 2>&1; then
  echo "Error: base ref '$BASE_REF' not found after fetch." >&2
  exit 1
fi

declare -a merged=()
declare -a unmerged=()

mapfile -t merged_raw < <(git branch -r --merged "$BASE_REF" || true)
for b in "${merged_raw[@]}"; do
  # Trim leading whitespace from `git branch` output.
  b="${b#"${b%%[![:space:]]*}"}"
  [[ -z "$b" ]] && continue

  case "$b" in
    "$REMOTE/HEAD" | "$REMOTE/HEAD -> "* | "$REMOTE/main")
      continue
      ;;
  esac
  merged+=("$b")
done

mapfile -t unmerged_raw < <(git branch -r --no-merged "$BASE_REF" || true)
for b in "${unmerged_raw[@]}"; do
  b="${b#"${b%%[![:space:]]*}"}"
  [[ -z "$b" ]] && continue
  case "$b" in
    "$REMOTE/HEAD" | "$REMOTE/HEAD -> "* | "$REMOTE/main")
      continue
      ;;
  esac
  unmerged+=("$b")
done

echo
echo "[branch-cleanup] merged-into-$BASE_REF (candidates to delete): ${#merged[@]}"
for b in "${merged[@]}"; do
  echo "  - $b"
done

echo
echo "[branch-cleanup] NOT merged into $BASE_REF (needs review): ${#unmerged[@]}"
for b in "${unmerged[@]}"; do
  counts="$(git rev-list --left-right --count "$BASE_REF...$b" 2>/dev/null || echo "? ?")"
  # counts format: "<left> <right>" where right=commits only in branch
  echo "  - $b  (origin/main-only=${counts%%[[:space:]]*}, branch-only=${counts##*[[:space:]]})"
done

echo
if [[ "$APPLY" != "true" ]]; then
  echo "[branch-cleanup] DRY-RUN. To delete merged branches:"
  echo "  ABRAXAS_BRANCH_CLEANUP_I_UNDERSTAND=1 scripts/branch_cleanup.sh --apply"
  echo
  echo "[branch-cleanup] Commands that would run:"
  for b in "${merged[@]}"; do
    short="${b#${REMOTE}/}"
    echo "  git push \"$REMOTE\" --delete \"$short\""
  done
  exit 0
fi

if [[ "${ABRAXAS_BRANCH_CLEANUP_I_UNDERSTAND:-0}" != "1" ]]; then
  echo "Refusing to delete branches without ABRAXAS_BRANCH_CLEANUP_I_UNDERSTAND=1" >&2
  exit 3
fi

echo "[branch-cleanup] APPLY mode enabled. Deleting merged branches from $REMOTE..."
for b in "${merged[@]}"; do
  short="${b#${REMOTE}/}"
  echo "  deleting: $REMOTE/$short"
  git push "$REMOTE" --delete "$short"
done

echo "[branch-cleanup] done."
