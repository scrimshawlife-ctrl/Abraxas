from __future__ import annotations

from itertools import combinations

from abx.concurrency.concurrentClassification import classify_concurrency_posture, classify_overlap_state
from abx.concurrency.concurrentInventory import build_concurrent_operation_inventory
from abx.concurrency.concurrencyDomains import build_concurrency_domains
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_concurrent_operation_report() -> dict[str, object]:
    ops = build_concurrent_operation_inventory()
    domains = {x.domain_id: x for x in build_concurrency_domains()}
    overlap_rows: list[dict[str, str]] = []

    for left, right in combinations(ops, 2):
        same_target = left.target_ref == right.target_ref
        same_domain = left.domain_id == right.domain_id
        policy = domains[left.domain_id].overlap_policy if same_domain else "INDEPENDENT_CONCURRENT"
        overlap_state = classify_overlap_state(same_target=same_target, same_domain=same_domain, domain_policy=policy)
        overlap_rows.append(
            {
                "pair": f"{left.operation_id}|{right.operation_id}",
                "domain": left.domain_id if same_domain else "cross-domain",
                "state": overlap_state,
            }
        )

    report = {
        "artifactType": "ConcurrentOperationAudit.v1",
        "artifactId": "concurrent-operation-audit",
        "operations": [x.__dict__ for x in ops],
        "domains": [x.__dict__ for x in build_concurrency_domains()],
        "overlaps": sorted(overlap_rows, key=lambda x: x["pair"]),
        "posture": classify_concurrency_posture([x["state"] for x in overlap_rows]),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
