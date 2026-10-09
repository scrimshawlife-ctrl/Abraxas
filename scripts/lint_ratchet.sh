#!/usr/bin/env bash
# Fails if ruff findings regress past the recorded per-rule baselines.
#
# WHY A RATCHET AND NOT AN IGNORE LIST
#   The configured ruleset (see [tool.ruff.lint] in pyproject.toml) carries pre-existing debt,
#   so a plain `ruff check` gate would be red on day one and stay red -- a gate nobody can act
#   on is a gate nobody reads. Ignoring the noisy rules instead would switch them OFF, so a NEW
#   violation of them could never fail. The ratchet keeps every rule ACTIVE and only requires
#   that the recorded counts do not grow. Same idiom as scripts/test_ratchet.sh.
#
# BASELINE MAY ONLY EVER DECREASE, PER RULE. Lower a count in the same commit that fixes a
#   cluster. Never raise one without saying why -- and prefer fixing.
#
# THE F401 CLUSTER IS DELIBERATELY NOT SWEEPABLE, and that is MEASURED, not assumed. Three
#   throwaway-worktree experiments, each against the full suite (the suite is the judge because
#   no amount of reading exposed any of these):
#     1. a re-export held by `# noqa: E402`. That marker covers "import not at top", NOT F401, so
#        `ruff --fix --select F401` deleted it and cost 54 tests' collection.
#     2. a re-export carrying NO marker at all (abraxas/integrity/composites.py), findable only by
#        scanning F401 findings for names that other modules import FROM that same module.
#     3. WITH both marked, the sweep STILL failed: removing fastapi's FileResponse from
#        abraxas/dashboard/api.py made .aal/dependency_manifest.v0.yaml a FALSE RECORD, which
#        tests/test_dependency_import_locations.py catches by design.
#   The third is the stopping point. Landing this sweep would mean rewriting a governed
#   declaration of where dependencies are used so that it agrees with a cosmetic edit -- changing
#   an evidence record to flatter a cleanup. Pay F401 down per cluster instead, reconciling the
#   manifest deliberately in the same change. Assume more invisible obstacles than these three:
#   every one was found by measurement, never by reading.
#
# A rule ABSENT from the baseline is reported but does NOT fail: a ruff upgrade can introduce
#   new rule codes, and failing on those would break CI for a reason unrelated to this repo.
#   Triage it and add it deliberately.
#
# Usage: bash scripts/lint_ratchet.sh
set -uo pipefail

TARGETS=(abraxas abx abx_familiar scripts tests webpanel)
# .github/ is deliberately NOT scanned. The engine cookiecutter holds Jinja templates whose .py
# files contain {{ placeholders }} and are not valid Python until rendered, so scanning them yields
# invalid-syntax noise that says nothing about this repository. Do not "fix" this by adding .github:
# measure it first and see the syntax errors for what they are.
BASELINE="scripts/lint_baseline.json"
PYTHON="${PYTHON:-python3}"

if ! command -v ruff >/dev/null 2>&1; then
  echo "PREFLIGHT FAILED: ruff is not on PATH." >&2
  echo "  It is a declared dev dependency, so install it the documented way:" >&2
  echo "    pip install -e \".[dev]\"" >&2
  exit 2
fi

if [[ ! -f "$BASELINE" ]]; then
  echo "PREFLIGHT FAILED: missing baseline $BASELINE" >&2
  exit 2
fi

# ruff exits non-zero whenever it finds anything, which is the normal case here. Capture its
# JSON via a file rather than a pipe so its exit code cannot masquerade as this gate's verdict.
FINDINGS="$(mktemp)"
trap 'rm -f "$FINDINGS"' EXIT
ruff check "${TARGETS[@]}" --output-format=json > "$FINDINGS" 2>/dev/null || true

"$PYTHON" - "$BASELINE" "$FINDINGS" <<'PY'
import collections
import json
import sys

baseline = json.load(open(sys.argv[1]))
current = collections.Counter(x["code"] for x in json.load(open(sys.argv[2])))

regressions, improvements = [], []
for rule, allowed in sorted(baseline["rules"].items()):
    got = current.get(rule, 0)
    if got > allowed:
        regressions.append((rule, allowed, got))
    elif got < allowed:
        improvements.append((rule, allowed, got))

untracked = sorted(c for c in current if c not in baseline["rules"])
total = sum(current.values())

for rule, allowed, got in regressions:
    print(f"REGRESSION {rule}: {allowed} -> {got}  (+{got - allowed})")
for rule, allowed, got in improvements:
    print(f"improved   {rule}: {allowed} -> {got}  (-{allowed - got})")
for rule in untracked:
    print(f"untracked  {rule}: {current[rule]}  (new rule code; not failing)")

print(f"lint: total={total} baseline={baseline['total']} rules_tracked={len(baseline['rules'])}")

if regressions:
    print(
        "\nFAIL: lint debt grew. Fix the new findings, or -- if a cluster was resolved -- "
        "lower its baseline entry in scripts/lint_baseline.json."
    )
    sys.exit(1)

if improvements:
    print(
        f"\nOK: within baseline, and {len(improvements)} rule(s) improved. Lower those "
        "baseline entries in the same commit so the gain is locked in."
    )
else:
    print("\nOK: within baseline")
PY
