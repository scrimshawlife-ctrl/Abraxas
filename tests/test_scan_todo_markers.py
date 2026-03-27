from __future__ import annotations

from pathlib import Path

import scripts.scan_todo_markers as mod


def test_build_report_counts_todo_and_fixme(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("# TODO: alpha\nprint('x')\n# FIXME: beta\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("No markers here\n", encoding="utf-8")

    report = mod.build_report(tmp_path)

    assert report["schema"] == "TodoMarkerScan.v0"
    assert report["totals"]["files_with_markers"] == 1
    assert report["totals"]["todo"] == 1
    assert report["totals"]["fixme"] == 1
    assert report["top_files"][0]["path"] == "a.py"
    assert report["top_files"][0]["total"] == 2


def test_build_report_ignores_unreadable_binary(tmp_path: Path) -> None:
    (tmp_path / "bin.dat").write_bytes(b"\xff\xfe\x00\x01")

    report = mod.build_report(tmp_path)

    assert report["totals"]["files_with_markers"] == 0
    assert report["top_files"] == []
