from __future__ import annotations

from typing import Any, Mapping

from abraxas.canary.closure_ledger import build_cycle_closure_ledger
from abraxas.canary.closure_ledger_validator import validate_cycle_closure_ledger


def run_cycle_closure_ledger(
    report: Mapping[str, Any],
    previous: Mapping[str, Any] | None = None,
) -> dict:
    out = build_cycle_closure_ledger(report, previous)
    errors = validate_cycle_closure_ledger(out)
    if errors:
        raise ValueError(";".join(errors))
    return out
