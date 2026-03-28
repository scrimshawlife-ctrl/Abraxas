from __future__ import annotations

from abx.operator.traceInventory import build_trace_inventory


def build_operator_trace_records() -> tuple:
    return build_trace_inventory()
