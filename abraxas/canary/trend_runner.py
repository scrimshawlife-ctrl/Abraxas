from __future__ import annotations

from typing import Any, Mapping

from abraxas.canary.cycle_trends import build_cycle_trend_analysis
from abraxas.canary.trend_validator import validate_cycle_trend_analysis


def run_cycle_trend_analysis(ledger_run: Mapping[str, Any]) -> dict:
    out = build_cycle_trend_analysis(ledger_run)
    errors = validate_cycle_trend_analysis(out)
    if errors:
        raise ValueError(";".join(errors))
    return out
