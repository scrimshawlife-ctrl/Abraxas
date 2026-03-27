from __future__ import annotations

from abx.obligations.types import ObligationLifecycleRecord


def build_obligation_lifecycle_records() -> list[ObligationLifecycleRecord]:
    rows = [
        ObligationLifecycleRecord("lifecycle.release-v1-6", "commitment.release-v1-6", "IN_PROGRESS", "product-steward", ""),
        ObligationLifecycleRecord("lifecycle.incident-followup", "commitment.incident-followup", "DUE_SOON", "ops-steward", ""),
        ObligationLifecycleRecord("lifecycle.docs-refresh", "commitment.docs-refresh", "SCHEDULED", "docs-steward", ""),
        ObligationLifecycleRecord("lifecycle.legacy-api-window", "commitment.legacy-api-window", "MISSED", "platform-steward", "blocker.migration-lag"),
        ObligationLifecycleRecord("lifecycle.deprecated-export", "commitment.deprecated-export", "WAIVED", "product-steward", ""),
    ]
    return sorted(rows, key=lambda x: x.lifecycle_id)
