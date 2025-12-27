"""Canonical ABX-Runes invocation API with ctx + provenance."""

from __future__ import annotations

import importlib
from typing import Any

from abraxas.runes.ctx import RuneInvocationContext, require_ctx
from abraxas.runes.ledger import RuneInvocationLedger, build_record
from abraxas.runes.registry import describe_rune, list_runes_by_capability


class RuneInvocationError(RuntimeError):
    """Raised when rune invocation fails."""


class RuneStubError(RuneInvocationError):
    """Raised when a rune operator is a stub and cannot execute."""


def _resolve_operator(operator_path: str):
    module_path, func_name = operator_path.split(":", 1)
    module = importlib.import_module(module_path)
    try:
        return getattr(module, func_name)
    except AttributeError as exc:
        raise RuneInvocationError(
            f"Missing operator function {func_name} in {module_path}"
        ) from exc


def invoke_rune(
    rune_id: str,
    inputs: dict[str, Any],
    *,
    ctx: RuneInvocationContext | dict,
    ledger: RuneInvocationLedger | None = None,
    strict_execution: bool = True,
) -> dict[str, Any]:
    context = require_ctx(ctx)
    ledger = ledger or RuneInvocationLedger()
    binding = describe_rune(rune_id)
    operator = _resolve_operator(binding.operator_path)

    try:
        outputs = operator(**inputs, strict_execution=strict_execution)
    except NotImplementedError as exc:
        record = build_record(
            rune_id=binding.rune_id,
            rune_version=binding.version,
            capability=binding.capability,
            ctx=context,
            inputs=inputs,
            outputs=None,
            status="stub_blocked",
            error=str(exc),
        )
        ledger.append(record)
        raise RuneStubError(
            f"Rune {binding.rune_id} operator stubbed. Provide implementation before use."
        ) from exc
    except Exception as exc:
        record = build_record(
            rune_id=binding.rune_id,
            rune_version=binding.version,
            capability=binding.capability,
            ctx=context,
            inputs=inputs,
            outputs=None,
            status="failed",
            error=str(exc),
        )
        ledger.append(record)
        raise RuneInvocationError(f"Rune invocation failed for {binding.rune_id}") from exc

    record = build_record(
        rune_id=binding.rune_id,
        rune_version=binding.version,
        capability=binding.capability,
        ctx=context,
        inputs=inputs,
        outputs=outputs,
        status="ok",
        error=None,
    )
    ledger.append(record)
    return outputs


def invoke_capability(
    capability: str,
    inputs: dict[str, Any],
    *,
    ctx: RuneInvocationContext | dict,
    ledger: RuneInvocationLedger | None = None,
    strict_execution: bool = True,
) -> dict[str, Any]:
    bindings = list_runes_by_capability(capability)
    if not bindings:
        raise RuneInvocationError(f"No rune registered for capability: {capability}")
    if len(bindings) > 1:
        raise RuneInvocationError(
            f"Multiple runes registered for capability: {capability}"
        )
    return invoke_rune(
        bindings[0].rune_id,
        inputs,
        ctx=ctx,
        ledger=ledger,
        strict_execution=strict_execution,
    )
