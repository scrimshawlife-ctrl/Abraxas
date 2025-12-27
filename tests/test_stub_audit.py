"""Stub audit test for registered rune operator stubs."""

from __future__ import annotations

import json
from pathlib import Path


def test_stub_index_matches_scope() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    index_path = repo_root / "tools" / "stub_index.json"
    payload = json.loads(index_path.read_text())

    scope_dirs = [repo_root / path for path in payload.get("scope", [])]
    registered = {
        Path(entry["file"]): entry["marker"] for entry in payload.get("stubs", [])
    }

    missing_markers = []
    for file_path, marker in registered.items():
        absolute = repo_root / file_path
        if not absolute.exists():
            missing_markers.append(f"Missing file: {file_path}")
            continue
        content = absolute.read_text(encoding="utf-8", errors="ignore")
        if marker not in content:
            missing_markers.append(f"Missing marker in {file_path}: {marker}")

    assert not missing_markers, "Stub index mismatch:\n" + "\n".join(missing_markers)

    unregistered = []
    for scope_dir in scope_dirs:
        for path in scope_dir.rglob("*.py"):
            rel = path.relative_to(repo_root)
            content = path.read_text(encoding="utf-8", errors="ignore")
            if "NotImplementedError" in content and rel not in registered:
                unregistered.append(str(rel))

    assert not unregistered, "Unregistered stubs found:\n" + "\n".join(unregistered)
