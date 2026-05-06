#!/usr/bin/env python3
"""run_doctrine_validator.py

Runs doctrine validator gates over the latest execution artifacts.
Governance-first, fail-closed output.
"""
from __future__ import annotations

import json
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core.models.governance import Authority
from core.observability.aggregation import run_observability_pipeline


def main() -> int:
    print("[run_doctrine_validator] running doctrine validator gates")

    authority = Authority.locked(source="run_doctrine_validator")
    result = run_observability_pipeline(
        out_dir="out",
        run_id="doctrine-validator-run",
        authority=authority,
    )

    gates = result.get("doctrine_gates", [])
    passed = result.get("gates_passed", False)

    for gate in gates:
        symbol = "[PASS]" if gate["result"] == "pass" else "[FAIL]"
        print(f"  {symbol} {gate['gate']}: {gate['reason']}")

    print(f"\n  overall: {'ALL GATES PASS' if passed else 'ONE OR MORE GATES FAILED'}")
    print("[run_doctrine_validator] complete")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
