"""Tests for forecast.outcome.record capability contract."""

from __future__ import annotations

import pytest

from abraxas.forecast.rune_adapter import record_forecast_outcome_deterministic


def test_record_forecast_outcome_deterministic(tmp_path):
    ledger_path = str(tmp_path / "outcomes.jsonl")
    payload = {
        "pred_id": "pred-123",
        "result": "hit",
        "run_id": "run-001",
        "evidence": [{"source": "test"}],
        "notes": "verified",
        "ts_observed": "2026-01-05T00:00:00+00:00",
        "ledger_path": ledger_path,
    }

    result1 = record_forecast_outcome_deterministic(**payload, seed=42)
    result2 = record_forecast_outcome_deterministic(**payload, seed=42)

    assert result1["outcome"] == result2["outcome"]
    assert result1["provenance"]["inputs_sha256"] == result2["provenance"]["inputs_sha256"]
    assert result1["provenance"]["operation_id"] == "forecast.outcome.record"
    assert result1["not_computable"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
