"""
abx_familiar.ir - Intermediate Representation layer

Exports:
    TaskGraphIR: Deterministic, hashable task graph representation
    TIER_SCOPES: Valid tier scope values
    MODES: Valid mode values
    EvidenceItem: Single evidence reference with provenance
    EvidencePack: Container for evidence references
    SOURCE_TYPES: Valid evidence source types
    CONFIDENCE_CLASSES: Valid confidence classifications
    RuneInvocation: Single rune call description
    DependencyEdge: Dependency relationship between invocations
    BudgetAllocation: Budget targets for plan execution
    InvocationPlan: Plan describing rune invocations and dependencies
    DETERMINISM_CLASSES: Valid determinism classifications
    SIDE_EFFECTS: Valid side effect classifications
"""

from abx_familiar.ir.task_graph_ir_v0 import (
    TaskGraphIR,
    TIER_SCOPES,
    MODES,
)

from abx_familiar.ir.evidence_pack_v0 import (
    EvidenceItem,
    EvidencePack,
    SOURCE_TYPES,
    CONFIDENCE_CLASSES,
)

from abx_familiar.ir.invocation_plan_v0 import (
    RuneInvocation,
    DependencyEdge,
    BudgetAllocation,
    InvocationPlan,
    DETERMINISM_CLASSES,
    SIDE_EFFECTS,
)

__all__ = [
    # Task Graph IR
    "TaskGraphIR",
    "TIER_SCOPES",
    "MODES",
    # Evidence Pack IR
    "EvidenceItem",
    "EvidencePack",
    "SOURCE_TYPES",
    "CONFIDENCE_CLASSES",
    # Invocation Plan IR
    "RuneInvocation",
    "DependencyEdge",
    "BudgetAllocation",
    "InvocationPlan",
    "DETERMINISM_CLASSES",
    "SIDE_EFFECTS",
]
