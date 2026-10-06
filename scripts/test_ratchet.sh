#!/usr/bin/env bash
# Fails if the test suite regresses past the recorded baseline.
#
# The baseline lives here so CI and humans read the same number. Lower it in the
# same commit that fixes a cluster. It must only ever decrease -- copying the
# idiom in tests/test_coupling_lint.py (MAX_ALLOWED_VIOLATIONS).
#
# See docs/TEST_DEBT.md for the cluster breakdown behind the current number.
#
# Usage: bash scripts/test_ratchet.sh
set -uo pipefail

BASELINE_FAILURES=6
OUT="$(mktemp)"

cd "$(dirname "$0")/.." || exit 2
python -m pytest tests/ -q --no-header -p no:cacheprovider > "$OUT" 2>&1

failures=$(grep -cE '^(FAILED|ERROR) ' "$OUT")
summary=$(tail -1 "$OUT")

echo "$summary"
echo "failures=$failures baseline=$BASELINE_FAILURES"

if [ "$failures" -gt "$BASELINE_FAILURES" ]; then
  echo "REGRESSION: $failures failures exceeds baseline $BASELINE_FAILURES" >&2
  grep -E '^(FAILED|ERROR) ' "$OUT" >&2
  exit 1
fi

echo "OK: within baseline"
exit 0
