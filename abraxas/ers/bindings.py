from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Tuple

from .types import TaskSpec


def bind_callable(
    *,
    name: str,
    lane: str,
    priority: int,
    cost_ops: int,
    cost_entropy: int = 0,
    fn: Callable[[Dict[str, Any]], Any],
    tags: Tuple[str, ...] = (),
) -> TaskSpec:
    """
    Wrap any deterministic callable(context)->Any into a TaskSpec.
    """
    return TaskSpec(
        name=name,
        lane=lane,  # "forecast" | "shadow"
        priority=priority,
        cost_ops=cost_ops,
        cost_entropy=cost_entropy,
        fn=fn,
        tags=tags,
    )


def bind_rune_invoke(
    *,
    rune_name: str,
    lane: str,
    priority: int,
    cost_ops: int,
    invoker: Callable[[str, Dict[str, Any]], Any],
    input_key: str = "rune_inputs",
    tags: Tuple[str, ...] = ("rune",),
) -> TaskSpec:
    """
    Adapter for your existing ABX-Runes invocation path.

    Expects context[input_key] to be a dict of rune inputs:
      context["rune_inputs"][rune_name] -> dict
    """

    def _fn(ctx: Dict[str, Any]) -> Any:
        inputs = ctx.get(input_key, {}) or {}
        rune_inputs = inputs.get(rune_name, None)
        if rune_inputs is None:
            # Deterministic "not computable"
            return {"status": "not_computable", "missing": rune_name}
        return invoker(rune_name, rune_inputs)

    return TaskSpec(
        name=f"rune:{rune_name}",
        lane=lane,
        priority=priority,
        cost_ops=cost_ops,
        cost_entropy=0,
        fn=_fn,
        tags=tags,
    )
