"""Tests for rune invocation ctx enforcement and provenance logging."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from abraxas.runes.invoke import invoke_rune, RuneStubError
from abraxas.runes.ledger import RuneInvocationLedger


def test_invoke_requires_ctx() -> None:
    with pytest.raises(ValueError, match="ctx is required"):
        invoke_rune("ϟ₁", {}, ctx=None)


def test_invoke_logs_stub_blocked(tmp_path: Path) -> None:
    ledger_path = tmp_path / "runes.jsonl"
    ledger = RuneInvocationLedger(ledger_path)
    ctx = {
        "run_id": "test-run",
        "subsystem_id": "test",
        "git_hash": "deadbeef",
    }
    with pytest.raises(RuneStubError):
        invoke_rune(
            "ϟ₁",
            {
                "semantic_field": {},
                "context_vector": {},
                "anchor_candidates": [],
            },
            ctx=ctx,
            ledger=ledger,
            strict_execution=True,
        )

    lines = [line for line in ledger_path.read_text().splitlines() if line]
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["status"] == "stub_blocked"
    assert entry["ctx"]["subsystem_id"] == "test"
    assert entry["rune_id"] == "ϟ₁"
