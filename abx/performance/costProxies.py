from __future__ import annotations

from abx.performance.resourceAccounting import build_resource_accounting_records


def build_cost_proxy_summary() -> dict[str, object]:
    records = build_resource_accounting_records()
    proxy = [x.record_id for x in records if x.accounting_mode == "estimated_proxy"]
    heuristic = [x.record_id for x in records if x.accounting_mode == "heuristic"]
    return {
        "proxyRecords": sorted(proxy),
        "heuristicRecords": sorted(heuristic),
    }
