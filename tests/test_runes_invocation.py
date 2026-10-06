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


def test_invoke_logs_stub_blocked(tmp_path: Path, monkeypatch) -> None:
    """Verify the stub-blocking mechanism, with a stub INJECTED.

    This previously invoked rune ϟ₁ (RFA) and expected RuneStubError, because RFA was a
    stub when the test was written. RFA has since been implemented -- apply_rfa returns a
    real anchored-field result -- so the test silently stopped testing anything and failed
    with DID NOT RAISE.

    No rune in the repo is currently a stub, so a test that depends on one existing cannot
    be stable. Inject the stub instead: that exercises the same mechanism in invoke_rune
    (operator raises NotImplementedError -> ledger record with status="stub_blocked" ->
    RuneStubError) without depending on which runes happen to be implemented.
    """
    ledger_path = tmp_path / "runes.jsonl"
    ledger = RuneInvocationLedger(ledger_path)
    ctx = {
        "run_id": "test-run",
        "subsystem_id": "test",
        "git_hash": "deadbeef",
    }

    def _stub_operator(**kwargs):  # noqa: ANN003
        raise NotImplementedError("operator is a stub")

    monkeypatch.setattr(
        "abraxas.runes.invoke._resolve_operator", lambda _path: _stub_operator
    )

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
