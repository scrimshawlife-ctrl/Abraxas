from __future__ import annotations

from abx.freshness.decayClassification import classify_freshness
from abx.freshness.freshnessRecords import build_decay_records, build_freshness_records
from abx.freshness.types import FreshnessGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_freshness_decay_report() -> dict[str, object]:
    freshness = build_freshness_records()
    decay = build_decay_records()
    decay_by_ref = {x.entity_ref: x for x in decay}
    states = {}
    for row in freshness:
        decay_row = decay_by_ref.get(row.entity_ref)
        states[row.freshness_id] = classify_freshness(
            freshness_state=row.freshness_state,
            reuse_posture=row.reuse_posture,
            decay_state=decay_row.decay_state if decay_row else "DECAY_UNKNOWN",
        )

    errors = []
    for row in freshness:
        state = states[row.freshness_id]
        if state in {"EXPIRED", "REUSE_BLOCKED", "BLOCKED"}:
            errors.append(FreshnessGovernanceErrorRecord("FRESHNESS_INVALID_FOR_REUSE", "ERROR", f"{row.entity_ref} state={state}"))
        elif state in {"STALE", "DECAY_UNKNOWN", "REFRESH_REQUIRED", "ARCHIVAL_ONLY"}:
            errors.append(FreshnessGovernanceErrorRecord("FRESHNESS_ATTENTION_REQUIRED", "WARN", f"{row.entity_ref} state={state}"))

    report = {
        "artifactType": "FreshnessDecayAudit.v1",
        "artifactId": "freshness-decay-audit",
        "freshness": [x.__dict__ for x in freshness],
        "decay": [x.__dict__ for x in decay],
        "freshnessStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
