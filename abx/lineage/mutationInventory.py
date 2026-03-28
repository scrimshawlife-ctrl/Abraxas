from __future__ import annotations

from abx.lineage.types import MutationLegitimacyRecord


def build_mutation_inventory() -> tuple[MutationLegitimacyRecord, ...]:
    return (
        MutationLegitimacyRecord(
            "mut.norm",
            "state.orders.norm",
            "pipeline.normalize",
            "MUTATION_LEGITIMATE",
            mutation_scope="state.orders.*",
            authority_ref="policy/state-mutation@v3",
            mutation_semantics="PATCH",
        ),
        MutationLegitimacyRecord(
            "mut.rollup",
            "state.rev.rollup",
            "pipeline.aggregate",
            "MUTATION_CONDITIONAL",
            mutation_scope="state.rev.rollup",
            authority_ref="policy/materialization@v2",
            mutation_semantics="MATERIALIZE",
        ),
        MutationLegitimacyRecord(
            "mut.cache",
            "state.rev.cache",
            "scheduler.cache",
            "MUTATION_LEGITIMATE",
            mutation_scope="state.rev.cache",
            authority_ref="policy/cache-refresh@v2",
            mutation_semantics="OVERWRITE",
        ),
        MutationLegitimacyRecord(
            "mut.manual",
            "state.partner.shadow",
            "manual.override",
            "MUTATION_CONDITIONAL",
            mutation_scope="state.partner.*",
            authority_ref="approval/manual@pending",
            mutation_semantics="OVERWRITE",
        ),
        MutationLegitimacyRecord(
            "mut.partner",
            "state.partner.merged",
            "connector.partner",
            "MUTATION_ILLEGITIMATE",
            mutation_scope="state.partner.merged",
            authority_ref="policy/federation-write@v1",
            mutation_semantics="OVERWRITE",
        ),
    )
