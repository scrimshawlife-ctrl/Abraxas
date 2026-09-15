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
IMPLEMENTED = {item[0] for item in SEQUENCE}


def build_v11_invocation_plan(plan_id: str = "familiar_v1_1") -> InvocationPlan:
    invocations: list[RuneInvocation] = []
    for inv_id, rune_id in SEQUENCE:
        invocations.append(
            RuneInvocation(
                invocation_id=inv_id,
                rune_id=rune_id,
                input_contract_ref="EvidencePack.v0",
                params={"coupling": COUPLING, "gate": inv_id},
                determinism="strict",
                side_effects="ledger_append" if inv_id == "keep" else "none",
                not_computable=False,
                missing_fields=[],
            )
        )
    edges = [
        DependencyEdge(SEQUENCE[i][0], SEQUENCE[i + 1][0])
        for i in range(len(SEQUENCE) - 1)
    ]
    return InvocationPlan(plan_id=plan_id, rune_invocations=invocations, dependency_edges=edges)
