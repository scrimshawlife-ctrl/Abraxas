from __future__ import annotations

from abx.concurrency.types import SerializationPolicyRecord


def build_arbitration_policies() -> list[SerializationPolicyRecord]:
    rows = [
        SerializationPolicyRecord(
            policy_id="arbitration.runtime.write_vs_rollback",
            domain_id="domain.runtime",
            trigger_classes=["TARGET_CONFLICT", "AUTHORITY_CONFLICT", "SIDE_EFFECT_CONFLICT"],
            strategy="SERIALIZE_OR_ESCALATE",
        ),
        SerializationPolicyRecord(
            policy_id="arbitration.review.duplicates",
            domain_id="domain.review",
            trigger_classes=["DUPLICATE_CONFLICT", "TEMPORAL_CONFLICT"],
            strategy="MERGE_OR_DELAY",
        ),
        SerializationPolicyRecord(
            policy_id="arbitration.notifications",
            domain_id="domain.notifications",
            trigger_classes=["DUPLICATE_CONFLICT", "MERGEABLE_CONFLICT"],
            strategy="MERGE",
        ),
    ]
    return sorted(rows, key=lambda x: x.policy_id)
