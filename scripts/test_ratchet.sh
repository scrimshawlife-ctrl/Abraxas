#!/usr/bin/env bash
# Fails if the test suite regresses past the recorded baselines.
#
# TWO baselines live here, so CI and humans read the same numbers:
#
#   BASELINE_FAILURES   may only ever DECREASE. Lower it in the same commit that fixes
#                       a cluster. Mirrors tests/test_coupling_lint.py
#                       (MAX_ALLOWED_VIOLATIONS).
#
#   BASELINE_COLLECTED  may only ever INCREASE. Raise it when tests are added.
#                       A DROP means tests stopped being COLLECTED -- which produces no
#                       FAILED and no ERROR line, so BASELINE_FAILURES cannot see it.
#                       Without this floor a whole module can silently stop running
#                       and the ratchet still reports OK.
#
# See docs/TEST_DEBT.md for the cluster breakdown behind the current numbers.
#
# Usage: bash scripts/test_ratchet.sh
set -uo pipefail

BASELINE_FAILURES=0
# Collected total (passed + xfailed + deselected), NOT the passed count -- read it off
# the "collected N items" line, not the summary line. 3358 = 3347 passed + 9 xfailed
# + 2 skipped.
BASELINE_COLLECTED=3358
OUT="$(mktemp)"

cd "$(dirname "$0")/.." || exit 2

# ---------------------------------------------------------------------------
# Preflight: confirm `core` resolves to THIS repo.
#
# `core/` here is a NAMESPACE package (no __init__.py). A stale editable install
# (abraxas-v2) puts another checkout on sys.path whose `core/` is a REGULAR package,
# and a regular package beats a namespace portion regardless of sys.path order. On
# such an interpreter every `import core.*` resolves into that other checkout and 28
# test modules fail to collect with a bare ModuleNotFoundError -- which reads like a
# broken repo rather than the wrong interpreter.
#
# The check compares each candidate search location against <repo>/core, which works
# for namespace packages too (their `origin` is None, so checking `origin` would be
# wrong here).
# ---------------------------------------------------------------------------
if ! python -c '
import importlib.util as u, os, sys
s = u.find_spec("core")
locs = [os.path.realpath(p) for p in (s.submodule_search_locations or [])] if s else []
want = os.path.realpath(os.path.join(os.getcwd(), "core"))
sys.exit(0 if want in locs else 1)
'
then
  echo "PREFLIGHT FAILED: wrong interpreter." >&2
  echo "  'core' does not resolve to <repo>/core on this python." >&2
  echo "  Use the Hermes toolchain interpreter (bare 'python' on this host):" >&2
  echo "    ~/.hermes/tools/python-*/bin/python3" >&2
  exit 1
fi

python -m pytest tests/ -q --no-header -p no:cacheprovider > "$OUT" 2>&1

failures=$(grep -cE '^(FAILED|ERROR) ' "$OUT")
collected=$(grep -oE 'collected [0-9]+ items' "$OUT" | grep -oE '[0-9]+' | head -1)
collected=${collected:-0}
summary=$(tail -1 "$OUT")

echo "$summary"
echo "failures=$failures baseline=$BASELINE_FAILURES  collected=$collected floor=$BASELINE_COLLECTED"

status=0

if [ "$failures" -gt "$BASELINE_FAILURES" ]; then
  echo "REGRESSION: $failures failures exceeds baseline $BASELINE_FAILURES" >&2
  grep -E '^(FAILED|ERROR) ' "$OUT" >&2
  status=1
fi

if [ "$collected" -lt "$BASELINE_COLLECTED" ]; then
  echo "COLLECTION DROP: $collected collected is below the floor $BASELINE_COLLECTED" >&2
  echo "  Tests stopped being collected. That yields no FAILED/ERROR line, so the" >&2
  echo "  failure ratchet cannot detect it. Check for a concurrent writer in this" >&2
  echo "  working tree, a collection error, or a test file that was removed/renamed." >&2
  echo "  If tests were legitimately removed, lower BASELINE_COLLECTED in the same" >&2
  echo "  commit and say why." >&2
  status=1
fi

if [ "$status" -eq 0 ]; then
  echo "OK: within baseline"
fi
exit "$status"
