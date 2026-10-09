from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_graft_gap_analyzer_binding_mode(tmp_path: Path) -> None:
    """TDD: graft_gap_analyzer --mode binding produces a valid report."""
    report_path = tmp_path / "graft_gap_report.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/graft_gap_analyzer.py",
            "--mode", "binding",
            "--report-path", report_path.as_posix(),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"analyzer failed (exit {result.returncode}):\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )

    assert report_path.exists(), f"missing report: {report_path}"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["schema_version"] == "GraftGapReport.v1"
    assert "modes" in report
    assert "binding" in report["modes"]
    assert "residual" in report["modes"]
    binding_section = report["modes"]["binding"]
    assert "total_hits" in binding_section
    assert "top_symbols" in binding_section
    assert isinstance(binding_section["total_hits"], int)
    assert isinstance(binding_section["top_symbols"], list)

    # residual mode should be empty (not requested)
    residual_section = report["modes"]["residual"]
    assert residual_section["total_hits"] == 0


def test_graft_gap_analyzer_residual_mode(tmp_path: Path) -> None:
    """TDD: graft_gap_analyzer --mode residual produces hits."""
    report_path = tmp_path / "graft_gap_report.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/graft_gap_analyzer.py",
            "--mode", "residual",
            "--report-path", report_path.as_posix(),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"analyzer failed (exit {result.returncode}):\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )

    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["schema_version"] == "GraftGapReport.v1"
    residual_section = report["modes"]["residual"]
    assert residual_section["total_hits"] > 0
    assert len(residual_section["top_symbols"]) > 0

    # binding mode should be empty (not requested)
    binding_section = report["modes"]["binding"]
    assert binding_section["total_hits"] == 0


def test_graft_gap_analyzer_both_modes(tmp_path: Path) -> None:
    """TDD: graft_gap_analyzer --mode binding,residual queries both."""
    report_path = tmp_path / "graft_gap_report.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/graft_gap_analyzer.py",
            "--mode", "binding,residual",
            "--report-path", report_path.as_posix(),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"analyzer failed (exit {result.returncode}):\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )

    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["modes"]["binding"]["total_hits"] > 0
    assert report["modes"]["residual"]["total_hits"] > 0


def test_graft_gap_analyzer_unknown_mode(tmp_path: Path) -> None:
    """TDD: unknown mode produces exit 1."""
    report_path = tmp_path / "graft_gap_report.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/graft_gap_analyzer.py",
            "--mode", "nonexistent",
            "--report-path", report_path.as_posix(),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "unknown mode" in result.stderr.lower()


def test_graft_gap_analyzer_produces_top_symbols(tmp_path: Path) -> None:
    """TDD: report includes top N symbols with file and line spans."""
    report_path = tmp_path / "graft_gap_report.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/graft_gap_analyzer.py",
            "--mode", "binding",
            "--report-path", report_path.as_posix(),
            "--top-n", "3",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    report = json.loads(report_path.read_text(encoding="utf-8"))
    symbols = report["modes"]["binding"]["top_symbols"]
    assert len(symbols) > 0
    for sym in symbols:
        assert "name" in sym
        assert "kind" in sym
        assert "file" in sym