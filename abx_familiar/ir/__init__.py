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
    WardFlag: Single governance signal
    WardReport: Governance findings report
    DRIFT_CLASSES: Valid drift classifications
    ContinuityLedgerEntry: Append-only run continuity record
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

from abx_familiar.ir.ward_report_v0 import (
    WardFlag,
    WardReport,
    DRIFT_CLASSES,
)

from abx_familiar.ir.continuity_ledger_v0 import (
    ContinuityLedgerEntry,
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
    # Ward Report IR
    "WardFlag",
    "WardReport",
    "DRIFT_CLASSES",
    # Continuity Ledger IR
    "ContinuityLedgerEntry",
]
