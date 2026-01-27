"""
InvocationPlan.v0

Deterministic, hashable plan describing a set of rune invocations and their
declared dependency edges.

This IR contains NO execution logic and NO scheduling decisions beyond
explicitly declared dependencies and budget allocation fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import hashlib
import json


# -------------------------
# Canonical Enums (v0)
# -------------------------

DETERMINISM_CLASSES = {"strict", "bounded", "n_a"}
SIDE_EFFECTS = {"none", "ledger_append", "scheduled_execution", "external_read_only", "n_a"}


# -------------------------
# Helpers
# -------------------------

def _stable_json(data: Dict[str, Any]) -> str:
    """
    Produce a stable JSON string for hashing.
    Sorting and separators are fixed to guarantee determinism.
    """
    return json.dumps(
        data,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    )


def _hash_payload(payload: Dict[str, Any]) -> str:
    stable = _stable_json(payload)
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


# -------------------------
# IR Definitions
# -------------------------

@dataclass(frozen=True)
class RuneInvocation:
    """
    RuneInvocation.v0

    Describes a single rune call by ID with a declared input contract reference
    and bounded parameter payload.

    Rules:
    - params must be JSON-serializable.
    - input_contract_ref is a string pointer (e.g., "TaskGraphIR.v0") to avoid
      importing upstream schema types here.
    """

    invocation_id: str
    rune_id: str
    input_contract_ref: str

    # Bounded parameter payload; do NOT embed raw evidence text here.
    params: Dict[str, Any] = field(default_factory=dict)

    determinism: str = "n_a"  # strict | bounded | n_a
    side_effects: str = "n_a"  # none | ledger_append | scheduled_execution | external_read_only | n_a

    cost_class: Optional[str] = None  # e.g., "S", "M", "L" or any policy-defined class
    estimated_duration_ms: Optional[int] = None

    not_computable: bool = False
    missing_fields: List[str] = field(default_factory=list)

    def validate(self) -> None:
        if self.determinism not in DETERMINISM_CLASSES:
            raise ValueError(f"Invalid determinism: {self.determinism}")
        if self.side_effects not in SIDE_EFFECTS:
            raise ValueError(f"Invalid side_effects: {self.side_effects}")

        if not isinstance(self.params, dict):
            raise ValueError("params must be a dict")

        # Ensure JSON-serializable deterministically by attempting stable dump
        try:
            _stable_json(self.params)
        except Exception as e:
            raise ValueError(f"params must be JSON-serializable: {e}") from e

        if self.estimated_duration_ms is not None and self.estimated_duration_ms < 0:
            raise ValueError("estimated_duration_ms must be non-negative")

        if self.not_computable and not self.missing_fields:
            raise ValueError("not_computable=True requires missing_fields to be non-empty")

    def to_payload(self) -> Dict[str, Any]:
        return {
            "invocation_id": self.invocation_id,
            "rune_id": self.rune_id,
            "input_contract_ref": self.input_contract_ref,
            "params": self.params,
            "determinism": self.determinism,
            "side_effects": self.side_effects,
            "cost_class": self.cost_class,
            "estimated_duration_ms": self.estimated_duration_ms,
            "not_computable": self.not_computable,
            "missing_fields": list(self.missing_fields),
        }

    def hash(self) -> str:
        self.validate()
        return _hash_payload(self.to_payload())


@dataclass(frozen=True)
class DependencyEdge:
    """
    DependencyEdge.v0

    Declares that `after_invocation_id` depends on `before_invocation_id`.
    """

    before_invocation_id: str
    after_invocation_id: str

    def validate(self) -> None:
        if not self.before_invocation_id or not self.after_invocation_id:
            raise ValueError("DependencyEdge invocation ids must be non-empty")
        if self.before_invocation_id == self.after_invocation_id:
            raise ValueError("DependencyEdge cannot be self-referential")

    def to_payload(self) -> Dict[str, Any]:
        return {
            "before_invocation_id": self.before_invocation_id,
            "after_invocation_id": self.after_invocation_id,
        }


@dataclass(frozen=True)
class BudgetAllocation:
    """
    BudgetAllocation.v0

    Optional budget targets. Enforcement occurs elsewhere; this IR just declares intent.
    """

    compute_budget: Optional[float] = None
    time_budget_ms: Optional[int] = None

    def validate(self) -> None:
        if self.compute_budget is not None and self.compute_budget < 0:
            raise ValueError("compute_budget must be non-negative")
        if self.time_budget_ms is not None and self.time_budget_ms < 0:
            raise ValueError("time_budget_ms must be non-negative")

    def to_payload(self) -> Dict[str, Any]:
        return {
            "compute_budget": self.compute_budget,
            "time_budget_ms": self.time_budget_ms,
        }


@dataclass(frozen=True)
class InvocationPlan:
    """
    InvocationPlan.v0

    Rules:
    - Pure declaration: no scheduling or execution.
    - dependency_edges must refer to invocation_ids that exist in rune_invocations.
    """

    plan_id: str
    rune_invocations: List[RuneInvocation] = field(default_factory=list)
    dependency_edges: List[DependencyEdge] = field(default_factory=list)
    budget_allocation: BudgetAllocation = field(default_factory=BudgetAllocation)

    not_computable: bool = False
    missing_fields: List[str] = field(default_factory=list)

    def validate(self) -> None:
        if not isinstance(self.rune_invocations, list):
            raise ValueError("rune_invocations must be a list")

        invocation_ids = set()
        for inv in self.rune_invocations:
            if not isinstance(inv, RuneInvocation):
                raise ValueError("rune_invocations must contain RuneInvocation objects")
            inv.validate()
            if inv.invocation_id in invocation_ids:
                raise ValueError(f"Duplicate invocation_id: {inv.invocation_id}")
            invocation_ids.add(inv.invocation_id)

        if not isinstance(self.dependency_edges, list):
            raise ValueError("dependency_edges must be a list")

        for edge in self.dependency_edges:
            if not isinstance(edge, DependencyEdge):
                raise ValueError("dependency_edges must contain DependencyEdge objects")
            edge.validate()
            if edge.before_invocation_id not in invocation_ids:
                raise ValueError(f"DependencyEdge before id not found: {edge.before_invocation_id}")
            if edge.after_invocation_id not in invocation_ids:
                raise ValueError(f"DependencyEdge after id not found: {edge.after_invocation_id}")

        if not isinstance(self.budget_allocation, BudgetAllocation):
            raise ValueError("budget_allocation must be a BudgetAllocation")
        self.budget_allocation.validate()

        if self.not_computable and not self.missing_fields:
            raise ValueError("not_computable=True requires missing_fields to be non-empty")

    def to_payload(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "rune_invocations": [inv.to_payload() for inv in self.rune_invocations],
            "dependency_edges": [e.to_payload() for e in self.dependency_edges],
            "budget_allocation": self.budget_allocation.to_payload(),
            "not_computable": self.not_computable,
            "missing_fields": list(self.missing_fields),
        }

    def hash(self) -> str:
        self.validate()
        return _hash_payload(self.to_payload())

    def semantically_equal(self, other: "InvocationPlan") -> bool:
        if not isinstance(other, InvocationPlan):
            return False
        return self.hash() == other.hash()
