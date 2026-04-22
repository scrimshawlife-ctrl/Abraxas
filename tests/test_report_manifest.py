from __future__ import annotations

import json
from pathlib import Path

import jsonschema

import abx.report_manifest as report_manifest


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_schema_compliance_and_deterministic_order(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(report_manifest, "ROOT", tmp_path)
    monkeypatch.setattr(
        report_manifest,
        "ARTIFACT_SPECS",
        [
            {"artifact_type": "developer_readiness", "path": "a/developer.json", "source_command": "cmd1"},
            {"artifact_type": "invariance", "path": "b/invariance.json", "source_command": "cmd2"},
            {"artifact_type": "comparison", "path": "c/comparison.json", "source_command": "cmd3"},
            {"artifact_type": "preflight", "path": "d/preflight.json", "source_command": "cmd4"},
            {"artifact_type": "reporting_cycle", "path": "e/cycle.json", "source_command": "cmd5"},
        ],
    )

    _write(tmp_path / "a/developer.json", {"timestamp_utc": "2026-04-21T00:00:00Z"})
    _write(tmp_path / "b/invariance.json", {"provenance": {"projection_generated_at": "2026-04-21T00:00:00Z"}})
    _write(tmp_path / "c/comparison.json", {"timestamp_utc": "2026-04-21T00:00:00Z"})
    _write(tmp_path / "d/preflight.json", {"timestamp_utc": "2026-04-21T00:00:00Z"})
    _write(tmp_path / "e/cycle.json", {"timestamp_utc": "2026-04-21T00:00:00Z"})

    rows = report_manifest.build_report_manifest(current_time_utc="2026-04-21T00:00:01Z")
    assert [row["artifact_type"] for row in rows] == [
        "comparison",
        "developer_readiness",
        "invariance",
        "preflight",
        "reporting_cycle",
    ]

    schema = json.loads(Path("schemas/ReportManifestRecord.v1.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for row in rows:
        validator.validate(row)


def test_missing_files_not_computable(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(report_manifest, "ROOT", tmp_path)
    monkeypatch.setattr(
        report_manifest,
        "ARTIFACT_SPECS",
        [{"artifact_type": "developer_readiness", "path": "missing.json", "source_command": "cmd"}],
    )
    rows = report_manifest.build_report_manifest(current_time_utc="2026-04-21T00:00:00Z")
    assert rows[0]["timestamp_utc"] == "NOT_COMPUTABLE"
    assert rows[0]["hash"] == "NOT_COMPUTABLE"
    assert rows[0]["provenance"]["status"] == "NOT_COMPUTABLE"


def test_freshness_propagation(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(report_manifest, "ROOT", tmp_path)
    monkeypatch.setattr(
        report_manifest,
        "ARTIFACT_SPECS",
        [{"artifact_type": "comparison", "path": "comparison.json", "source_command": "cmd"}],
    )
    _write(tmp_path / "comparison.json", {"timestamp_utc": "2026-04-21T00:00:00Z"})
    rows = report_manifest.build_report_manifest(current_time_utc="2026-04-21T00:10:00Z")
    assert rows[0]["freshness"]["is_stale"] is True
    assert rows[0]["freshness"]["age_seconds"] == 600


def test_deterministic_output(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(report_manifest, "ROOT", tmp_path)
    monkeypatch.setattr(
        report_manifest,
        "ARTIFACT_SPECS",
        [{"artifact_type": "preflight", "path": "preflight.json", "source_command": "cmd"}],
    )
    _write(tmp_path / "preflight.json", {"timestamp_utc": "2026-04-21T00:00:00Z"})
    a = report_manifest.build_report_manifest(current_time_utc="2026-04-21T00:00:01Z")
    b = report_manifest.build_report_manifest(current_time_utc="2026-04-21T00:00:01Z")
    assert a == b
