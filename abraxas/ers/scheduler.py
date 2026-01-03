from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from .types import Budget, TaskResult, TaskSpec, TraceEvent


@dataclass
class DeterministicScheduler:
    """
    ERS v0.1 — deterministic, tick-based scheduler.

    Ordering is stable:
      (lane_order, priority, name, insertion_index)

    lane_order: forecast first, then shadow.

    This module does not use wall clock time or randomness.
    """
    tasks: List[TaskSpec] = field(default_factory=list)
    _insert_counter: int = 0
    _insert_index: Dict[str, int] = field(default_factory=dict)

    def add(self, task: TaskSpec) -> None:
        # deterministic insertion ordering
        if task.name in self._insert_index:
            # Preserve determinism: disallow duplicate names
            raise ValueError(f"Duplicate task name: {task.name}")
        self._insert_index[task.name] = self._insert_counter
        self._insert_counter += 1
        self.tasks.append(task)

    def _sort_key(self, task: TaskSpec) -> Tuple[int, int, str, int]:
        lane_order = 0 if task.lane == "forecast" else 1
        return (lane_order, task.priority, task.name, self._insert_index[task.name])

    def run_tick(
        self,
        tick: int,
        budget_forecast: Budget,
        budget_shadow: Budget,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Returns:
          {
            "tick": int,
            "results": {task_name: TaskResult},
            "trace": [TraceEvent...],
            "remaining": {"forecast": Budget, "shadow": Budget},
          }
        """
        # Work with mutable counters, but output remains deterministic.
        rem_f_ops, rem_f_ent = budget_forecast.ops, budget_forecast.entropy
        rem_s_ops, rem_s_ent = budget_shadow.ops, budget_shadow.entropy

        results: Dict[str, TaskResult] = {}
        trace: List[TraceEvent] = []

        for task in sorted(self.tasks, key=self._sort_key):
            if task.lane == "forecast":
                can = task.cost_ops <= rem_f_ops and task.cost_entropy <= rem_f_ent
            else:
                can = task.cost_ops <= rem_s_ops and task.cost_entropy <= rem_s_ent

            if not can:
                res = TaskResult(
                    name=task.name,
                    lane=task.lane,
                    status="skipped_budget",
                    value=None,
                    error=None,
                    cost_ops=0,
                    cost_entropy=0,
                )
                results[task.name] = res
                trace.append(
                    TraceEvent(
                        tick=tick,
                        task=task.name,
                        lane=task.lane,
                        status="skipped_budget",
                        cost_ops=task.cost_ops,
                        cost_entropy=task.cost_entropy,
                        meta={"reason": "budget"},
                    )
                )
                continue

            try:
                value = task.fn(context)
                status = "ok"
                err = None
            except Exception as e:
                value = None
                status = "error"
                err = f"{type(e).__name__}: {e}"

            # Apply cost only if attempted (ok or error).
            if task.lane == "forecast":
                rem_f_ops -= task.cost_ops
                rem_f_ent -= task.cost_entropy
            else:
                rem_s_ops -= task.cost_ops
                rem_s_ent -= task.cost_entropy

            res = TaskResult(
                name=task.name,
                lane=task.lane,
                status=status,
                value=value,
                error=err,
                cost_ops=task.cost_ops,
                cost_entropy=task.cost_entropy,
            )
            results[task.name] = res
            trace.append(
                TraceEvent(
                    tick=tick,
                    task=task.name,
                    lane=task.lane,
                    status=status,
                    cost_ops=task.cost_ops,
                    cost_entropy=task.cost_entropy,
                    meta={"tags": list(task.tags)},
                )
            )

        return {
            "tick": tick,
            "results": results,
            "trace": trace,
            "remaining": {
                "forecast": Budget(ops=rem_f_ops, entropy=rem_f_ent),
                "shadow": Budget(ops=rem_s_ops, entropy=rem_s_ent),
            },
        }
