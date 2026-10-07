"""Survey each engine against the technical-settlement criteria.

Why this exists
---------------
Phase 4 gave every engine a `Settlement` record defaulting to `unsettled`. That is truthful, but it
carries no information -- exactly the decay the arXiv scan measured in the wild, where limitations
and evaluation fields have the lowest fill-out rates of any model-card section. The field needed
something that could actually DECIDE it.

The doctrine sibling defines what technical settlement means:

    Technical -- Does the instrument perform to specification?
    Verified by: determinism, schemas, tests, replay, provenance, canonical artifacts

This survey evaluates each engine against those criteria and reports honestly which are satisfied,
which are absent, and which are NOT MEASURABLE without running the engine. It never guesses: an
unmeasured criterion is reported as `?`, and a `?` cannot support a settlement -- because a claim
resting on an unmeasured criterion is the thing the doctrine exists to prevent.

Two criteria are established elsewhere and are deliberately NOT faked here:
  - *schemas*   -- contracts/ + the schema-validity guards
  - *registered* -- tests/test_production_engine_wiring.py

Usage:
    python scripts/survey_engine_settlements.py            # table
    python scripts/survey_engine_settlements.py --json      # machine-readable

Exit code 0 if every engine declaring `technical: settled` is corroborated by this survey, else 1.
That makes the survey the evidence the manifest cites rather than a report nobody reads.
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

_COLLECTED: Optional[List[str]] = None

#: Criteria a survey can establish by INSPECTION, without running the engine.
INSPECTABLE: Tuple[str, ...] = ("entry_point", "conforms", "collected_tests")
#: Criteria that require running the engine and comparing runs. Reported as unmeasured, because a
#: survey that claimed to know these without running anything would be inventing its evidence.
RUN_REQUIRED: Tuple[str, ...] = ("determinism", "replay", "provenance", "canonical_artifacts")

PRESENT = "yes"
ABSENT = "no"
UNMEASURED = "?"


def _resolve(implementation: str):
    """Resolve ``module:Attribute`` -> the object, or None. Importing the module is not enough."""
    if not implementation or ":" not in implementation:
        return None
    module_path, attribute = implementation.split(":", 1)
    try:
        module = importlib.import_module(module_path)
    except Exception:
        return None
    return getattr(module, attribute, None)


def _entry_point_status(implementation: str) -> str:
    target = _resolve(implementation)
    if target is None:
        return ABSENT
    return PRESENT if (callable(target) or isinstance(target, type)) else ABSENT


def _conformance_status(spec) -> str:
    """Conformance, MEASURED rather than assumed.

    A CLASS is checked by subclass. A FACTORY is checked by actually building it with the same
    deterministic stand-in that `abraxas/engines/execution_harness.py` uses, and asking whether the
    result satisfies the interface -- the same construction `tests/test_engine_manifest_agreement.py`
    performs.

    This returned `?` until the harness existed, on the reasoning that calling a factory with guessed
    arguments would mean reporting a guess as a measurement. That reasoning was right about guessing and
    wrong about the fix: the harness supplies a *defined* stand-in, so the construction is a measurement,
    not a guess. Since this table's own legend defines `?` as "not measurable without running it",
    leaving `?` here after the capability existed would have been a status the code no longer supported.
    """
    from abraxas.evidence.provider import EvidenceProvider

    target = _resolve(spec.implementation)
    if target is None:
        return ABSENT
    if isinstance(target, type):
        return PRESENT if issubclass(target, EvidenceProvider) else ABSENT

    # A factory: build it with the harness's stand-in and inspect what comes out.
    try:
        from abraxas.engines.execution_harness import _construct_engine

        produced = _construct_engine(spec)
    except Exception:
        return ABSENT
    return PRESENT if isinstance(produced, EvidenceProvider) else ABSENT


def _collected_test_ids() -> List[str]:
    """Collect every test id ONCE, so parametrised ids are visible.

    Why not grep the test files: `test_live_engine_entry_point_resolves[trutina]` exists only as a
    parametrised ID -- the string `trutina` appears nowhere in tests/test_engine_manifest_agreement.py.
    A grep therefore reported "trutina has no coverage" while two of its tests were passing.

    That was this survey's own first bug, and it is the SAME error that produced the doctrine arc's
    first wrong claim (`grep weakest` returned nothing, so "no weakest-link rule exists"): a
    name-based check standing in for a mechanism-based one. Collect, don't grep.
    """
    global _COLLECTED
    if _COLLECTED is None:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", "--collect-only", "-q", "--no-header",
             "-p", "no:cacheprovider", "-o", "addopts="],
            cwd=REPO, capture_output=True, text=True,
        )
        _COLLECTED = [ln.strip() for ln in proc.stdout.splitlines() if "::" in ln]
        if not _COLLECTED:
            # An instrument that silently returns nothing is worse than one that errors: this
            # survey reported "not measurable" for every engine the first time collection came
            # back empty, which looks exactly like a real finding. Fail loudly instead.
            raise RuntimeError(
                "collection produced no test ids -- the survey's instrument is broken, so its "
                f"output cannot be trusted.\n  argv: {proc.args}\n"
                f"  stdout tail: {proc.stdout[-400:]}\n  stderr tail: {proc.stderr[-400:]}"
            )
    return _COLLECTED


def _collected_tests_status(name: str) -> str:
    """Are any tests COLLECTED for this engine?

    Discovered through pytest's own collection, so a parametrised case counts -- which is the only
    correct answer. Still a proxy: a collected test is not proof the test is meaningful, but its
    absence is decisive.
    """
    ids = _collected_test_ids()
    if not ids:
        return UNMEASURED
    hit = any(re.search(rf"\b{re.escape(name)}\b", test_id) for test_id in ids)
    return PRESENT if hit else ABSENT


def survey() -> List[Dict[str, object]]:
    from abraxas.engines.manifest import ENGINES, LIVE
    from abraxas.engines.execution_harness import measure as _harness_measure

    rows: List[Dict[str, object]] = []
    for spec in ENGINES:
        criteria: Dict[str, str] = {
            "entry_point": _entry_point_status(spec.implementation),
            "conforms": _conformance_status(spec),
            "collected_tests": _collected_tests_status(spec.name),
        }
        if spec.status == LIVE:
            measured = _harness_measure(spec.name)
            for criterion in RUN_REQUIRED:
                criteria[criterion] = measured.get(criterion, UNMEASURED)
        else:
            for criterion in RUN_REQUIRED:
                criteria[criterion] = UNMEASURED

        # A settlement needs EVERY criterion present. Unmeasured is not satisfied.
        satisfiable = spec.status == LIVE and all(v == PRESENT for v in criteria.values())
        missing = [k for k, v in criteria.items() if v != PRESENT]

        rows.append(
            {
                "engine": spec.name,
                "status": spec.status,
                "declared_technical": spec.settlements.technical,
                "criteria": criteria,
                "technical_satisfiable": satisfiable,
                "missing_or_unmeasured": missing,
            }
        )
    return rows


def uncorroborated_settlements(rows: List[Dict[str, object]]) -> List[str]:
    """Engines declaring a technical settlement this survey cannot corroborate.

    Exposed as a function so it can be driven to fail by a test. An enforcement link nobody has seen
    reject anything is not known to enforce anything.
    """
    return [
        str(r["engine"])
        for r in rows
        if r["declared_technical"] == "settled" and not r["technical_satisfiable"]
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = parser.parse_args()

    rows = survey()

    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        cols = ["engine", "status"] + list(INSPECTABLE) + list(RUN_REQUIRED) + ["declared", "satisfiable"]
        widths = [max(len(str(c)), 12) for c in cols]
        print("  ".join(str(c).ljust(w) for c, w in zip(cols, widths)))
        print("  ".join("-" * w for w in widths))
        for r in rows:
            criteria = r["criteria"]
            assert isinstance(criteria, dict)
            cells: List[str] = [str(r["engine"]), str(r["status"])]
            cells += [str(criteria[c]) for c in INSPECTABLE]
            cells += [str(criteria[c]) for c in RUN_REQUIRED]
            cells += [str(r["declared_technical"]), str(r["technical_satisfiable"])]
            print("  ".join(str(c).ljust(w) for c, w in zip(cells, widths)))
        print()
        print(f"  {PRESENT}=present  {ABSENT}=absent  {UNMEASURED}=not measurable without running it")
        print("  Run-required criteria need a real execution comparison; a '?' cannot support a settlement.")

    # The enforcement link: nothing may DECLARE technical settlement this survey cannot corroborate.
    lying = uncorroborated_settlements(rows)
    if lying:
        print()
        print(
            "  SETTLEMENT NOT CORROBORATED for: " + ", ".join(lying)
            + " -- declared `settled` without every criterion present.",
            file=sys.stderr,
        )
        return 1

    declared = [str(r["engine"]) for r in rows if r["declared_technical"] == "settled"]
    corroborable = [
        str(r["engine"]) for r in rows
        if r["technical_satisfiable"] and r["declared_technical"] != "settled"
    ]
    print()
    print(f"  engines declaring technical settlement and corroborated: {declared or 'none'}")
    if corroborable:
        # Without this line the summary above reads as "nothing is corroborated", when in fact these
        # engines have every criterion measured and passing -- they simply do not CLAIM a settlement.
        # The survey corroborates; the operator decides. See docs/ENGINE_TOPOLOGY.md.
        print(
            "  engines with every criterion measured and passing but NOT claiming a settlement "
            f"(available, unclaimed): {corroborable}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
