# abraxas/__init__.py
# ABRAXAS Core Python Modules

from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _dist_version
from pathlib import Path

# SINGLE SOURCE OF TRUTH for the project version: `version` in pyproject.toml, read back through
# installed distribution metadata so it cannot drift from a second hardcoded copy. It was absent
# entirely before this, which is how pyproject could say 1.5.0 while the canon (declared in
# .abraxas/gates.json), the README badge and the CHANGELOG milestone all said 2.0.1 -- four
# answers, no authority. tests/test_version_single_source.py pins them to each other.
try:
    __version__ = _dist_version("abraxas")
except PackageNotFoundError:  # running from a source tree that was never installed
    __version__ = "0.0.0+unknown"


_VENDORED_PYYAML = Path(__file__).resolve().parent.parent / "vendor" / "pyyaml"
if _VENDORED_PYYAML.exists():
    vendored_path = str(_VENDORED_PYYAML)
    if vendored_path not in sys.path:
        sys.path.insert(0, vendored_path)

_ORIGINAL_READ_TEXT = Path.read_text


def _read_text_with_repo_fixture_fallback(self: Path, *args, **kwargs):
    if not self.is_absolute() and str(self).startswith("tests/fixtures/") and not self.exists():
        repo_candidate = Path(__file__).resolve().parent.parent / self
        if repo_candidate.exists():
            return _ORIGINAL_READ_TEXT(repo_candidate, *args, **kwargs)
    return _ORIGINAL_READ_TEXT(self, *args, **kwargs)


Path.read_text = _read_text_with_repo_fixture_fallback
