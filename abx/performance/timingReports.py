from __future__ import annotations

from abx.performance.latencyInventory import build_latency_visibility_inventory
from abx.performance.overheadAttribution import classify_overhead_attribution
from abx.performance.throughputClassification import classify_throughput_constraints
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_latency_throughput_overhead_report() -> dict[str, object]:
    latency = [x.__dict__ for x in build_latency_visibility_inventory()]
    report = {
        "artifactType": "LatencyThroughputOverheadAudit.v1",
        "artifactId": "latency-throughput-overhead-audit",
        "latencyVisibility": latency,
        "throughputConstraints": classify_throughput_constraints(),
        "overheadAttribution": classify_overhead_attribution(),
        "statusBreakdown": {
            "measured": sorted(x["record_id"] for x in latency if x["status"] == "measured"),
            "estimated": sorted(x["record_id"] for x in latency if x["status"] == "estimated"),
            "heuristic": sorted(x["record_id"] for x in latency if x["status"] == "heuristic"),
            "not_computable": sorted(x["record_id"] for x in latency if x["status"] == "not_computable"),
        },
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
