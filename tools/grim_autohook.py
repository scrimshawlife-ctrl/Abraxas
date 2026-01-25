"""Auto-hook Abraxas rune registrations for GRIM export."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}

REGISTER_PATTERNS = [
    re.compile(r"\.register\(\s*(?P<var>[A-Za-z_][\w]*)\s*[\),]"),
    re.compile(r"\.add\(\s*(?P<var>[A-Za-z_][\w]*)\s*[\),]"),
    re.compile(r"\.append\(\s*(?P<var>[A-Za-z_][\w]*)\s*[\),]"),
    re.compile(r"\[[^\]]+\]\s*=\s*(?P<var>[A-Za-z_][\w]*)"),
]

IMPORT_LINE = "from abraxas.grim_bridge import register_rune  # GRIM_AUTOHOOK"
HOOK_MARKER = "# GRIM_AUTOHOOK"


def _iter_python_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def _find_candidates(lines: list[str]) -> list[tuple[int, str]]:
    candidates: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        if "rune" not in line.lower():
            continue
        if HOOK_MARKER in line:
            continue
        for pattern in REGISTER_PATTERNS:
            match = pattern.search(line)
            if match:
                candidates.append((idx, match.group("var")))
                break
    return candidates


def _score_candidate(line: str) -> int:
    score = 0
    if "rune_registry" in line:
        score += 5
    if "runes" in line:
        score += 2
    if ".register" in line:
        score += 3
    return score


def _insert_import(lines: list[str]) -> list[str]:
    if any(IMPORT_LINE in line for line in lines):
        return lines
    insert_at = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("from __future__"):
            insert_at = idx + 1
            continue
        if stripped.startswith("import ") or stripped.startswith("from "):
            insert_at = idx + 1
            continue
        if stripped and not stripped.startswith("#"):
            break
        insert_at = idx + 1
    return lines[:insert_at] + [IMPORT_LINE + "\n"] + lines[insert_at:]


def _apply_hook(lines: list[str], line_index: int, rune_var: str) -> list[str]:
    indentation = re.match(r"\s*", lines[line_index]).group(0)
    hook_line = f"{indentation}register_rune({rune_var}, source=__name__)  # GRIM_AUTOHOOK\n"
    return lines[: line_index + 1] + [hook_line] + lines[line_index + 1 :]


def _build_proposed_edit(path: Path) -> tuple[list[str], list[str], int] | None:
    lines = path.read_text().splitlines(keepends=True)
    if any(HOOK_MARKER in line for line in lines):
        return None
    candidates = _find_candidates(lines)
    if not candidates:
        return None

    scored = [
        (idx, var, _score_candidate(lines[idx]))
        for idx, var in candidates
    ]
    scored.sort(key=lambda item: (-item[2], item[0]))
    best_idx, best_var, _ = scored[0]

    updated = _insert_import(lines)
    if updated is not lines:
        import_delta = len(updated) - len(lines)
        best_idx += import_delta
        lines = updated
    hooked = _apply_hook(lines, best_idx, best_var)
    best_score = _score_candidate(lines[best_idx])
    return lines, hooked, best_score


def _describe_candidate(path: Path, before: list[str], after: list[str]) -> str:
    diff_lines = []
    for idx, (old, new) in enumerate(zip(before, after), start=1):
        if old != new:
            diff_lines.append(f"L{idx}: -{old.rstrip()}\nL{idx}: +{new.rstrip()}")
    if len(after) > len(before):
        for idx in range(len(before), len(after)):
            diff_lines.append(f"L{idx + 1}: +{after[idx].rstrip()}")
    return f"{path}\n" + "\n".join(diff_lines)


def _apply_edit(path: Path, before: list[str], after: list[str]) -> None:
    backup = path.with_suffix(path.suffix + ".bak")
    backup.write_text("".join(before))
    path.write_text("".join(after))


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-hook Abraxas rune registrations")
    parser.add_argument("--dry-run", action="store_true", help="Show proposed edits only")
    parser.add_argument("--apply", action="store_true", help="Apply best edit with backup")
    parser.add_argument("--root", type=Path, default=Path("."), help="Repo root")
    args = parser.parse_args()

    if args.dry_run == args.apply:
        print("Specify exactly one of --dry-run or --apply", file=sys.stderr)
        return 2

    candidates: list[tuple[Path, list[str], list[str], int]] = []
    for path in _iter_python_files(args.root):
        proposed = _build_proposed_edit(path)
        if not proposed:
            continue
        before, after, score = proposed
        candidates.append((path, before, after, score))

    if not candidates:
        print("No hook candidates found.")
        return 1

    candidates.sort(key=lambda item: (-item[3], str(item[0])))
    best_path, before, after, _ = candidates[0]

    if args.dry_run:
        print("GRIM auto-hook candidates:")
        for path, candidate_before, candidate_after, _ in candidates:
            print(_describe_candidate(path, candidate_before, candidate_after))
        print("\nBest candidate:")
        print(_describe_candidate(best_path, before, after))
        return 0

    _apply_edit(best_path, before, after)
    print(f"Applied hook to {best_path} (backup at {best_path.with_suffix(best_path.suffix + '.bak')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
