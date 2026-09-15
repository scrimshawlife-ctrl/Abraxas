"""Summoner — declare the spec v1.1 invocation plan. No execution."""

from __future__ import annotations

from abx_familiar.ir.invocation_plan_v0 import DependencyEdge, InvocationPlan, RuneInvocation

COUPLING = "spec_v1.1"
SEQUENCE = (
    ("summon", "abx.familiar.summon.v0"),
    ("ward_pre", "abx.familiar.ward.v0"),
    ("forage", "abx.familiar.forage.v0"),
    ("bind", "abx.familiar.bind.v0"),
    ("weave", "abx.familiar.weave.v0"),
    ("ward_post", "abx.familiar.ward.v0"),
    ("keep", "abx.familiar.keep.v0"),
    ("herald", "abx.familiar.herald.v0"),
)
IMPLEMENTED = {"summon", "ward_pre", "forage", "bind", "keep"}


def build_v11_invocation_plan(plan_id: str = "familiar_v1_1") -> InvocationPlan:
    invocations: list[RuneInvocation] = []
    for inv_id, rune_id in SEQUENCE:
        implemented = inv_id in IMPLEMENTED
        invocations.append(
            RuneInvocation(
                invocation_id=inv_id,
                rune_id=rune_id,
                input_contract_ref="EvidencePack.v0",
                params={"coupling": COUPLING, "gate": inv_id},
                determinism="strict",
                side_effects="none" if inv_id != "keep" else "ledger_append",
                not_computable=not implemented,
                missing_fields=[] if implemented else ["implementation"],
            )
        )
    edges = [
        DependencyEdge(SEQUENCE[i][0], SEQUENCE[i + 1][0])
        for i in range(len(SEQUENCE) - 1)
    ]
    return InvocationPlan(plan_id=plan_id, rune_invocations=invocations, dependency_edges=edges)
