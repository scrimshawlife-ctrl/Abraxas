"""Deterministic hashing utilities for assets and provenance."""

from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Iterable

def sha256_bytes(b: bytes) -> str:
    """Hash bytes to SHA256 hex digest."""
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    """Hash file contents to SHA256 hex digest."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            data = f.read(chunk)
            if not data:
                break
            h.update(data)
    return h.hexdigest()

def sha256_paths(paths: Iterable[Path]) -> str:
    """Deterministic hash of multiple files.

    Hashes concatenated (path, filehash) pairs sorted by path.
    """
    pairs = []
    for p in paths:
        pairs.append((str(p.as_posix()), sha256_file(p)))
    pairs.sort(key=lambda x: x[0])
    h = hashlib.sha256()
    for k, v in pairs:
        h.update(k.encode("utf-8"))
        h.update(b"\0")
        h.update(v.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()
