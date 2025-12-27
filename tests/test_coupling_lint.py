"""Coupling lint to prevent direct cross-subsystem rune imports."""

from __future__ import annotations

from pathlib import Path

FORBIDDEN_PATTERNS = [
    "../runes",
    "./runes.js",
    "../../runes",
    "../../runes.js",
    "require(\"../../runes\")",
    "require('../../runes')",
]

ALLOWED_FILES = {
    Path("server/abraxas/runes/registry.js"),
    Path("server/runes.js"),
}


def test_no_direct_rune_imports() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    server_root = repo_root / "server"
    violations = []

    for path in server_root.rglob("*"):
        if path.is_dir() or path.suffix not in {".ts", ".js"}:
            continue
        rel_path = path.relative_to(repo_root)
        if rel_path in ALLOWED_FILES:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in content:
                violations.append(f"{rel_path}: {pattern}")
                break

    assert not violations, "Direct rune imports detected:\n" + "\n".join(violations)
