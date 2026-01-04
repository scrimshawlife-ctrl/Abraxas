from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

Lane = Literal["forecast", "shadow"]
Status = Literal["ok", "skipped_budget", "error", "not_computable"]


@dataclass(frozen=True)
class Budget:
    """
    Deterministic budget envelope for a single tick.
    - ops: abstract 'work units' (cheap, deterministic)
    - entropy: abstract 'complexity cost' proxy (cheap, deterministic)
    """
    ops: int
    entropy: int = 0

    def can_afford(self, ops: int, entropy: int = 0) -> bool:
        return ops <= self.ops and entropy <= self.entropy


@dataclass(frozen=True)
class TaskSpec:
    """
    A deterministic task.
    - name: stable identifier
    - lane: forecast tasks run before shadow
    - priority: lower is earlier (0 is highest)
    - cost_ops/cost_entropy: declared deterministic costs
    - fn: callable(context) -> result
    """
    name: str
    lane: Lane
    priority: int
    cost_ops: int
    cost_entropy: int = 0
    fn: Callable[[Dict[str, Any]], Any] = field(repr=False, default=lambda _: None)
    tags: Tuple[str, ...] = ()


@dataclass(frozen=True)
class TraceEvent:
    """
    Trace event suitable for later AAL-Viz ingestion.
    """
    tick: int
    task: str
    lane: Lane
    status: Status
    cost_ops: int
    cost_entropy: int
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskResult:
    name: str
    lane: Lane
    status: Status
    value: Any = None
    error: Optional[str] = None
    cost_ops: int = 0
    cost_entropy: int = 0
