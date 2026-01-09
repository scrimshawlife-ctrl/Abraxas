"""Tests for artifacts.proof_bundle.generate capability contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from abraxas.artifacts.rune_adapter import generate_proof_bundle_deterministic


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_generate_proof_bundle_deterministic(tmp_path):
    run_id = "run-proof-001"
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    a_path = artifacts_dir / "a.json"
    b_path = artifacts_dir / "b.json"
    _write_json(a_path, {"policy": {"non_truncation": True}})
    _write_json(b_path, {"policy": {"non_truncation": False}})

    bundle_root = str(tmp_path / "bundles")
    payload = {
        "run_id": run_id,
        "artifacts": {"a_json": str(a_path), "b_json": str(b_path)},
        "bundle_root": bundle_root,
        "ledger_pointer": {"predictions": "out/forecast_ledger/predictions.jsonl"},
        "ts": "2026-01-05T00:00:00+00:00",
    }

    result1 = generate_proof_bundle_deterministic(**payload, seed=7)
    result2 = generate_proof_bundle_deterministic(**payload, seed=7)

    assert result1["bundle"]["bundle_dir"] == result2["bundle"]["bundle_dir"]
    assert result1["provenance"]["inputs_sha256"] == result2["provenance"]["inputs_sha256"]
    assert result1["provenance"]["operation_id"] == "artifacts.proof_bundle.generate"
    assert result1["not_computable"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
