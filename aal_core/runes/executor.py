"""Base deterministic rune execution wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Callable, Mapping, MutableMapping, Optional, Sequence


ArtifactStatus = str
SUCCESS: ArtifactStatus = "SUCCESS"
FAILED: ArtifactStatus = "FAILED"
NOT_COMPUTABLE: ArtifactStatus = "NOT_COMPUTABLE"
SCHEMA_VERSION = "aal.runes.execution_artifact.v1"


@dataclass(frozen=True)
class RuneExecutionContext:
    """Execution context for a single rune step."""

    rune_id: str
    run_id: str
    phase: str


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _artifact_id(
    *,
    run_id: str,
    rune_id: str,
    phase: str,
    status: ArtifactStatus,
    inputs: Mapping[str, Any],
    outputs: Mapping[str, Any],
) -> str:
    digest_source = {
        "run_id": run_id,
        "rune_id": rune_id,
        "phase": phase,
        "status": status,
        "inputs": inputs,
        "outputs": outputs,
    }
    digest = hashlib.sha256(_canonical_json(digest_source).encode("utf-8")).hexdigest()
    return f"art.{digest[:16]}"


def execute_rune(
    *,
    rune_id: str,
    run_id: str,
    phase: str,
    step: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    inputs: Mapping[str, Any],
    provenance: Mapping[str, Any],
    correlation_pointers: Optional[Sequence[Mapping[str, str]]] = None,
    ledger_record_ids: Optional[Sequence[str]] = None,
    ledger_artifact_ids: Optional[Sequence[str]] = None,
) -> MutableMapping[str, Any]:
    """Execute one rune step and normalize output into artifact envelope schema."""

    context = RuneExecutionContext(rune_id=rune_id, run_id=run_id, phase=phase)
    timestamp = _utc_timestamp()

    status: ArtifactStatus = SUCCESS
    normalized_outputs: Mapping[str, Any]

    try:
        raw_output = step(inputs)
        if raw_output is None:
            status = NOT_COMPUTABLE
            normalized_outputs = {
                "payload": None,
                "summary": "Execution returned no output.",
                "errors": ["STEP_RETURNED_NONE"],
            }
        elif isinstance(raw_output, Mapping):
            normalized_outputs = dict(raw_output)
            if normalized_outputs.get("status") == NOT_COMPUTABLE:
                status = NOT_COMPUTABLE
        else:
            status = FAILED
            normalized_outputs = {
                "payload": None,
                "summary": "Execution returned non-mapping output.",
                "errors": ["STEP_RETURN_TYPE_INVALID"],
            }
    except Exception as exc:  # deterministic failure envelope
        status = FAILED
        normalized_outputs = {
            "payload": None,
            "summary": "Rune execution raised an exception.",
            "errors": [f"{type(exc).__name__}: {exc}"],
        }

    normalized_inputs = dict(inputs)
    normalized_provenance = dict(provenance)
    normalized_provenance.setdefault("source_refs", [])

    artifact_id = _artifact_id(
        run_id=context.run_id,
        rune_id=context.rune_id,
        phase=context.phase,
        status=status,
        inputs=normalized_inputs,
        outputs=normalized_outputs,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": context.run_id,
        "artifact_id": artifact_id,
        "rune_id": context.rune_id,
        "timestamp": timestamp,
        "phase": context.phase,
        "status": status,
        "inputs": normalized_inputs,
        "outputs": dict(normalized_outputs),
        "provenance": normalized_provenance,
        "ledger_record_ids": list(ledger_record_ids or []),
        "ledger_artifact_ids": list(ledger_artifact_ids or []),
        "correlation_pointers": list(correlation_pointers or []),
    }
