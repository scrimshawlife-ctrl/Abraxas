"""ABX-PORTFOLIO_SELECT rune operator."""

from __future__ import annotations

from typing import Any, Dict

from abraxas.runes.operators.no_auto_tune import apply_no_auto_tune
from abraxas.runes.operators.active_pointer_atomic import apply_active_pointer_atomic
from abraxas.tuning.device_apply import select_and_apply_portfolio


def apply_portfolio_select(
    *,
    run_ctx: Dict[str, Any],
    dry_run: bool = False,
    strict_execution: bool = True,
) -> Dict[str, Any]:
    apply_no_auto_tune()
    if not dry_run:
        apply_active_pointer_atomic(path="data/utp/ACTIVE")
    result = select_and_apply_portfolio(run_ctx, dry_run=dry_run)
    return result
