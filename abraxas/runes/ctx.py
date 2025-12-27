"""Rune invocation context contract for ABX-Runes."""

from __future__ import annotations

from pydantic import BaseModel, Field, ValidationError


class RuneInvocationContext(BaseModel):
    """Required context for rune invocations."""

    run_id: str = Field(..., description="Stable ID for this run/session")
    subsystem_id: str = Field(..., description="Caller subsystem identifier")
    git_hash: str = Field(..., description="Repo revision identifier")


def require_ctx(ctx: RuneInvocationContext | dict | None) -> RuneInvocationContext:
    """Validate and return rune invocation context.

    Raises:
        ValueError: If ctx is missing or invalid.
    """
    if ctx is None:
        raise ValueError("Rune invocation ctx is required")
    try:
        return ctx if isinstance(ctx, RuneInvocationContext) else RuneInvocationContext(**ctx)
    except ValidationError as exc:
        raise ValueError(f"Invalid rune invocation ctx: {exc}") from exc
