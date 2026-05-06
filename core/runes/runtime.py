from pydantic import BaseModel, Field, root_validator
from typing import List, Union, Dict
from core.models.governance import Authority

class RuneInvocationStep(BaseModel):
    step_id: str
    rune_id: str
    input_schema: Dict
    output_schema: Dict
    required_receipts: List[str]
    route_node: str
    deterministic_order: int

    @root_validator
    def validate_step(cls, values):
        if values["deterministic_order"] < 0:
            raise ValueError("deterministic_order must be non-negative")
        return values

class RuneInvocationPlan(BaseModel):
    schema_version: str = Field("RuneInvocationPlan.v1", const=True)
    plan_id: str
    pipeline_id: str
    steps: List[RuneInvocationStep]
    authority: Authority

    @root_validator
    def validate_plan(cls, values):
        if not values["steps"]:
            raise ValueError("steps cannot be empty")
        if len(set(step.deterministic_order for step in values["steps"])) != len(values["steps"]):
            raise ValueError("deterministic_order values must be unique")
        if not values["authority"].is_locked():
            raise ValueError("authority must be locked")
        return values

    def invocation_plan_hash(self) -> str:
        # Calculate a deterministic hash for the invocation plan
        import hashlib
        import json
        steps_repr = [
            {
                "step_id": step.step_id,
                "rune_id": step.rune_id,
                "route_node": step.route_node,
                "deterministic_order": step.deterministic_order
            }
            for step in sorted(self.steps, key=lambda x: x.deterministic_order)
        ]
        canonical_data = json.dumps(
            {
                "plan_id": self.plan_id,
                "pipeline_id": self.pipeline_id,
                "steps": steps_repr,
            },
            sort_keys=True
        ).encode("utf-8")
        return hashlib.sha256(canonical_data).hexdigest()

def build_invocation_plan(contract, route_graph, rune_catalog):
    """
    Build a RuneInvocationPlan using the given contract and route graph.

    Args:
        contract (dict): The contract defining required runes and their connections.
        route_graph (dict): The graph defining valid routes.
        rune_catalog (dict): Available runes and their schemas.

    Returns:
        RuneInvocationPlan: A validated deterministic plan.
    """
    import uuid

    # Example Procedure for Steps (implement according to exact need):
    steps = []
    for idx, rune in enumerate(contract.get("required_runes", [])):
        if rune not in rune_catalog:
            raise ValueError(f"Rune {rune} does not exist in rune catalog")
        steps.append(
            RuneInvocationStep(
                step_id=str(uuid.uuid4()),
                rune_id=rune,
                input_schema=rune_catalog[rune].get("input_schema"),
                output_schema=rune_catalog[rune].get("output_schema"),
                required_receipts=[],  # Populate based on contract
                route_node=route_graph.get(rune, {}).get("node", "unknown"),
                deterministic_order=idx
            )
        )

    authority = contract.get("authority")
    if not authority.is_locked():
        raise ValueError("Authority must be locked.")

    return RuneInvocationPlan(
        plan_id=str(uuid.uuid4()),
        pipeline_id=contract["pipeline_id"],
        steps=steps,
        authority=authority
    )