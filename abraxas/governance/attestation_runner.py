"""PATCH-004 deterministic repository attestation."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, List

SCAN_ROOTS = (".aal", ".abraxas", "aal_core", "abraxas", "schemas", "scripts", "tests")
IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "pycache",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
}


def _sha256_file(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for block in iter(lambda: handle.read(8192), b""):
            digest.update(block)
    return digest.hexdigest()


def run_attestation(repo_root: str | Path, timestamp: str = "1970-01-01T00:00:00Z") -> Dict[str, object]:
    base_path = Path(repo_root).resolve()
    files_indexed: List[str] = []
    sha256_map: Dict[str, str] = {}
    missing_roots: List[str] = []

    for root in SCAN_ROOTS:
        root_path = base_path / root
        if not root_path.exists():
            missing_roots.append(root)
            continue

        for file_path in sorted(path for path in root_path.rglob("*") if path.is_file()):
            if any(part in IGNORE_DIRS for part in file_path.parts):
                continue
            rel_path = file_path.relative_to(base_path).as_posix()
            files_indexed.append(rel_path)
            sha256_map[rel_path] = _sha256_file(file_path)

    files_indexed = sorted(files_indexed)

    status = "PASS"
    if missing_roots:
        status = "PARTIAL" if files_indexed else "FAIL"

    return {
        "schema_version": "AttestationRun.v1",
        "run_id": "patch004_attestation",
        "generated_at": timestamp,
        "provenance": {"deterministic": True},
        "files_indexed": files_indexed,
        "sha256_map": sha256_map,
        "missing_roots": sorted(missing_roots),
        "status": status,
    }
