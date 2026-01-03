"""
ERS — Execution & Resource Scheduler (v0.2)

Deterministic tick scheduler for Abraxas.
Shadow lane is observation-only; forecast lane is high priority.
"""

from .types import Budget, TaskSpec, TaskResult, TraceEvent
from .scheduler import DeterministicScheduler
from .trace import canonicalize_trace, trace_hash_sha256, trace_json_bytes
from .invariance import InvarianceResult, dozen_run_invariance_gate

__all__ = [
    "Budget", "TaskSpec", "TaskResult", "TraceEvent",
    "DeterministicScheduler",
    "canonicalize_trace", "trace_hash_sha256", "trace_json_bytes",
    "InvarianceResult", "dozen_run_invariance_gate",
]
