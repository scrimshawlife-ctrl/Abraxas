#!/usr/bin/env python3
"""Scan repository text files for TODO/FIXME and broader debt markers and emit a deterministic summary artifact.

Broader debt closure: now detects XXX, HACK, KLUDGE in comment context; excludes historical artifacts and self-referential mentions.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

MARKER_RE = re.compile(r"\b(TODO|FIXME|XXX|HACK|KLUDGE)\b", re.IGNORECASE)
DEBT_CONTEXT_RE = re.compile(r"(?i)^\s*(#|//|/\*|\*|-|\+)\s*(TODO|FIXME|XXX|HACK|KLUDGE)", re.IGNORECASE)
SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", ".mypy_cache", ".venv", "venv", "node_modules", "artifacts_gate", "artifacts_seal", "docs/artifacts"}
SKIP_FILES = {"docs/artifacts/todo_marker_scan.json"}
ALLOWED_SUFFIXES = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".sh", ".mk"}


def _iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    candidates: list[Path] = []

    git_dir = root / ".git"
    if git_dir.exists():
        try:
            tracked = subprocess.run(
                ["git", "-C", str(root), "ls-files"],
                check=False,
                capture_output=True,
                text=True,
            )
            if tracked.returncode == 0:
                candidates = [root / line.strip() for line in tracked.stdout.splitlines() if line.strip()]
        except Exception:
            candidates = []

    if not candidates:
        candidates = [p for p in root.rglob("*") if p.is_file()]

    for p in candidates:
        rel = p.relative_to(root).as_posix()
        if any(part in SKIP_DIRS for part in p.parts) or "docs/artifacts" in rel or rel.startswith("docs/artifacts"):
            continue
        if rel in SKIP_FILES:
            continue
        if p.suffix and p.suffix.lower() not in ALLOWED_SUFFIXES:
            continue
        if not p.exists() or not p.is_file():
            continue
        files.append(p)

    files.sort()
    return files


def _scan_file(path: Path) -> dict[str, Any]:
    counts = {"TODO": 0, "FIXME": 0, "XXX": 0, "HACK": 0, "KLUDGE": 0}
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {"counts": counts, "first_hit_line": None}

    first_hit_line: int | None = None
    for idx, line in enumerate(text.splitlines(), start=1):
        if DEBT_CONTEXT_RE.search(line):
            marker_match = MARKER_RE.search(line)
            marker = marker_match.group(1).upper() if marker_match else "TODO"
            if marker in counts:
                counts[marker] = counts.get(marker, 0) + 1
                if first_hit_line is None:
                    first_hit_line = idx
    return {"counts": counts, "first_hit_line": first_hit_line}


def build_report(repo_root: Path) -> dict[str, Any]:
    file_hits: list[dict[str, Any]] = []
    marker_totals = {"TODO": 0, "FIXME": 0, "XXX": 0, "HACK": 0, "KLUDGE": 0}

    for file_path in _iter_files(repo_root):
        scan = _scan_file(file_path)
        counts = scan["counts"]
        total_for_file = sum(int(v) for v in counts.values())
        if total_for_file == 0:
            continue
        for k in marker_totals:
            marker_totals[k] += int(counts.get(k, 0))
        file_hits.append(
            {
                "path": str(file_path.relative_to(repo_root)),
                "todo": int(counts.get("TODO", 0)),
                "fixme": int(counts.get("FIXME", 0)),
                "xxx": int(counts.get("XXX", 0)),
                "hack": int(counts.get("HACK", 0)),
                "kludge": int(counts.get("KLUDGE", 0)),
                "total": total_for_file,
                "first_hit_line": scan["first_hit_line"],
            }
        )

    file_hits.sort(key=lambda x: (-int(x["total"]), x["path"]))

    return {
        "schema": "TodoMarkerScan.v1",
        "repo_root": str(repo_root),
        "totals": {
            "files_with_markers": len(file_hits),
            "todo": marker_totals.get("TODO", 0),
            "fixme": marker_totals.get("FIXME", 0),
            "xxx": marker_totals.get("XXX", 0),
            "hack": marker_totals.get("HACK", 0),
            "kludge": marker_totals.get("KLUDGE", 0),
        },
        "top_files": file_hits[:100],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan TODO/FIXME and broader debt markers (context-aware)")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out", default="out/reports/todo_markers.latest.json")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    report = build_report(repo_root)

    out = Path(args.out)
    if not out.is_absolute():
        out = repo_root / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[TODO_SCAN] wrote: {out}")
    t = report["totals"]
    print(f"[TODO_SCAN] files_with_markers={t['files_with_markers']} todo={t['todo']} fixme={t['fixme']} xxx={t['xxx']} hack={t['hack']} kludge={t['kludge']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
