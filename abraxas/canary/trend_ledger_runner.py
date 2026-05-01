from __future__ import annotations

from typing import Any, Mapping

from abraxas.canary.trend_ledger import build_trend_ledger
from abraxas.canary.trend_ledger_validator import validate_trend_ledger


def run_trend_ledger(
    analysis: Mapping[str, Any],
    previous: Mapping[str, Any] | None = None,
) -> dict:
    out = build_trend_ledger(analysis, previous)
    errors = validate_trend_ledger(out)
    if errors:
        raise ValueError(";".join(errors))
    return out
