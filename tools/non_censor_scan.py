from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable, List, Tuple


BANNED_PATTERNS = [
    r"firewall",
    r"refuse_extension",
    r"de_escalate",
    r"rewrite_output",
    r"sanitize",
    r"redact",
    r"filter_output",
    r"moderation",
    r"block_output",
    r"strip_terms",
    r"response_mode",
]

CODE_EXTENSIONS = {".py", ".ts", ".tsx", ".js"}
SKIP_PARTS = {"node_modules", "attached_assets", ".git", "__pycache__"}
ALLOWLIST_PATH_PARTS = {
    "tools/non_censor_scan.py",
    "abraxas/policy/non_censorship.py",
    "abraxas/policy/README.md",
    "tests/test_non_censorship_invariant.py",
    "abraxas/drift/orchestrator.py",
}


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() not in CODE_EXTENSIONS:
            continue
        yield path


def scan_file(path: Path, root: Path) -> List[Tuple[int, str]]:
    violations: List[Tuple[int, str]] = []
    rel_path = path.relative_to(root)
    allowlisted = any(str(rel_path).startswith(prefix) for prefix in ALLOWLIST_PATH_PARTS)
    if allowlisted:
        return violations
    text = path.read_text(encoding="utf-8", errors="ignore")
    for idx, line in enumerate(text.splitlines(), start=1):
        for pat in BANNED_PATTERNS:
            if re.search(pat, line, flags=re.IGNORECASE):
                violations.append((idx, line.strip()))
                break
    # Heuristic: flag functions that claim to sanitize or redact text
    for m in re.finditer(r"def\\s+([a-zA-Z0-9_]*sanitize[a-zA-Z0-9_]*|[a-zA-Z0-9_]*redact[a-zA-Z0-9_]*)", text):
        line_no = text[: m.start()].count("\\n") + 1
        snippet = text.splitlines()[line_no - 1].strip()
        violations.append((line_no, snippet))
    return violations


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    violations_found: List[Tuple[Path, int, str]] = []
    for path in iter_files(root):
        for line_no, snippet in scan_file(path, root):
            violations_found.append((path, line_no, snippet))

    if violations_found:
        print("Non-censorship scan detected potential violations:")
        for path, line_no, snippet in violations_found:
            rel = path.relative_to(root)
            print(f" - {rel}:{line_no}: {snippet}")
        return 1

    print("Non-censorship scan passed: no suspicious patterns found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
