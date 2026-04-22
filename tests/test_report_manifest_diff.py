from __future__ import annotations

import json
from pathlib import Path

import jsonschema

import abx.report_manifest_diff as manifest_diff


def _record(*, artifact_id: str, artifact_type: str, digest: str, stale: bool, status: str) -> dict:
    return {
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "path": f"out/reports/{artifact_type}.json",
        "timestamp_utc": "2026-04-21T00:00:00Z",
        "freshness": {"is_stale": stale, "age_seconds": 0},
        "hash": digest,
        "source_command": "cmd",
        "provenance": {"status": status},
    }


def test_correct_diff_detection(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(manifest_diff, "PREVIOUS_PATH", tmp_path / "report_manifest.previous.json")

    previous = [
        _record(artifact_id="cmp-old", artifact_type="comparison", digest="h1", stale=False, status="OK"),
        _record(artifact_id="inv-old", artifact_type="invariance", digest="h2", stale=False, status="OK"),
    ]
    current = [
        _record(artifact_id="cmp-new", artifact_type="comparison", digest="h9", stale=True, status="NOT_COMPUTABLE"),
        _record(artifact_id="dev-new", artifact_type="developer_readiness", digest="h3", stale=False, status="OK"),
    ]

    payload = manifest_diff.build_report_manifest_diff(
        current_manifest=current,
        previous_manifest=previous,
        timestamp_utc="2026-04-21T00:00:01Z",
    )
    diff = payload["diff"]

    assert payload["status"] == "OK"
    assert diff["hash_changed"] == ["comparison"]
    assert diff["freshness_changed"] == ["comparison"]
    assert diff["status_changed"] == ["comparison"]
    assert set(diff["added"]) == {"cmp-new", "dev-new"}
    assert set(diff["removed"]) == {"cmp-old", "inv-old"}


def test_missing_previous_manifest_not_computable(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(manifest_diff, "PREVIOUS_PATH", tmp_path / "report_manifest.previous.json")
    payload = manifest_diff.build_report_manifest_diff(
        current_manifest=[],
        previous_manifest=None,
        timestamp_utc="2026-04-21T00:00:01Z",
    )
    assert payload["status"] == "NOT_COMPUTABLE"
    assert payload["diff"]["provenance"]["status"] == "NOT_COMPUTABLE"


def test_deterministic_output() -> None:
    current = [_record(artifact_id="dev", artifact_type="developer_readiness", digest="h1", stale=False, status="OK")]
    previous = [_record(artifact_id="dev", artifact_type="developer_readiness", digest="h1", stale=False, status="OK")]
    a = manifest_diff.build_report_manifest_diff(current_manifest=current, previous_manifest=previous, timestamp_utc="2026-04-21T00:00:01Z")
    b = manifest_diff.build_report_manifest_diff(current_manifest=current, previous_manifest=previous, timestamp_utc="2026-04-21T00:00:01Z")
    assert a == b


def test_no_false_positives_and_schema() -> None:
    current = [_record(artifact_id="dev", artifact_type="developer_readiness", digest="h1", stale=False, status="OK")]
    previous = [_record(artifact_id="dev", artifact_type="developer_readiness", digest="h1", stale=False, status="OK")]
    payload = manifest_diff.build_report_manifest_diff(current_manifest=current, previous_manifest=previous, timestamp_utc="2026-04-21T00:00:01Z")
    diff = payload["diff"]
    assert diff["added"] == []
    assert diff["removed"] == []
    assert diff["hash_changed"] == []
    assert diff["freshness_changed"] == []
    assert diff["status_changed"] == []
    assert diff["unchanged_count"] == 1

    schema = json.loads(Path("schemas/ReportManifestDiff.v1.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(diff)
