from __future__ import annotations

from abx.knowledge.forgettingPolicy import build_forgetting_policy
from abx.knowledge.memoryLifecycle import build_memory_lifecycle
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_forgetting_report() -> dict[str, object]:
    policy = build_forgetting_policy()
    expired = [x.memory_id for x in build_memory_lifecycle() if x.lifecycle_state in set(policy.expiry_states)]
    archival_only = [x.memory_id for x in build_memory_lifecycle() if x.lifecycle_state in set(policy.archival_only_states)]
    report = {
        "artifactType": "ForgettingAudit.v1",
        "artifactId": "forgetting-audit",
        "policy": policy.__dict__,
        "expired": sorted(expired),
        "archivalOnly": sorted(archival_only),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
