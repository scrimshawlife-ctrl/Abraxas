"""Provenance ledger for ABX-Runes invocations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from abraxas.core.provenance import hash_canonical_json
from abraxas.runes.ctx import RuneInvocationContext


@dataclass(frozen=True)
class RuneInvocationRecord:
    rune_id: str
    rune_version: str
    capability: str
    ctx: RuneInvocationContext
    inputs: dict[str, Any]
    outputs: dict[str, Any] | None
    status: str
    error: str | None
    timestamp_utc: str
    inputs_hash: str
    outputs_hash: str | None
    ctx_hash: str


class RuneInvocationLedger:
    """Append-only JSONL ledger for rune invocations."""

    def __init__(self, ledger_path: str | Path | None = None) -> None:
        if ledger_path is None:
            ledger_path = Path(".aal/ledger/rune_invocations.jsonl")
        self.ledger_path = Path(ledger_path)
        self._ensure_ledger_exists()

    def _ensure_ledger_exists(self) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.ledger_path.exists():
            self.ledger_path.touch()

    def append(self, record: RuneInvocationRecord) -> str:
        payload = {
            "rune_id": record.rune_id,
            "rune_version": record.rune_version,
            "capability": record.capability,
            "ctx": record.ctx.model_dump(),
            "inputs": record.inputs,
            "outputs": record.outputs,
            "status": record.status,
            "error": record.error,
            "timestamp_utc": record.timestamp_utc,
            "inputs_hash": record.inputs_hash,
            "outputs_hash": record.outputs_hash,
            "ctx_hash": record.ctx_hash,
        }
        entry_hash = hash_canonical_json(payload)
        payload["ledger_sha256"] = entry_hash
        with open(self.ledger_path, "a") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
        return entry_hash


def build_record(
    *,
    rune_id: str,
    rune_version: str,
    capability: str,
    ctx: RuneInvocationContext,
    inputs: dict[str, Any],
    outputs: dict[str, Any] | None,
    status: str,
    error: str | None,
) -> RuneInvocationRecord:
    timestamp = datetime.now(timezone.utc).isoformat()
    inputs_hash = hash_canonical_json(inputs)
    outputs_hash = hash_canonical_json(outputs) if outputs is not None else None
    ctx_hash = hash_canonical_json(ctx.model_dump())
    return RuneInvocationRecord(
        rune_id=rune_id,
        rune_version=rune_version,
        capability=capability,
        ctx=ctx,
        inputs=inputs,
        outputs=outputs,
        status=status,
        error=error,
        timestamp_utc=timestamp,
        inputs_hash=inputs_hash,
        outputs_hash=outputs_hash,
        ctx_hash=ctx_hash,
    )
