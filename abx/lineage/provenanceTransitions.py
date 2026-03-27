from __future__ import annotations

from abx.lineage.types import ProvenanceTransitionRecord


def build_provenance_transition_records() -> tuple[ProvenanceTransitionRecord, ...]:
    return (
        ProvenanceTransitionRecord("ptr.rollup", "state.rev.rollup", "PROVENANCE_COMPLETE", "PROVENANCE_STALE", "upstream_source_changed"),
        ProvenanceTransitionRecord("ptr.cache", "state.rev.cache", "DERIVATION_VALID", "STALE_DERIVED_STATE", "refresh_lag"),
        ProvenanceTransitionRecord("ptr.partner", "state.partner.merged", "MUTATION_LEGITIMATE", "UNAUTHORIZED_MUTATION", "unauthorized_external_write"),
        ProvenanceTransitionRecord("ptr.partner2", "state.partner.merged", "REPLAYABLE_STATE", "NON_REPLAYABLE_STATE", "missing_transform_record"),
    )
