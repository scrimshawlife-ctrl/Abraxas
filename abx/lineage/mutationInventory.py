from __future__ import annotations

from abx.lineage.types import MutationLegitimacyRecord


def build_mutation_inventory() -> tuple[MutationLegitimacyRecord, ...]:
    return (
        MutationLegitimacyRecord("mut.norm", "state.orders.norm", "pipeline.normalize", "MUTATION_LEGITIMATE"),
        MutationLegitimacyRecord("mut.rollup", "state.rev.rollup", "pipeline.aggregate", "MUTATION_CONDITIONAL"),
        MutationLegitimacyRecord("mut.cache", "state.rev.cache", "scheduler.cache", "MUTATION_LEGITIMATE"),
        MutationLegitimacyRecord("mut.partner", "state.partner.merged", "connector.partner", "MUTATION_ILLEGITIMATE"),
    )
