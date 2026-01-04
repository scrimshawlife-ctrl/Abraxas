from __future__ import annotations

from abraxas.runes.invoke import invoke_capability


def test_invoke_capability_contract_roundtrip() -> None:
    ctx = {"run_id": "TEST_RUN", "subsystem_id": "tests", "git_hash": "deadbeef"}
    out = invoke_capability(
        "evolve.non_truncation.enforce",
        {"artifact": {"version": "x"}, "raw_full": {"k": "v"}},
        ctx=ctx,
        strict_execution=True,
    )
    assert isinstance(out, dict)
    assert "artifact" in out
    assert out["artifact"]["policy"]["non_truncation"] is True
    assert out["artifact"]["raw_full"] == {"k": "v"}


def test_invoke_capability_contract_appends_chained_jsonl(tmp_path) -> None:
    ctx = {"run_id": "TEST_RUN", "subsystem_id": "tests", "git_hash": "deadbeef"}
    ledger_path = str(tmp_path / "ledger.jsonl")

    out1 = invoke_capability(
        "evolve.ledger.append_chained_jsonl",
        {"ledger_path": ledger_path, "record": {"run_id": "A", "x": 1}},
        ctx=ctx,
        strict_execution=True,
    )
    assert out1["prev_hash"] == "genesis"
    assert isinstance(out1["step_hash"], str) and len(out1["step_hash"]) == 64

    out2 = invoke_capability(
        "evolve.ledger.append_chained_jsonl",
        {"ledger_path": ledger_path, "record": {"run_id": "B", "x": 2}},
        ctx=ctx,
        strict_execution=True,
    )
    assert out2["prev_hash"] == out1["step_hash"]
    assert out2["step_hash"] != out1["step_hash"]


def test_invoke_capability_contract_forecast_helpers() -> None:
    ctx = {"run_id": "TEST_RUN", "subsystem_id": "tests", "git_hash": "deadbeef"}

    hb = invoke_capability(
        "forecast.horizon_bins.horizon_bucket",
        {"horizon": "Weeks"},
        ctx=ctx,
        strict_execution=True,
    )
    assert hb["bucket"] == "weeks"

    br = invoke_capability(
        "forecast.scoring.brier_score",
        {"probs": [0.0, 1.0], "outcomes": [0, 1]},
        ctx=ctx,
        strict_execution=True,
    )
    assert float(br["brier"]) == 0.0

    cand = invoke_capability(
        "forecast.policy_candidates.v0_1",
        {},
        ctx=ctx,
        strict_execution=True,
    )["candidates"]
    assert "balanced" in cand


