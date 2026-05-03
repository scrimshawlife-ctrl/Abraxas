from __future__ import annotations

from abraxas.registry.notion_sync_validator import run_notion_sync_validator


def test_notion_sync_validator_runs() -> None:
    result = run_notion_sync_validator()
    assert result["schema_version"] == "NotionSyncValidatorRun.v1"
    assert result["status"] in {"PASS", "FAIL"}
    assert "missing_in_map" in result
    assert "extra_in_map" in result


def test_notion_sync_validator_deterministic() -> None:
    first = run_notion_sync_validator()
    second = run_notion_sync_validator()
    assert first["canonical_hash"] == second["canonical_hash"]
