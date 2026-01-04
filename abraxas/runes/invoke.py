"""Canonical ABX-Runes invocation API with ctx + provenance."""

from __future__ import annotations

import json
import importlib
from pathlib import Path
from typing import Any

from abraxas.runes.capabilities import load_capability_registry
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


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _validate_with_schema(schema_relpath: str | None, payload: dict[str, Any], *, label: str) -> None:
    if not schema_relpath:
        return
    try:
        import jsonschema  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuneInvocationError(
            "jsonschema is required for capability contract validation. "
            "Install with: pip install 'abraxas[dev]' (or add jsonschema to your environment)."
        ) from exc
    schema_path = _repo_root() / schema_relpath
    if not schema_path.exists():
        raise RuneInvocationError(f"Missing {label} schema: {schema_relpath}")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(instance=payload, schema=schema)
    except jsonschema.ValidationError as exc:
        raise RuneInvocationError(f"{label} schema validation failed: {exc.message}") from exc


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
    # Prefer canonical rune bindings first (e.g., "rune:sds")
    bindings = list_runes_by_capability(capability)
    if bindings:
        if len(bindings) > 1:
            raise RuneInvocationError(f"Multiple runes registered for capability: {capability}")
        return invoke_rune(
            bindings[0].rune_id,
            inputs,
            ctx=ctx,
            ledger=ledger,
            strict_execution=strict_execution,
        )

    # Fall back to capability contracts (e.g., "oracle.v2.run")
    contract_registry = load_capability_registry()
    contract = contract_registry.find_capability(capability)
    if contract is None:
        raise RuneInvocationError(f"No rune registered for capability: {capability}")

    context = require_ctx(ctx)
    ledger = ledger or RuneInvocationLedger()
    operator = _resolve_operator(contract.operator_path)

    _validate_with_schema(contract.input_schema, inputs, label="input")
    try:
        outputs = operator(**inputs, strict_execution=strict_execution)
    except NotImplementedError as exc:
        record = build_record(
            rune_id=contract.rune_id,
            rune_version=contract.version,
            capability=contract.capability_id,
            ctx=context,
            inputs=inputs,
            outputs=None,
            status="stub_blocked",
            error=str(exc),
        )
        ledger.append(record)
        raise RuneStubError(f"Capability {contract.capability_id} operator stubbed.") from exc
    except Exception as exc:
        record = build_record(
            rune_id=contract.rune_id,
            rune_version=contract.version,
            capability=contract.capability_id,
            ctx=context,
            inputs=inputs,
            outputs=None,
            status="failed",
            error=str(exc),
        )
        ledger.append(record)
        raise RuneInvocationError(f"Capability invocation failed for {contract.capability_id}") from exc

    if not isinstance(outputs, dict):
        raise RuneInvocationError(
            f"Capability operator {contract.operator_path} must return dict, got {type(outputs).__name__}"
        )
    _validate_with_schema(contract.output_schema, outputs, label="output")

    record = build_record(
        rune_id=contract.rune_id,
        rune_version=contract.version,
        capability=contract.capability_id,
        ctx=context,
        inputs=inputs,
        outputs=outputs,
        status="ok",
        error=None,
    )
    ledger.append(record)
    return outputs
