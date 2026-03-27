from __future__ import annotations

from abx.concurrency.types import SerializationPolicyRecord


def build_serialization_policies() -> list[SerializationPolicyRecord]:
    rows = [
        SerializationPolicyRecord(
            policy_id="serialize.runtime.plan",
            domain_id="domain.runtime",
            trigger_classes=["TARGET_CONFLICT", "SIDE_EFFECT_CONFLICT"],
            strategy="SERIALIZE_BY_AUTHORITY_THEN_TIME",
        ),
        SerializationPolicyRecord(
            policy_id="serialize.review.window",
            domain_id="domain.review",
            trigger_classes=["TEMPORAL_CONFLICT"],
            strategy="DELAY_WITH_BACKOFF",
        ),
    ]
    return sorted(rows, key=lambda x: x.policy_id)
