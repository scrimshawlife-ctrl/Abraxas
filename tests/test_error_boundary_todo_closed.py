"""TDD guard: ErrorBoundary TODO must be resolved (Slice 3 debt closure)."""
from __future__ import annotations

from pathlib import Path


def test_error_boundary_has_no_todo_marker() -> None:
    """Failing test: ErrorBoundary.tsx must not contain an unresolved TODO."""
    repo_root = Path(__file__).resolve().parent.parent
    eb_path = repo_root / "dashboard" / "frontend" / "src" / "components" / "ErrorBoundary.tsx"
    assert eb_path.exists(), f"Expected ErrorBoundary.tsx at {eb_path}"

    content = eb_path.read_text()
    lines = content.splitlines()

    # Line 25 should not contain an unresolved TODO
    todo_lines = [
        (i + 1, line)
        for i, line in enumerate(lines)
        if "TODO:" in line and "Send to error reporting" in line
    ]
    assert len(todo_lines) == 0, (
        f"Unresolved TODO found in ErrorBoundary.tsx:\n"
        + "\n".join(f"  L{ln}: {text.strip()}" for ln, text in todo_lines)
    )


def test_error_boundary_acknowledges_error_reporting_gap() -> None:
    """ErrorBoundary must acknowledge the error reporting gap (not just delete the TODO)."""
    repo_root = Path(__file__).resolve().parent.parent
    eb_path = repo_root / "dashboard" / "frontend" / "src" / "components" / "ErrorBoundary.tsx"
    content = eb_path.read_text()

    # Should mention the gap explicitly
    assert "error reporting" in content.lower(), (
        "ErrorBoundary must document the error reporting gap, not silently delete it"
    )