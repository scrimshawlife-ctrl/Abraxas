from __future__ import annotations

from abx.performance.resourceAccounting import build_resource_accounting_records


def classify_accounting_modes() -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {
        "accounted": [],
        "estimated_proxy": [],
        "heuristic": [],
        "not_computable": [],
    }
    for record in build_resource_accounting_records():
        buckets[record.accounting_mode].append(record.record_id)
    return {k: sorted(v) for k, v in buckets.items()}


def classify_accounting_necessity() -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {
        "required": [],
        "optional": [],
        "avoidable_overhead": [],
    }
    for record in build_resource_accounting_records():
        buckets[record.necessity_class].append(record.record_id)
    return {k: sorted(v) for k, v in buckets.items()}


def detect_redundant_accounting_surfaces() -> list[str]:
    seen: set[tuple[str, str, str]] = set()
    redundant: list[str] = []
    for record in build_resource_accounting_records():
        key = (record.workflow, record.capability, record.resource_type)
        if key in seen:
            redundant.append(record.record_id)
            continue
        seen.add(key)
    return sorted(redundant)
