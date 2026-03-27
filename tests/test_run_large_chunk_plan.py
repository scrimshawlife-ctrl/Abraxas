from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import scripts.run_large_chunk_plan as runner


def test_build_report_marks_chunk_and_overall_status() -> None:
    steps = [
        runner.StepResult(name="a", chunk="chunk_a", command=["py", "a"], returncode=0),
        runner.StepResult(name="b", chunk="chunk_b", command=["py", "b"], returncode=0),
        runner.StepResult(name="scan", chunk="chunk_d", command=["py", "scan"], returncode=0),
        runner.StepResult(name="pytest_1", chunk="chunk_c", command=["py", "-m", "pytest"], returncode=0),
        runner.StepResult(name="gate", chunk="chunk_c", command=["py", "-m", "scripts.n_run_gate_runtime"], returncode=1),
        runner.StepResult(name="e", chunk="chunk_e", command=["py", "e"], returncode=0),
    ]

    report = runner.build_report(
        started_at="2026-03-27T00:00:00+00:00",
        finished_at="2026-03-27T00:00:01+00:00",
        step_results=steps,
        config={"pytest_runs": 1},
    )

    assert report["overall_status"] == "FAIL"
    assert report["chunks"]["chunk_a_runtime_gate"]["status"] == "PASS"
    assert report["chunks"]["chunk_b_guardrails"]["status"] == "PASS"
    assert report["chunks"]["chunk_d_todo_closure"]["status"] == "PASS"
    assert report["chunks"]["chunk_e_verification"]["status"] == "PASS"
    assert report["chunks"]["chunk_f_runtime_ers_coverage"]["status"] == "not_run"
    assert report["chunks"]["chunk_c_repetition_proof"]["status"] == "FAIL"


def test_main_runs_expected_commands(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_run(command, cwd, check):
        calls.append(list(command))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_large_chunk_plan",
            "--repo-root",
            str(tmp_path),
            "--pytest-runs",
            "3",
            "--report-out",
            "out/wave.json",
        ],
    )

    rc = runner.main()

    assert rc == 0
    assert len(calls) == 13  # A(1) + B(1) + C(3+1) + D(4) + E(2) + F(1)
    assert calls[0][-1] == "tests/test_dozen_run_gate_runtime.py"
    assert calls[1][-1] == "tests/test_online_decodo_flow.py"
    assert calls[6][1].endswith("scripts/scan_todo_markers.py")
    assert calls[7][1].endswith("scripts/scan_stubs.py")
    assert calls[8][1].endswith("scripts/build_stub_taxonomy_artifact.py")
    assert calls[9][1].endswith("scripts/build_notion_sync_artifact.py")
    assert calls[10][-1] == "tests/test_stub_taxonomy_artifact.py"
    assert calls[11][1].endswith("scripts/verify_wave6_artifacts.py")
    assert calls[5][2] == "scripts.n_run_gate_runtime"
    assert calls[12][3] == "tests/test_runtime_infrastructure.py"
    assert calls[12][4] == "tests/test_ers_invariance_gate.py"
    report_path = tmp_path / "out" / "wave.json"
    assert report_path.exists()


def test_main_accepts_custom_runtime_ers_targets(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_run(command, cwd, check):
        calls.append(list(command))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_large_chunk_plan",
            "--repo-root",
            str(tmp_path),
            "--pytest-runs",
            "1",
            "--runtime-ers-targets",
            "tests/test_runtime_infrastructure.py",
            "--report-out",
            "out/wave.json",
        ],
    )

    rc = runner.main()
    assert rc == 0
    assert calls[-1][1:] == ["-m", "pytest", "tests/test_runtime_infrastructure.py"]
    report_payload = json.loads((tmp_path / "out" / "wave.json").read_text(encoding="utf-8"))
    assert report_payload["version"] == "wave6_large_chunk_report.v0.3"


def test_main_supports_fixed_timestamp_for_replay(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_run(command, cwd, check):
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_large_chunk_plan",
            "--repo-root",
            str(tmp_path),
            "--pytest-runs",
            "1",
            "--fixed-now",
            "2026-03-27T00:00:00+00:00",
            "--report-out",
            "out/wave.json",
        ],
    )

    rc = runner.main()
    assert rc == 0
    payload = json.loads((tmp_path / "out" / "wave.json").read_text(encoding="utf-8"))
    assert payload["started_at"] == "2026-03-27T00:00:00+00:00"
    assert payload["finished_at"] == "2026-03-27T00:00:00+00:00"
