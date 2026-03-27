from __future__ import annotations

from abx.obligations.types import ExternalCommitmentRecord


def build_commitment_inventory() -> list[ExternalCommitmentRecord]:
    rows = [
        ExternalCommitmentRecord("commitment.release-v1-6", "external-partner", "scope.release.v1_6", "product-steward", "ACCEPTED_COMMITMENT"),
        ExternalCommitmentRecord("commitment.incident-followup", "customer-cohort-a", "scope.incident.followup", "ops-steward", "SCHEDULED_OBLIGATION"),
        ExternalCommitmentRecord("commitment.docs-refresh", "integration-consumers", "scope.docs.refresh", "docs-steward", "PROPOSED_COMMITMENT"),
        ExternalCommitmentRecord("commitment.legacy-api-window", "legacy-clients", "scope.api.legacy-window", "platform-steward", "SUPERSEDED_OBLIGATION"),
        ExternalCommitmentRecord("commitment.deprecated-export", "external-partner", "scope.export.deprecated", "product-steward", "CANCELED_OBLIGATION"),
    ]
    return sorted(rows, key=lambda x: x.commitment_id)
