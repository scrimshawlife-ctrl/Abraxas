from __future__ import annotations

from abx.lineage.types import ProvenanceTransitionRecord


def build_provenance_transition_records() -> tuple[ProvenanceTransitionRecord, ...]:
    return (
        ProvenanceTransitionRecord(
            "ptr.rollup",
            "state.rev.rollup",
            "PROVENANCE_COMPLETE",
            "PROVENANCE_STALE",
            "upstream_source_changed",
            "DOWNGRADED",
            "REFRESH_REQUIRED",
        ),
        ProvenanceTransitionRecord(
            "ptr.cache",
            "state.rev.cache",
            "DERIVATION_VALID",
            "STALE_DERIVED_STATE",
            "refresh_lag",
            "DOWNGRADED",
            "RE_DERIVATION_REQUIRED",
        ),
        ProvenanceTransitionRecord(
            "ptr.partner",
            "state.partner.merged",
            "MUTATION_LEGITIMATE",
            "UNAUTHORIZED_MUTATION",
            "unauthorized_external_write",
            "QUARANTINE_ACTIVE",
            "QUARANTINE_REQUIRED",
        ),
        ProvenanceTransitionRecord(
            "ptr.partner2",
            "state.partner.merged",
            "REPLAYABLE_STATE",
            "NON_REPLAYABLE_STATE",
            "missing_transform_record",
            "DOWNGRADED",
            "REPLAY_PATH_REPAIR_REQUIRED",
        ),
        ProvenanceTransitionRecord(
            "ptr.manual",
            "state.partner.shadow",
            "MUTATION_CONDITIONAL",
            "BLOCKED",
            "approval_chain_expired",
            "BLOCKED",
            "HUMAN_APPROVAL_REQUIRED",
        ),
    )
