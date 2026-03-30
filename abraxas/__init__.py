# abraxas/__init__.py
# ABRAXAS Core Python Modules

from __future__ import annotations

import sys
from pathlib import Path

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
