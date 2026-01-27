"""
abx_familiar.ir - Intermediate Representation layer

Exports:
    TaskGraphIR: Deterministic, hashable task graph representation
    TIER_SCOPES: Valid tier scope values
    MODES: Valid mode values
"""

from abx_familiar.ir.task_graph_ir_v0 import (
    TaskGraphIR,
    TIER_SCOPES,
    MODES,
)

__all__ = [
    "TaskGraphIR",
    "TIER_SCOPES",
    "MODES",
]
