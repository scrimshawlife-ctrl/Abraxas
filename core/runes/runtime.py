from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict
from core.models.governance import Authority
import hashlib
import json
import uuid

KNOWN_RUNES = {
    "ϟ₁", "ϟ₂", "ϟ₃", "ϟ₄", "ϟ₅", "ϟ₆", "ϟ₇",
    "RUNE_AUDIT", "RUNE_HASH", "RUNE_VALIDATE", "RUNE_ROUTE",
    "sdct.text_subword.v1",
}


class RuneInvocationStep(BaseModel):
    step_id: str
    rune_id: str
    input_schema: Dict
    output_schema: Dict
    required_receipts: List[str]
    route_node: str
    deterministic_order: int

    def __init__(self, **data):
        super().__init__(**data)
        if self.deterministic_order < 0:
            raise ValueError("deterministic_order must be non-negative")


class RuneInvocationPlan(BaseModel):
    schema_version: str = "RuneInvocationPlan.v1"
    plan_id: str
    pipeline_id: str
    steps: List[RuneInvocationStep]
    authority: Authority

    def __init__(self, **data):
        super().__init__(**data)
        if not self.steps:
            raise ValueError("steps cannot be empty")
        orders = [s.deterministic_order for s in self.steps]
        if len(set(orders)) != len(orders):
            raise ValueError("deterministic_order values must be unique")
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")

    def invocation_plan_hash(self) -> str:
        steps_repr = [
            {
                "step_id": step.step_id,
                "rune_id": step.rune_id,
                "route_node": step.route_node,
                "deterministic_order": step.deterministic_order,
            }
            for step in sorted(self.steps, key=lambda x: x.deterministic_order)
        ]
        canonical_data = json.dumps({
            "plan_id": self.plan_id,
            "pipeline_id": self.pipeline_id,
            "steps": steps_repr,
        }, sort_keys=True).encode("utf-8")
        return hashlib.sha256(canonical_data).hexdigest()


def build_invocation_plan(contract: dict, route_graph: dict, rune_catalog: dict) -> RuneInvocationPlan:
    steps = []
    for idx, rune in enumerate(contract.get("required_runes", [])):
        if rune not in rune_catalog:
            raise ValueError(f"Rune {rune} does not exist in rune catalog")
        steps.append(RuneInvocationStep(
            step_id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{rune}-{idx}")),
            rune_id=rune,
            input_schema=rune_catalog[rune].get("input_schema", {}),
            output_schema=rune_catalog[rune].get("output_schema", {}),
            required_receipts=[],
            route_node=route_graph.get(rune, {}).get("node", "unknown"),
            deterministic_order=idx,
        ))
    authority = contract.get("authority")
    if not authority.is_locked():
        raise ValueError("Authority must be locked.")
    return RuneInvocationPlan(
        plan_id=str(uuid.uuid5(uuid.NAMESPACE_DNS, contract["pipeline_id"])),
        pipeline_id=contract["pipeline_id"],
        steps=steps,
        authority=authority,
    )