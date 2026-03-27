from __future__ import annotations

from abx.continuity.persistenceClassification import classify_persistence_state
from abx.continuity.persistedIntentRecords import build_persisted_intent_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_intent_persistence_report() -> dict[str, object]:
    records = build_persisted_intent_records()
    states = {
        row.intent_id: classify_persistence_state(
            persistence_state=row.persistence_state,
            freshness_state=row.freshness_state,
            revalidation_required=row.revalidation_required,
        )
        for row in records
    }
    report = {
        "artifactType": "IntentPersistenceAudit.v1",
        "artifactId": "intent-persistence-audit",
        "intents": [x.__dict__ for x in records],
        "intentStates": states,
        "staleIntents": sorted(k for k, v in states.items() if v == "STALE_INTENT"),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
