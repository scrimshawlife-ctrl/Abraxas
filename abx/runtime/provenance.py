"""Provenance stamping for deterministic run metadata."""

from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, Any
import os
import subprocess
import sys
import time

from abx.util.hashutil import sha256_file
from abx.util.jsonutil import dumps_stable

def _run(cmd: list[str]) -> Optional[str]:
    """Run command and return output, or None on failure."""
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8").strip()
        return out or None
    except Exception:
        return None

def git_sha(root: Path) -> Optional[str]:
    """Get short git commit SHA."""
    return _run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"])

def git_dirty(root: Path) -> Optional[bool]:
    """Check if git working directory is dirty."""
    s = _run(["git", "-C", str(root), "status", "--porcelain"])
    if s is None:
        return None
    return len(s.strip()) > 0

def lock_hash(root: Path) -> Optional[str]:
    """Hash of dependency lockfile (supports multiple formats)."""
    # Support common lockfiles; pick first that exists
    candidates = ["uv.lock", "poetry.lock", "requirements.txt"]
    for name in candidates:
        p = root / name
        if p.exists() and p.is_file():
            return sha256_file(p)
    return None

@dataclass(frozen=True)
class Provenance:
    """Immutable provenance metadata for a run."""
    ts_unix: int
    python: str
    platform: str
    git_sha: Optional[str]
    git_dirty: Optional[bool]
    lock_hash: Optional[str]
    config_hash: Optional[str]
    assets_hash: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

def compute_config_hash(config_obj: Any) -> str:
    """Hash a configuration object (must be JSON-serializable)."""
    return __import__("hashlib").sha256(dumps_stable(config_obj).encode("utf-8")).hexdigest()

def make_provenance(
    root: Path,
    config_hash: Optional[str] = None,
    assets_hash: Optional[str] = None,
) -> Provenance:
    """Create provenance stamp for current environment."""
    return Provenance(
        ts_unix=int(time.time()),
        python=sys.version.split()[0],
        platform=os.uname().sysname + "-" + os.uname().machine,
        git_sha=git_sha(root),
        git_dirty=git_dirty(root),
        lock_hash=lock_hash(root),
        config_hash=config_hash,
        assets_hash=assets_hash,
    )
