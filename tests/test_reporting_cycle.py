from __future__ import annotations

import json
from pathlib import Path

import scripts.run_reporting_cycle as reporting_cycle_script


class _Completed:
    def __init__(self, returncode: int = 0):
        self.returncode = returncode


def test_execution_order_and_status_propagation(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path
    reports = root / "out" / "reports"
    reports.mkdir(parents=True)
    (reports / "developer_readiness.json").write_text(
        json.dumps({"status": "PASS", "timestamp_utc": "2026-04-21T00:00:00Z"}),
        encoding="utf-8",
    )
    (reports / "gap_closure_invariance.projection.json").write_text(
        json.dumps({"provenance": {"projection_generated_at": "2026-04-21T00:00:00Z"}}),
        encoding="utf-8",
    )
    (reports / "readiness_comparison.latest.json").write_text(
        json.dumps({"timestamp_utc": "2026-04-21T00:00:00Z"}),
        encoding="utf-8",
    )
    (reports / "promotion_preflight.latest.json").write_text(
        json.dumps({"timestamp_utc": "2026-04-21T00:00:00Z"}),
        encoding="utf-8",
    )

    calls: list[list[str]] = []

    def _fake_run(command, cwd, check):
        assert cwd == root
        assert check is False
        calls.append(list(command))
        return _Completed(0)

    monkeypatch.setattr(reporting_cycle_script, "ROOT", root)
    monkeypatch.setattr(reporting_cycle_script, "LATEST_PATH", reports / "reporting_cycle.latest.json")
    monkeypatch.setattr(reporting_cycle_script.subprocess, "run", _fake_run)
    monkeypatch.setattr(reporting_cycle_script, "read_gap_closure_invariance_payload", lambda _path: {"status": "PASS"})
    monkeypatch.setattr(
        reporting_cycle_script,
        "read_latest_comparison",
        lambda _path: {"status": "OK", "comparison": {"timestamp_utc": "2026-04-21T00:00:00Z"}},
    )
    monkeypatch.setattr(
        reporting_cycle_script,
        "read_promotion_preflight",
        lambda _path: {"status": "OK", "advisory": {"timestamp_utc": "2026-04-21T00:00:00Z"}},
    )
    monkeypatch.setattr(reporting_cycle_script, "now_utc", lambda: "2026-04-21T00:00:00Z")

    rc = reporting_cycle_script.main()
    assert rc == 0
    assert calls == [
        ["python", "scripts/run_developer_readiness.py"],
        ["python", "scripts/project_gap_closure_invariance.py"],
        ["python", "scripts/log_readiness_comparison.py"],
        ["python", "scripts/generate_promotion_preflight.py"],
    ]

    payload = json.loads((reports / "reporting_cycle.latest.json").read_text(encoding="utf-8"))
    assert payload["steps"] == {
        "developer_readiness_status": "PASS",
        "invariance_status": "PASS",
        "comparison_status": "PASS",
        "advisory_status": "PASS",
    }
    assert payload["overall_status"] == "PASS"
    assert payload["missing_artifacts"] == []
    assert payload["freshness"]["overall_stale"] is False


def test_missing_artifact_not_computable(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path
    reports = root / "out" / "reports"
    reports.mkdir(parents=True)

    monkeypatch.setattr(reporting_cycle_script, "ROOT", root)
    monkeypatch.setattr(reporting_cycle_script, "LATEST_PATH", reports / "reporting_cycle.latest.json")
    monkeypatch.setattr(reporting_cycle_script.subprocess, "run", lambda command, cwd, check: _Completed(0))
    monkeypatch.setattr(reporting_cycle_script, "read_gap_closure_invariance_payload", lambda _path: {"status": "NOT_COMPUTABLE"})
    monkeypatch.setattr(reporting_cycle_script, "read_latest_comparison", lambda _path: {"status": "NOT_COMPUTABLE"})
    monkeypatch.setattr(reporting_cycle_script, "read_promotion_preflight", lambda _path: {"status": "NOT_COMPUTABLE"})
    monkeypatch.setattr(reporting_cycle_script, "now_utc", lambda: "2026-04-21T00:00:00Z")

    reporting_cycle_script.main()
    payload = json.loads((reports / "reporting_cycle.latest.json").read_text(encoding="utf-8"))
    assert payload["overall_status"] == "NOT_COMPUTABLE"
    assert payload["steps"]["developer_readiness_status"] == "NOT_COMPUTABLE"
    assert len(payload["missing_artifacts"]) == 4


def test_deterministic_output(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path
    reports = root / "out" / "reports"
    reports.mkdir(parents=True)
    (reports / "developer_readiness.json").write_text(
        json.dumps({"status": "PARTIAL", "timestamp_utc": "2026-04-21T00:00:00Z"}),
        encoding="utf-8",
    )
    (reports / "gap_closure_invariance.projection.json").write_text(
        json.dumps({"provenance": {"projection_generated_at": "2026-04-21T00:00:00Z"}}),
        encoding="utf-8",
    )
    (reports / "readiness_comparison.latest.json").write_text(
        json.dumps({"timestamp_utc": "2026-04-21T00:00:00Z"}),
        encoding="utf-8",
    )
    (reports / "promotion_preflight.latest.json").write_text(
        json.dumps({"timestamp_utc": "2026-04-21T00:00:00Z"}),
        encoding="utf-8",
    )

    monkeypatch.setattr(reporting_cycle_script, "ROOT", root)
    monkeypatch.setattr(reporting_cycle_script, "LATEST_PATH", reports / "reporting_cycle.latest.json")
    monkeypatch.setattr(reporting_cycle_script.subprocess, "run", lambda command, cwd, check: _Completed(0))
    monkeypatch.setattr(reporting_cycle_script, "read_gap_closure_invariance_payload", lambda _path: {"status": "PASS"})
    monkeypatch.setattr(
        reporting_cycle_script,
        "read_latest_comparison",
        lambda _path: {"status": "OK", "comparison": {"timestamp_utc": "2026-04-21T00:00:00Z"}},
    )
    monkeypatch.setattr(
        reporting_cycle_script,
        "read_promotion_preflight",
        lambda _path: {"status": "OK", "advisory": {"timestamp_utc": "2026-04-21T00:00:00Z"}},
    )
    monkeypatch.setattr(reporting_cycle_script, "now_utc", lambda: "2026-04-21T00:00:00Z")

    reporting_cycle_script.main()
    first = json.loads((reports / "reporting_cycle.latest.json").read_text(encoding="utf-8"))
    reporting_cycle_script.main()
    second = json.loads((reports / "reporting_cycle.latest.json").read_text(encoding="utf-8"))

    assert first == second
    assert first["overall_status"] == "PARTIAL"
