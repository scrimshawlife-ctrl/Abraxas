#!/usr/bin/env python3
"""Automated stub scanner for Abraxas codebase.

Scans for NotImplementedError, TODO, FIXME, and stub markers across the
codebase and generates a comprehensive stub_index.json.

Usage:
    python scripts/scan_stubs.py --write  # Update stub_index.json
    python scripts/scan_stubs.py          # Dry run (print results)
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Any


# Patterns to search for
STUB_PATTERNS = [
    (r"NotImplementedError", "not_implemented"),
    (r"TODO:", "todo"),
    (r"FIXME:", "fixme"),
    (r"# stub", "stub_comment"),
    (r"# placeholder", "placeholder"),
    (r"pass\s*#.*stub", "stub_pass"),
]


def scan_file(file_path: Path) -> List[Dict[str, Any]]:
    """Scan a single Python file for stub markers."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        return []

    stubs = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, start=1):
        for pattern, stub_type in STUB_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                # Extract context (trim to 80 chars)
                marker = line.strip()[:80]

                # Determine priority based on context
                priority = "P2"  # Default
                if "NotImplementedError" in line:
                    priority = "P1"
                if "# TODO" in line and "P0" in line:
                    priority = "P0"

                stubs.append({
                    "file": str(file_path),
                    "line": line_num,
                    "marker": marker,
                    "type": stub_type,
                    "priority": priority,
                })
                break  # Only record first match per line

    return stubs


def scan_directory(dir_path: Path, patterns: List[str]) -> List[Dict[str, Any]]:
    """Scan a directory for stub markers."""
    all_stubs = []

    for pattern in patterns:
        for py_file in dir_path.rglob(pattern):
            if py_file.is_file() and not py_file.name.startswith("test_"):
                stubs = scan_file(py_file)
                all_stubs.extend(stubs)

    return all_stubs


def classify_stub(stub: Dict[str, Any]) -> str:
    """Classify stub by module type."""
    file_path = stub["file"]

    if "abraxas/runes/operators" in file_path:
        return "operator"
    elif "abraxas/sources/adapters" in file_path or "base.py" in file_path:
        return "interface"
    elif "abx/core" in file_path or "abraxas/core" in file_path:
        return "core"
    elif stub["type"] == "not_implemented":
        return "not_implemented"
    else:
        return "module"


def deduplicate_stubs(stubs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate stubs by file (keep first occurrence)."""
    seen_files = set()
    deduped = []

    for stub in stubs:
        file_path = stub["file"]
        if file_path not in seen_files:
            seen_files.add(file_path)
            deduped.append(stub)

    return deduped


def generate_stub_index(repo_root: Path) -> Dict[str, Any]:
    """Generate complete stub index."""
    scopes = [
        {"path": "abraxas/runes/operators", "type": "operators"},
        {"path": "abraxas/storage", "type": "modules"},
        {"path": "abraxas/sources/adapters", "type": "interfaces"},
        {"path": "abraxas/runtime", "type": "modules"},
        {"path": "abraxas/shadow_metrics", "type": "shadow"},
        {"path": "abraxas/metric_extractors", "type": "interfaces"},
        {"path": "abraxas/detectors", "type": "detectors"},
        {"path": "abraxas/narratives", "type": "modules"},
        {"path": "abx/core", "type": "core"},
        {"path": "abx/kernel.py", "type": "kernel"},
    ]

    all_stubs = []

    for scope in scopes:
        scope_path = repo_root / scope["path"]
        if scope_path.exists():
            if scope_path.is_dir():
                stubs = scan_directory(scope_path, ["*.py"])
            else:
                stubs = scan_file(scope_path)

            all_stubs.extend(stubs)

    # Deduplicate by file
    all_stubs = deduplicate_stubs(all_stubs)

    # Convert absolute paths to relative
    for stub in all_stubs:
        stub["file"] = str(Path(stub["file"]).relative_to(repo_root))
        stub["stub_type"] = classify_stub(stub)
        # Remove line number from final index (just track file)
        stub.pop("line", None)

    # Sort by file path
    all_stubs.sort(key=lambda x: x["file"])

    return {
        "version": "2.0.0",
        "generated_at": "auto",
        "scopes": scopes,
        "stubs": all_stubs,
        "summary": {
            "total_stubs": len(all_stubs),
            "by_priority": {
                "P0": len([s for s in all_stubs if s.get("priority") == "P0"]),
                "P1": len([s for s in all_stubs if s.get("priority") == "P1"]),
                "P2": len([s for s in all_stubs if s.get("priority") == "P2"]),
            },
            "by_type": {
                "operator": len([s for s in all_stubs if s.get("stub_type") == "operator"]),
                "interface": len([s for s in all_stubs if s.get("stub_type") == "interface"]),
                "not_implemented": len([s for s in all_stubs if s.get("stub_type") == "not_implemented"]),
                "module": len([s for s in all_stubs if s.get("stub_type") == "module"]),
            }
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Scan for stub markers in Abraxas codebase")
    parser.add_argument("--write", action="store_true", help="Write to tools/stub_index.json")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    stub_index = generate_stub_index(repo_root)

    if args.verbose or not args.write:
        print(f"Found {stub_index['summary']['total_stubs']} stubs:")
        print(f"  P0: {stub_index['summary']['by_priority']['P0']}")
        print(f"  P1: {stub_index['summary']['by_priority']['P1']}")
        print(f"  P2: {stub_index['summary']['by_priority']['P2']}")
        print()
        print(f"By type:")
        for stub_type, count in stub_index['summary']['by_type'].items():
            print(f"  {stub_type}: {count}")

    if args.write:
        output_path = repo_root / "tools" / "stub_index.json"
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(stub_index, f, indent=2, ensure_ascii=False)

        print(f"✅ Written to {output_path}")
        print(f"   Total stubs tracked: {stub_index['summary']['total_stubs']}")
    else:
        print("\nDry run complete. Use --write to update stub_index.json")


if __name__ == "__main__":
    main()
