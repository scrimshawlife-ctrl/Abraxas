"""Asset manifest generation and validation."""

from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional

from abx.util.hashutil import sha256_file, sha256_paths
from abx.util.jsonutil import dump_file, load_file

MANIFEST_NAME = "assets.manifest.json"

@dataclass(frozen=True)
class AssetEntry:
    """Single asset file entry."""
    relpath: str
    sha256: str
    bytes: int

def _walk_files(root: Path) -> List[Path]:
    """Walk directory and return all files, sorted."""
    files: List[Path] = []
    if not root.exists():
        return files
    for p in root.rglob("*"):
        if p.is_file():
            # Ignore manifest itself
            if p.name == MANIFEST_NAME:
                continue
            files.append(p)
    files.sort(key=lambda x: x.as_posix())
    return files

def build_manifest(assets_dir: Path) -> Dict[str, Any]:
    """Build asset manifest from directory."""
    assets_dir.mkdir(parents=True, exist_ok=True)
    entries: List[Dict[str, Any]] = []
    files = _walk_files(assets_dir)
    for p in files:
        rel = str(p.relative_to(assets_dir).as_posix())
        entries.append(asdict(AssetEntry(relpath=rel, sha256=sha256_file(p), bytes=p.stat().st_size)))
    # Deterministic overall hash
    overall = sha256_paths([assets_dir / e["relpath"] for e in entries]) if entries else sha256_paths([])
    return {
        "assets_dir": str(assets_dir),
        "entries": entries,
        "overall_sha256": overall,
    }

def write_manifest(assets_dir: Path) -> Path:
    """Write asset manifest to directory."""
    manifest = build_manifest(assets_dir)
    path = assets_dir / MANIFEST_NAME
    dump_file(str(path), manifest)
    return path

def read_manifest(assets_dir: Path) -> Optional[Dict[str, Any]]:
    """Read asset manifest from directory."""
    path = assets_dir / MANIFEST_NAME
    if not path.exists():
        return None
    return load_file(str(path))
